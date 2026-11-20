"""Phase 0 health check, checks C1 to C5.

The checks are defined in documents/planning/phase0/phase0_plan.md. Run from
the repository root:

    .venv\\Scripts\\python.exe scripts\\phase0_health_check.py

Writes results/phase0/health_report.txt, health_report.json,
algorithm_runs.csv and pytest_runs.txt. Nothing in aad/ is changed; some
checks patch a function for the length of one call to record what it does.
"""

import ast
import contextlib
import csv
import importlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import warnings
from datetime import date

import ioh
import numpy as np

ROOT =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "results", "phase0")
SEED = 0
DIM = 5
POP, GENS = 20, 10

import aad  # noqa: E402
from aad.evolutionary_algorithm import EvolutionaryAlgorithm, build_algorithm  # noqa: E402
from aad.mealpy_algorithms import MEALPY_REGISTRY, MealpyAlgorithm  # noqa: E402

ROWS = []


def record(check, item, status, detail=""):
    ROWS.append({"check": check, "item": item, "status": status, "detail": str(detail)})


def reseed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)


def scalar(f):
    return float(sum(f)) if isinstance(f, (list, tuple)) else float(f)


class CountingProblem:
    """Wraps a problem; counts evaluate() calls and the best value seen."""

    def __init__(self, problem):
        self.problem = problem
        self.calls = 0
        self.best_seen = math.inf

    def evaluate(self, x):
        self.calls += 1
        f = self.problem.evaluate(x)
        s = scalar(f)
        if s < self.best_seen:
            self.best_seen = s
        return f

    def __getattr__(self, name):
        return getattr(self.problem, name)


class ConstantProblem(aad.OptimizationProblem):
    """A 5-d problem that returns NaN, or raises, on every evaluation."""

    def __init__(self, mode):
        self.mode = mode

    def evaluate(self, solution):
        if self.mode == "raise":
            raise RuntimeError("evaluation failed")
        return float("nan")

    def bounds(self):
        return [-5.0] * DIM, [5.0] * DIM

    def is_multiobjective(self):
        return False


def bbob_classes():
    return [getattr(aad, n) for n in aad.__all__ if n.startswith("BBOB_F")]


def ea_config(**extra):
    return {"algorithm": "ea", "population_size": POP, "max_generations": GENS, **extra}


# ---------------------------------------------------------------------------
# C1: imports and packages
# ---------------------------------------------------------------------------

def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def third_party_imports():
    """Map each imported third-party module to the places that import it."""
    files = [os.path.join(ROOT, "aad", f) for f in os.listdir(os.path.join(ROOT, "aad")) if f.endswith(".py")]
    files.append(os.path.join(ROOT, "experiment_runner.py"))
    found = {}
    for path in files:
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in sys.stdlib_module_names or top == "aad":
                    continue
                where = f"{os.path.relpath(path, ROOT)}:{node.lineno}".replace("\\", "/")
                found.setdefault(name, []).append(where)
    return found


def c1_imports():
    modules = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, "aad")) if f.endswith(".py") and f != "__init__.py")
    for mod in ["aad"] + [f"aad.{m}" for m in modules] + ["experiment_runner"]:
        r = subprocess.run([sys.executable, "-c", f"import {mod}"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            record("C1", f"import {mod} (fresh process)", "PASS")
        else:
            record("C1", f"import {mod} (fresh process)", "FAIL", r.stderr.strip().splitlines()[-1])

    missing = [n for n in aad.__all__ if not hasattr(aad, n)]
    record("C1", "every name in aad.__all__ exists", "FAIL" if missing else "PASS",
           f"{len(aad.__all__)} names" + (f"; missing {missing}" if missing else ""))

    pins = set()
    for line in open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8"):
        m = re.match(r"\s*([A-Za-z0-9_.-]+)\s*==", line)
        if m:
            pins.add(norm(m.group(1)))
    dists = importlib.metadata.packages_distributions()

    for name, where in sorted(third_party_imports().items()):
        try:
            installed = importlib.util.find_spec(name) is not None
        except ModuleNotFoundError:
            installed = False
        top_dists = dists.get(name.split(".")[0], [])
        pinned = [d for d in top_dists if norm(d) in pins]
        if installed and pinned:
            record("C1", f"package for '{name}'", "PASS", f"installed, pinned as {pinned}")
        elif installed:
            record("C1", f"package for '{name}'", "FLAG", f"installed but not pinned; imported at {', '.join(where)}")
        else:
            record("C1", f"package for '{name}'", "FLAG", f"not installed; imported at {', '.join(where)}")


# ---------------------------------------------------------------------------
# C2: wiring between modules
# ---------------------------------------------------------------------------

def c2_wiring():
    from aad.config_space import EXTENDED_CONFIG_SPACE
    from aad.config_space import MEALPY_ALGORITHM_KEYS as CS_KEYS
    from aad.landscape_features import LandscapeFeatureExtractor
    from aad.mealpy_algorithms import MEALPY_ALGORITHM_KEYS as REG_KEYS
    import aad.meta_learner as ml

    alg = build_algorithm({"algorithm": "ea"})
    record("C2", "build_algorithm({'algorithm': 'ea'})", "PASS" if isinstance(alg, EvolutionaryAlgorithm) else "FAIL", repr(alg))

    alg = build_algorithm({})
    record("C2", "build_algorithm with no 'algorithm' key", "PASS" if isinstance(alg, EvolutionaryAlgorithm) else "FLAG",
           f"builds {alg!r}; the docstring says the EA (D1)")

    bad = []
    for key in REG_KEYS:
        try:
            alg = build_algorithm({"algorithm": key})
            alg._make_model()
            if not (isinstance(alg, MealpyAlgorithm) and alg.algorithm_key == key):
                bad.append(f"{key}: built {alg!r}")
        except Exception as e:  # noqa: BLE001
            bad.append(f"{key}: {type(e).__name__}: {e}")
    record("C2", f"build_algorithm reaches each of the {len(REG_KEYS)} mealpy algorithms", "FAIL" if bad else "PASS",
           "; ".join(bad) or "each builds MealpyAlgorithm and its mealpy class instantiates")

    same = set(CS_KEYS) == set(REG_KEYS) == set(MEALPY_REGISTRY)
    record("C2", "mealpy name lists agree (config_space, mealpy_algorithms, registry)", "PASS" if same else "FAIL",
           f"{len(CS_KEYS)}, {len(REG_KEYS)} and {len(MEALPY_REGISTRY)} names")

    # Which algorithm does EA_Designer run when the space has an 'algorithm' key?
    built = []

    class RecordingEA(EvolutionaryAlgorithm):
        def __init__(self, config):
            built.append(config.get("algorithm"))
            super().__init__(config)

    space = {**EXTENDED_CONFIG_SPACE, "population_size": [POP], "max_generations": [GENS]}
    ml.EvolutionaryAlgorithm = RecordingEA
    try:
        reseed()
        designer = ml.EA_Designer(config_space=space, population_size=4, generations=1, runs_per_eval=1, use_surrogate=False)
        best_cfg, _ = designer.evolve(aad.BBOB_F1_Sphere(dim=DIM), verbose=False)
    finally:
        ml.EvolutionaryAlgorithm = EvolutionaryAlgorithm
    named = [a for a in built if a not in (None, "ea")]
    record("C2", "EA_Designer with EXTENDED_CONFIG_SPACE", "FLAG" if named else "PASS",
           f"{len(built)} candidate runs; {len(named)} named a mealpy algorithm {sorted(set(named))} but ran the EA (D2); "
           f"returned best names '{best_cfg['algorithm']}'")

    # Problems
    classic = [aad.SphereProblem, aad.RastriginProblem, aad.RosenbrockProblem, aad.AckleyProblem, aad.ZDT1Problem, aad.ZDT2Problem]
    for cls in classic + bbob_classes():
        try:
            p = cls(dim=DIM)
            lb, ub = (np.asarray(b, dtype=float) for b in p.bounds())
            reseed()
            pts = lb + np.random.random((20, len(lb))) * (ub - lb)
            vals = [np.asarray(p.evaluate(x), dtype=float) for x in pts]
            problems = []
            if not all(hasattr(p, m) for m in ("evaluate", "bounds", "is_multiobjective", "name")):
                problems.append("missing interface method")
            if not isinstance(p.name, str):
                problems.append("name is not a string")
            if len(lb) != DIM:
                problems.append(f"bounds have length {len(lb)}")
            if not all(np.all(np.isfinite(v)) for v in vals):
                problems.append("non-finite value inside the bounds")
            detail = f"name {p.name}, multi-objective {p.is_multiobjective()}"
            status = "PASS"
            if hasattr(p, "xopt"):
                f_xopt = float(p.evaluate(p.xopt))
                lowest = min([f_xopt] + [float(v) for v in vals])
                detail += f", f(xopt) = {f_xopt:.6g}, lowest value seen {lowest:.6g}"
                if lowest < 0:
                    status = "FLAG"
                    detail += "; below 0, which the official BBOB function (minus its optimum value) never gives inside [-5, 5]"
                # Scale against ioh's reference BBOB (instance 1). Instances
                # differ, so only the order of magnitude is compared.
                ref = ioh.get_problem(p._fid, 1, DIM)
                median_ref = float(np.median([ref(x) - ref.optimum.y for x in pts]))
                median_own = float(np.median([float(v) for v in vals]))
                ratio = median_own / median_ref if median_ref > 0 else math.inf
                detail += f"; median at 20 random points {median_own:.4g} vs ioh reference {median_ref:.4g} (ratio {ratio:.3g})"
                if not 0.1 <= ratio <= 10:
                    status = "FLAG"
                    detail += ", more than 10 times off"
                if status == "FLAG":
                    detail += " (D12)"
            if problems:
                status = "FAIL"
                detail += "; " + "; ".join(problems)
            record("C2", f"problem {cls.__name__}", status, detail)
        except Exception as e:  # noqa: BLE001
            record("C2", f"problem {cls.__name__}", "FAIL", f"{type(e).__name__}: {e}")

    # Features for every single-objective problem
    keys, bad = None, []
    for cls in classic[:4] + bbob_classes():
        reseed()
        feats = LandscapeFeatureExtractor().extract_features(cls(dim=DIM))
        keys = keys or set(feats)
        if set(feats) != keys:
            bad.append(f"{cls.__name__}: keys {sorted(feats)}")
        if not all(math.isfinite(v) for v in feats.values()):
            bad.append(f"{cls.__name__}: non-finite {[k for k, v in feats.items() if not math.isfinite(v)]}")
    record("C2", "features: same keys, all finite, for 28 single-objective problems", "FAIL" if bad else "PASS",
           "; ".join(bad) or f"{len(keys)} keys: {sorted(keys)}")


# ---------------------------------------------------------------------------
# C3: algorithm runs
# ---------------------------------------------------------------------------

def c3_algorithms():
    configs = [ea_config(selection=s, crossover=c, mutation=m)
               for s in ("tournament", "roulette") for c in ("sbx", "uniform") for m in ("gaussian", "polynomial")]
    configs += [{"algorithm": k, "population_size": POP, "max_generations": GENS} for k in sorted(MEALPY_REGISTRY)]
    expected = POP * (GENS + 1)
    csv_rows = []

    for cfg in configs:
        label = cfg["algorithm"] if cfg["algorithm"] != "ea" else f"ea/{cfg['selection']}/{cfg['crossover']}/{cfg['mutation']}"
        for pcls in (aad.BBOB_F1_Sphere, aad.BBOB_F15_RastriginRotated):
            runs = []
            for run in (1, 2):
                prob = CountingProblem(pcls(dim=DIM))
                reseed()
                t0 = time.perf_counter()
                try:
                    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        _, best = build_algorithm(cfg).run(prob)
                    best, err = float(best), ""
                except Exception as e:  # noqa: BLE001
                    best, err = math.nan, f"{type(e).__name__}: {e}"
                secs = time.perf_counter() - t0
                runs.append({"algorithm": label, "problem": prob.name, "run": run, "error": err, "best": best,
                             "best_evaluated": prob.best_seen, "evaluations": prob.calls,
                             "expected_evaluations": expected, "seconds": round(secs, 4)})
            csv_rows += runs

            r1, r2 = runs
            if r1["error"] or r2["error"]:
                record("C3", f"{label} on {r1['problem']}", "FAIL", r1["error"] or r2["error"])
                continue
            reasons = []
            if not (math.isfinite(r1["best"]) and math.isfinite(r2["best"])):
                reasons.append("best value not finite")
            if r1["evaluations"] != expected:
                reasons.append(f"{r1['evaluations']} evaluations, not {expected}")
            if (r1["best"], r1["evaluations"]) != (r2["best"], r2["evaluations"]):
                reasons.append("same seed gave a different result")
            if not math.isclose(r1["best"], r1["best_evaluated"], rel_tol=1e-9, abs_tol=1e-12):
                reasons.append(f"reported best {r1['best']:.6g} differs from best evaluated {r1['best_evaluated']:.6g}")
            record("C3", f"{label} on {r1['problem']}", "FLAG" if reasons else "PASS",
                   "; ".join(reasons) or f"best {r1['best']:.6g}, {r1['evaluations']} evaluations, {r1['seconds']} s")

    with open(os.path.join(OUT, "algorithm_runs.csv"), "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)


# ---------------------------------------------------------------------------
# C4: other components on tiny cases
# ---------------------------------------------------------------------------

def c4_components():
    from aad.config_space import EA_CONFIG_SPACE
    from aad.landscape_features import LandscapeFeatureExtractor
    import aad.evaluation as ev
    import experiment_runner

    # Feature extractor: evaluations spent
    prob = CountingProblem(aad.BBOB_F1_Sphere(dim=DIM))
    fx = LandscapeFeatureExtractor()
    reseed()
    fx.extract_features(prob)
    once = fx.n_samples + 50 * DIM
    record("C4", "feature extractor: evaluations", "FLAG" if prob.calls > once else "PASS",
           f"{prob.calls} evaluations for {fx.n_samples} sample points in dimension {DIM}; "
           f"{once} if each point were evaluated once (D7)")

    # EA_Designer, surrogate off and on
    space = {**EA_CONFIG_SPACE, "population_size": [POP], "max_generations": [GENS]}
    for use_surrogate in (False, True):
        reseed()
        d = aad.EA_Designer(config_space=space, population_size=6, generations=2, runs_per_eval=1, use_surrogate=use_surrogate)
        measured, rejected = [], []
        evaluate_candidate, should_evaluate = d.evaluate_candidate, d._should_evaluate

        def rec_eval(cfg, problem):
            value = evaluate_candidate(cfg, problem)
            measured.append(value)
            return value

        def rec_should(*args):
            ok = should_evaluate(*args)
            rejected.append(not ok)
            return ok

        d.evaluate_candidate, d._should_evaluate = rec_eval, rec_should
        try:
            best_cfg, best = d.evolve(aad.BBOB_F1_Sphere(dim=DIM), verbose=False)
        except Exception as e:  # noqa: BLE001
            record("C4", f"EA_Designer, surrogate {'on' if use_surrogate else 'off'}", "FAIL", f"{type(e).__name__}: {e}")
            continue
        was_measured = best in measured
        record("C4", f"EA_Designer, surrogate {'on' if use_surrogate else 'off'}",
               "PASS" if was_measured and not any(rejected) else "FLAG",
               f"{len(measured)} candidates run, {sum(rejected)} scored by the surrogate's prediction × 1.05 instead"
               + (", and those scores entered selection and the surrogate's training data" if any(rejected) else "")
               + f"; returned best {best:.6g} was "
               f"{'a measured result' if was_measured else 'a prediction, not a measured result'}" + (" (D8)" if any(rejected) or not was_measured else ""))

    # LLMDesigner, rule-based
    problem = aad.BBOB_F1_Sphere(dim=DIM)
    designer = aad.LLMDesigner()
    desc = designer.generate_description(problem)
    reseed()
    cfg = designer.propose_algorithm(desc)
    valid = all(cfg.get(k) in v for k, v in EA_CONFIG_SPACE.items())
    record("C4", "LLMDesigner rule-based proposal", "PASS" if valid and "algorithm" in cfg else "FLAG",
           f"{cfg}; values valid: {valid}; it has no 'algorithm' key, so EvaluationFramework builds {build_algorithm(cfg)!r} (D1, D3)")
    record("C4", "LLMDesigner description", "FLAG" if problem.name in desc else "PASS",
           f"'{desc}'" + (" contains the problem's name (D4)" if problem.name in desc else ""))

    # LLMDesigner, LLM mode with a dummy key. Only when the client cannot be
    # imported, so that no request can reach the API.
    try:
        client_missing = importlib.util.find_spec("google.generativeai") is None
    except ModuleNotFoundError:
        client_missing = True
    if client_missing:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            reseed()
            cfg = aad.LLMDesigner(api_key="dummy-not-a-key").propose_algorithm(desc)
        record("C4", "LLMDesigner LLM mode (dummy key)", "FLAG",
               f"returned {cfg}, a rule-based pick, with only a printed message: '{out.getvalue().strip()}' (D4)")
    else:
        record("C4", "LLMDesigner LLM mode (dummy key)", "SKIP", "google.generativeai is installed; skipped so no request is sent")

    # EvaluationFramework
    reseed()
    framework = aad.EvaluationFramework(n_runs=2)
    metrics = framework.evaluate(ea_config(), aad.BBOB_F1_Sphere(dim=DIM))
    keys = {"best_fitness", "mean_fitness", "std_fitness", "worst_fitness", "convergence_speed", "stability", "mean_runtime", "histories"}
    record("C4", "EvaluationFramework.evaluate, 2 runs", "PASS" if keys <= set(metrics) and len(metrics["histories"]) == 2 else "FAIL",
           f"best_fitness {metrics['best_fitness']:.6g} is the best of the 2 runs, mean {metrics['mean_fitness']:.6g} (D10)")

    reseed()
    nan_metrics = framework.evaluate(ea_config(), ConstantProblem("nan"))
    ranked = framework.compare_configs([ea_config(), ea_config()], ConstantProblem("nan"), verbose=False)
    record("C4", "EvaluationFramework, every evaluation NaN", "FLAG",
           f"no error and no failure flag: best_fitness={nan_metrics['best_fitness']}, mean_fitness={nan_metrics['mean_fitness']}; "
           f"compare_configs still returns a ranking of {len(ranked)} (D10)")
    try:
        framework.evaluate(ea_config(), ConstantProblem("raise"))
        record("C4", "EvaluationFramework, evaluation raises", "PASS", "handled")
    except RuntimeError as e:
        record("C4", "EvaluationFramework, evaluation raises", "FLAG",
               f"the exception ({e}) stops the whole evaluation; no run is recorded as failed (D10)")

    # SurrogateModel: repeatability and units of the uncertainty
    rng = np.random.RandomState(SEED)
    X = rng.random_sample((60, 6))
    y = 1000.0 * (X ** 2).sum(axis=1) + rng.normal(0, 10, 60)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for kind in ("rf", "gp"):
            np.random.seed(SEED)
            m1, m2 = aad.SurrogateModel(kind), aad.SurrogateModel(kind)
            m1.fit(X, y)
            m2.fit(X, y)  # the global random state has moved on since m1
            p1 = m1.predict(X[:10])
            fits_diff = float(np.max(np.abs(p1 - m2.predict(X[:10]))))
            twice_diff = float(np.max(np.abs(p1 - m1.predict(X[:10]))))
            detail = (f"largest difference {fits_diff:.3g} between the two fits, {twice_diff:.3g} when one model "
                      f"predicts twice (predictions near {np.median(p1):.4g})")
            if kind == "rf":
                m1._model.set_params(n_jobs=1)
                m2._model.set_params(n_jobs=1)
                single = float(np.max(np.abs(m1.predict(X[:10]) - m2.predict(X[:10]))))
                detail += f"; with n_jobs=1 instead of -1: {single:.3g}"
            record("C4", f"SurrogateModel {kind}: two fits on the same data", "PASS" if fits_diff == twice_diff == 0 else "FLAG",
                   detail + ("" if fits_diff == twice_diff == 0 else " (D9)"))
            means, stds = m1.predict_with_uncertainty(X[:10])
            scale = float(m1._scaler_y.scale_[0])
            record("C4", f"SurrogateModel {kind}: units of predict_with_uncertainty", "FLAG" if not math.isclose(scale, 1.0) else "PASS",
                   f"mean in units of y (median {np.median(means):.4g}); spread returned as {np.median(stds):.4g}, "
                   f"which is {np.median(stds) * scale:.4g} in units of y (std of y = {scale:.4g}) (D9)")

    # Visualizer and run_experiment, writing to a temporary folder
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
        vis = aad.Visualizer(output_dir=tmp)
        paths = [
            vis.plot_fitness_curves(metrics["histories"]),
            vis.plot_pareto_front([[1.0, 2.0], [2.0, 1.0]]),
            vis.plot_meta_convergence([3.0, 2.0, 1.0]),
            vis.plot_algorithm_comparison([(ea_config(), metrics), (ea_config(), metrics)]),
        ]
        made = sum(os.path.exists(p) for p in paths)

        built = []

        def recording_build(config):
            alg = build_algorithm(config)
            built.append(repr(alg))
            return alg

        old_dir, ev.build_algorithm = experiment_runner.RESULTS_DIR, recording_build
        experiment_runner.RESULTS_DIR = tmp
        try:
            reseed()
            experiment_runner.run_experiment(problems=[aad.BBOB_F1_Sphere(dim=DIM)], meta_generations=1,
                                             meta_population_size=2, runs_per_eval=1, verbose=False)
            runner_ok = os.path.exists(os.path.join(tmp, "experiment_results.json"))
            runner_err = ""
        except Exception as e:  # noqa: BLE001
            runner_ok, runner_err = False, f"{type(e).__name__}: {e}"
        finally:
            ev.build_algorithm = build_algorithm
            experiment_runner.RESULTS_DIR = old_dir
    record("C4", "Visualizer: four plots", "PASS" if made == 4 else "FAIL", f"{made} of 4 files written")
    if not runner_ok:
        record("C4", "run_experiment on one problem", "FAIL", runner_err or "no results JSON written")
    else:
        record("C4", "run_experiment on one problem", "FLAG" if any("MealpyAlgorithm" in b for b in built) else "PASS",
               f"finished; EvaluationFramework built {built} for the LLM designer's and the final evaluation (D1, D14)")


# ---------------------------------------------------------------------------
# C5: test suite
# ---------------------------------------------------------------------------

def c5_tests():
    log = []
    summaries = []
    for i in (1, 2, 3):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                           cwd=ROOT, capture_output=True, text=True)
        lines = r.stdout.strip().splitlines()
        summaries.append(lines[-1] if lines else r.stderr.strip())
        log.append(f"===== run {i}, exit code {r.returncode} =====\n{r.stdout}{r.stderr}")
        record("C5", f"pytest run {i}", "PASS" if r.returncode == 0 else "FAIL", summaries[-1])
    with open(os.path.join(OUT, "pytest_runs.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log))

    tests = open(os.path.join(ROOT, "tests", "test_aad.py"), encoding="utf-8").read()
    untested = [n for n in aad.__all__ if not re.search(rf"\b{re.escape(n)}\b", tests)]
    record("C5", "public names never mentioned in tests/test_aad.py", "FLAG" if untested else "PASS",
           f"{len(untested)} of {len(aad.__all__)}: {untested} (D13)")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.perf_counter()
    for check in (c1_imports, c2_wiring, c3_algorithms, c4_components, c5_tests):
        try:
            check()
        except Exception as e:  # noqa: BLE001
            record(check.__name__[:2].upper(), f"{check.__name__} crashed", "FAIL", f"{type(e).__name__}: {e}")
    minutes = (time.perf_counter() - t0) / 60

    meta = {
        "date": date.today().isoformat(),
        "python": sys.version.split()[0],
        "git_head": git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes": bool(git("status", "--porcelain")),
        "seed": SEED,
        "minutes": round(minutes, 2),
    }
    counts = {s: sum(r["status"] == s for r in ROWS) for s in ("PASS", "FLAG", "FAIL", "SKIP")}
    with open(os.path.join(OUT, "health_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "counts": counts, "rows": ROWS}, fh, indent=2)

    lines = ["Phase 0 health check", ""]
    lines += [f"{k}: {v}" for k, v in meta.items()]
    lines += ["", "  ".join(f"{k} {v}" for k, v in counts.items()), ""]
    for check in ("C1", "C2", "C3", "C4", "C5"):
        lines.append(f"== {check} ==")
        lines += [f"[{r['status']}] {r['item']}" + (f": {r['detail']}" if r["detail"] else "") for r in ROWS if r["check"] == check]
        lines.append("")
    with open(os.path.join(OUT, "health_report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    main()
