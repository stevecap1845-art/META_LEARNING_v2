"""Phase 0 follow-up audit: the 24 BBOB classes, the algorithms' parameters,
and what experiment_runner.py actually runs.

The findings are written up in documents/context/phase0_context.md §9. Run
from the repository root:

    .venv\\Scripts\\python.exe scripts\\phase0_audit.py

Writes results/phase0/audit_*.csv and audit_report.txt. Nothing in aad/ is
changed; the runner trace patches two functions for the length of its calls.
"""

import contextlib
import csv
import importlib
import inspect
import io
import math
import os
import random
import sys
import tempfile
import warnings

import ioh
import numpy as np
from mealpy import FloatVar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "results", "phase0")
SEED = 0

import aad  # noqa: E402
from aad.evolutionary_algorithm import EvolutionaryAlgorithm, build_algorithm  # noqa: E402
from aad.mealpy_algorithms import MEALPY_REGISTRY  # noqa: E402

REPORT = []


def say(line=""):
    REPORT.append(line)
    print(line, flush=True)


def write_csv(name, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def reseed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


def bbob_class(fid):
    return next(getattr(aad, n) for n in aad.__all__ if n.startswith(f"BBOB_F{fid}_"))


# ---------------------------------------------------------------------------
# Part 1: BBOB classes against ioh's reference implementation
# ---------------------------------------------------------------------------

def lam(alpha, n):
    """Diagonal of the official Lambda^alpha: alpha^(i / (2(n-1)))."""
    return alpha ** (0.5 * np.arange(n) / (n - 1))


# The official definitions (Hansen et al. 2009) of the unrotated functions
# that the classes get wrong, built on each class's own helpers.
def official_f3(p, x):
    z = lam(10, p.dim) * p._t_asy(p._t_osz(x - p.xopt), beta=0.2)
    return 10 * (p.dim - np.cos(2 * np.pi * z).sum()) + z @ z


def official_f4(p, x):
    y = p._t_osz(x - p.xopt)
    s = lam(10, p.dim)
    s[0::2] *= np.where(y[0::2] > 0, 10.0, 1.0)
    z = s * y
    return 10 * (p.dim - np.cos(2 * np.pi * z).sum()) + z @ z + 100 * p._f_pen(x)


def official_f5(p, x):
    z = np.where(x * p.xopt < 25, x, p.xopt)
    return float(np.sum(5 * np.abs(p._s) - p._s * z))


def official_f20(p, x):
    a = np.abs(p.xopt)
    xh = 2 * np.sign(p.xopt) * x
    zh = xh.copy()
    zh[1:] += 0.25 * (xh[:-1] - 2 * a[:-1])
    z = 100 * (lam(10, p.dim) * (zh - 2 * a) + 2 * a)
    return -np.mean(z * np.sin(np.sqrt(np.abs(z)))) / 100 + 4.189828872724339 + 100 * p._f_pen(z / 100)


OFFICIAL = {3: official_f3, 4: official_f4, 5: official_f5, 20: official_f20}
UNROTATED = (1, 2, 3, 4, 5, 8, 20)  # no rotation matrix in the official definition


def official_rotated(fid, p, x):
    """Official definition of a rotated function, using the class's own xopt,
    R and Q in the positions where the class uses them."""
    n, R, Q, xo, osz, asy, pen = p.dim, p.R, p.Q, p.xopt, p._t_osz, p._t_asy, p._f_pen
    i = np.arange(n)
    if fid == 6:
        z = Q @ (lam(10, n) * (R @ (x - xo)))
        return osz(np.array([np.sum((np.where(z * xo > 0, 100.0, 1.0) * z) ** 2)]))[0] ** 0.9
    if fid == 7:
        zh = lam(10, n) * (R @ (x - xo))
        z = Q @ np.where(np.abs(zh) > 0.5, np.floor(0.5 + zh), np.floor(0.5 + 10 * zh) / 10)
        return 0.1 * max(abs(zh[0]) / 1e4, np.dot(10 ** (2 * i / (n - 1)), z ** 2)) + pen(x)
    if fid in (9, 19):
        z = max(1.0, np.sqrt(n) / 8) * (R @ x) + 0.5
        s = 100 * (z[:-1] ** 2 - z[1:]) ** 2 + (z[:-1] - 1) ** 2
        return s.sum() if fid == 9 else 10 / (n - 1) * np.sum(s / 4000 - np.cos(s)) + 10
    if fid in (10, 11):
        z = osz(R @ (x - xo))
        return np.dot(10 ** (6 * i / (n - 1)), z ** 2) if fid == 10 else 1e6 * z[0] ** 2 + z[1:] @ z[1:]
    if fid == 12:
        z = R @ asy(R @ (x - xo), beta=0.5)
        return z[0] ** 2 + 1e6 * z[1:] @ z[1:]
    if fid == 13:  # the class names its outer rotation R and the inner one Q
        z = R @ (lam(10, n) * (Q @ (x - xo)))
        return z[0] ** 2 + 100 * np.sqrt(z[1:] @ z[1:])
    if fid == 14:
        return np.sqrt(np.sum(np.abs(R @ (x - xo)) ** (2 + 4 * i / (n - 1))))
    if fid == 15:
        z = R @ (lam(10, n) * (Q @ asy(osz(R @ (x - xo)), beta=0.2)))
        return 10 * (n - np.cos(2 * np.pi * z).sum()) + z @ z
    if fid == 16:
        z = R @ (lam(0.01, n) * (Q @ osz(R @ (x - xo))))
        k = np.arange(12)
        f0 = np.sum(0.5 ** k * np.cos(np.pi * 3.0 ** k))
        total = np.sum(0.5 ** k * np.cos(2 * np.pi * 3.0 ** k * (z[:, None] + 0.5)))
        return 10 * (total / n - f0) ** 3 + 10 / n * pen(x)
    if fid in (17, 18):
        z = lam(10 if fid == 17 else 1000, n) * (Q @ asy(R @ (x - xo), beta=0.5))
        s = np.sqrt(z[:-1] ** 2 + z[1:] ** 2)
        return np.mean(np.sqrt(s) + np.sqrt(s) * np.sin(50 * s ** 0.2) ** 2) ** 2 + 10 * pen(x)
    if fid == 23:
        z = Q @ (lam(100, n) * (R @ (x - xo)))
        j = 2.0 ** np.arange(1, 33)
        inner = (np.abs(j * z[:, None] - np.round(j * z[:, None])) / j).sum(axis=1)
        return 10 / n ** 2 * np.prod((1 + (i + 1) * inner) ** (10 / n ** 1.2)) - 10 / n ** 2 + pen(x)
    if fid == 24:
        mu0, s = 2.5, 1 - 1 / (2 * np.sqrt(n + 20) - 8.2)
        mu1 = -np.sqrt((mu0 ** 2 - 1) / s)
        xh = 2 * np.sign(xo) * x
        z = Q @ (lam(100, n) * (R @ (xh - mu0)))
        return (min(np.sum((xh - mu0) ** 2), n + s * np.sum((xh - mu1) ** 2))
                + 10 * (n - np.cos(2 * np.pi * z).sum()) + 1e4 * pen(x))
    return None  # F21, F22: their parameters are compared by reading


def rel_diff(a, b):
    return float(np.max(np.abs(a - b) / np.maximum(1.0, np.abs(b))))


def constant_offset(own, reference):
    """The offset when the two differ by a constant only, else ''."""
    diff, scale = own - reference, max(1.0, np.abs(reference).max())
    if np.ptp(diff) <= 1e-9 * scale and abs(diff.mean()) > 1e-9 * scale:
        return float(diff.mean())
    return ""


INSTANCES = range(1, 11)


def median_ranges(fid, d, X):
    """Medians over the points for ioh instances 1-10 and for the official
    definition on class instances with seeds 1-10, to judge instance spread."""
    ioh_medians, def_medians = [], []
    for k in INSTANCES:
        ref, p = ioh.get_problem(fid, k, d), bbob_class(fid)(dim=d, seed=k)
        ioh_medians.append(np.median([ref(x) - ref.optimum.y for x in X]))
        def_medians.append(np.median([official_rotated(fid, p, x) for x in X]))
    return (min(ioh_medians), max(ioh_medians)), (min(def_medians), max(def_medians))


def audit_bbob():
    say("== Part 1: BBOB classes, 200 random points in [-5, 5]^d, ioh instance 1 as reference ==")
    say("unrotated functions: class given ioh's optimum, compared with ioh; rotated: class compared with the")
    say("official definition built from the class's own xopt, R and Q")
    rows = []
    rng = np.random.RandomState(SEED)
    for fid in range(1, 25):
        for d in (5, 10):
            p, ref = bbob_class(fid)(dim=d), ioh.get_problem(fid, 1, d)
            X = rng.uniform(-5, 5, size=(200, d))
            ref_vals = np.array([ref(x) - ref.optimum.y for x in X])
            own = np.array([p.evaluate(x) for x in X])
            row = {"function": f"F{fid}", "dim": d,
                   "median_class": float(np.median(own)), "median_ioh": float(np.median(ref_vals)),
                   "median_ratio_class_to_ioh": float(np.median(own) / np.median(ref_vals)),
                   "min_class": float(own.min()), "min_ioh": float(ref_vals.min()),
                   "reference": "", "class_max_rel_diff": "", "constant_offset": "",
                   "definition_check_against_ioh": ""}
            if fid in UNROTATED:
                p.xopt = np.array(ref.optimum.x)  # same instance as ioh
                if fid == 5:
                    p._s = np.sign(p.xopt) * 10 ** (np.arange(d) / (d - 1))
                own = np.array([p.evaluate(x) for x in X])
                row.update(reference="ioh, same optimum", class_max_rel_diff=rel_diff(own, ref_vals))
                if fid in OFFICIAL:
                    defined = np.array([OFFICIAL[fid](p, x) for x in X])
                    row["definition_check_against_ioh"] = f"max rel diff {rel_diff(defined, ref_vals):.3g}"
                    row["constant_offset"] = constant_offset(own, defined)
            elif official_rotated(fid, p, X[0]) is not None:
                defined = np.array([official_rotated(fid, p, x) for x in X])
                row.update(reference="definition, class's own matrices", class_max_rel_diff=rel_diff(own, defined),
                           constant_offset=constant_offset(own, defined))
                if d == 10:
                    (a, b), (c, e) = median_ranges(fid, d, X)
                    row["definition_check_against_ioh"] = (f"medians over 10 instances: ioh {a:.3g} to {b:.3g}, "
                                                           f"definition {c:.3g} to {e:.3g}")
            else:
                row["reference"] = "parameters compared by reading"
            rows.append(row)
            if d == 10:
                diff = row["class_max_rel_diff"]
                say(f"F{fid:<2} median class/ioh {row['median_ratio_class_to_ioh']:9.3g}  "
                    + (f"class vs {row['reference']}: max rel diff {diff:.3g}" if diff != "" else row["reference"])
                    + (f", constant offset {row['constant_offset']:.4g}" if row["constant_offset"] != "" else "")
                    + (f"; definition vs ioh: {row['definition_check_against_ioh']}" if row["definition_check_against_ioh"] else ""))
    write_csv("audit_bbob.csv", rows)


# ---------------------------------------------------------------------------
# Part 2: algorithm parameters, evaluations per epoch, equal-budget check
# ---------------------------------------------------------------------------

class Budget(Exception):
    pass


class Counter:
    """An ioh problem as f - fopt, with an evaluation count, the best value
    seen, and an optional hard budget."""

    def __init__(self, fid, d, budget=None):
        self.ref, self.d, self.budget = ioh.get_problem(fid, 1, d), d, budget
        self.calls, self.best = 0, math.inf

    def evaluate(self, x):
        if self.budget is not None and self.calls >= self.budget:
            raise Budget
        self.calls += 1
        value = float(self.ref(np.asarray(x, dtype=float)) - self.ref.optimum.y)
        self.best = min(self.best, value)
        return value

    def bounds(self):
        return [-5.0] * self.d, [5.0] * self.d

    def is_multiobjective(self):
        return False

    name = "ioh"


def mealpy_class(key):
    module, cls, _ = MEALPY_REGISTRY[key]
    return getattr(importlib.import_module(module), cls)


def audit_parameters():
    say()
    say("== Part 2a: parameters the framework leaves at mealpy's defaults ==")
    rows = []
    for key in sorted(MEALPY_REGISTRY):
        sig = inspect.signature(mealpy_class(key).__init__)
        params = {k: v.default for k, v in sig.parameters.items() if k not in ("self", "args", "kwargs", "epoch", "pop_size")}
        rows.append({"algorithm": key, "mealpy_class": ".".join(MEALPY_REGISTRY[key][:2]),
                     "passed_by_framework": "epoch, pop_size",
                     "left_at_default": params or "none",
                     "default_pop_size": sig.parameters["pop_size"].default})
        say(f"{key:8s} {params or 'no other parameters'}")
    write_csv("audit_algorithm_defaults.csv", rows)


def audit_evaluations_per_epoch():
    say()
    say("== Part 2b: evaluations used through the framework (ioh F1, d=5) ==")
    rows, per_epoch = [], {}
    for key in ["ea"] + sorted(MEALPY_REGISTRY):
        counts = {}
        for pop in (20, 40):
            for gens in (10, 20):
                c = Counter(1, 5)
                reseed()
                with quiet():
                    build_algorithm({"algorithm": key, "population_size": pop, "max_generations": gens}).run(c)
                counts[pop, gens] = c.calls
        row = {"algorithm": key}
        for (pop, gens), n in counts.items():
            row[f"evals_pop{pop}_gens{gens}"] = n
        for pop in (20, 40):
            row[f"per_epoch_pop{pop}"] = (counts[pop, 20] - counts[pop, 10]) / 10
            row[f"initial_pop{pop}"] = counts[pop, 10] - 10 * row[f"per_epoch_pop{pop}"]
        rows.append(row)
        per_epoch[key] = (row["initial_pop20"], row["per_epoch_pop20"])
        say(f"{key:8s} pop 20: {row['initial_pop20']:g} at start + {row['per_epoch_pop20']:g} per generation; "
            f"pop 40: {row['initial_pop40']:g} + {row['per_epoch_pop40']:g}")
    write_csv("audit_evaluations_per_epoch.csv", rows)
    return per_epoch


BUDGET, DIM, POP = 5000, 5, 20
FUNCTIONS = (1, 10, 15)  # sphere, rotated ellipsoid, rotated Rastrigin
SEEDS = range(5)
VARIANTS = {"DE_F0.5": ("DE", {"wf": 0.5}),
            "PSO_constriction": ("PSO", {"w": 0.7298, "c1": 1.49618, "c2": 1.49618})}


def run_once(label, fid, seed, per_epoch):
    c = Counter(fid, DIM, budget=BUDGET)
    reseed(seed)
    try:
        with quiet():
            if label == "random_search":
                rng = np.random.RandomState(seed)
                while True:
                    c.evaluate(rng.uniform(-5, 5, DIM))
            elif label.startswith("ea/"):
                sel, cx, mut = label.split("/")[1:]
                EvolutionaryAlgorithm({"population_size": POP, "max_generations": BUDGET // POP,
                                       "selection": sel, "crossover": cx, "mutation": mut}).run(c)
            else:
                key, params = VARIANTS.get(label, (label, {}))
                start, step = per_epoch[key]
                epochs = max(1, int((BUDGET - start) // max(step, 1)))
                model = mealpy_class(key)(epoch=epochs, pop_size=POP, **params)
                model.solve({"obj_func": c.evaluate, "bounds": FloatVar(lb=(-5.0,) * DIM, ub=(5.0,) * DIM),
                             "minmax": "min", "log_to": None}, seed=seed)
    except Budget:
        pass
    return c.best, c.calls


def audit_equal_budget(per_epoch):
    say()
    say(f"== Part 2c: equal budget ({BUDGET} evaluations, d={DIM}, population {POP}, "
        f"ioh F{FUNCTIONS} instance 1, seeds {list(SEEDS)}); median best f - fopt ==")
    labels = (["random_search"]
              + [f"ea/{s}/{c}/{m}" for s in ("tournament", "roulette") for c in ("sbx", "uniform") for m in ("gaussian", "polynomial")]
              + sorted(MEALPY_REGISTRY) + list(VARIANTS))
    runs, medians = [], {}
    for label in labels:
        for fid in FUNCTIONS:
            values = []
            for seed in SEEDS:
                best, used = run_once(label, fid, seed, per_epoch)
                runs.append({"candidate": label, "function": f"F{fid}", "seed": seed, "best_f_minus_fopt": best, "evaluations": used})
                values.append(best)
            medians[label, fid] = float(np.median(values))
        say(f"{label:34s} " + "  ".join(f"F{fid} {medians[label, fid]:10.4g}" for fid in FUNCTIONS))
    write_csv("audit_equal_budget_runs.csv", runs)
    worse = [label for label in labels[1:] if medians[label, 1] >= medians["random_search", 1]]
    say(f"no better than random search on F1 (sphere): {worse or 'none'}")


# ---------------------------------------------------------------------------
# Part 3: what experiment_runner.py runs for each of its 24 problems
# ---------------------------------------------------------------------------

class CountingProblem:
    def __init__(self, problem):
        self.problem, self.calls = problem, 0

    def evaluate(self, x):
        self.calls += 1
        return self.problem.evaluate(x)

    def __getattr__(self, name):
        return getattr(self.problem, name)


def audit_runner():
    import aad.evaluation as ev
    import aad.meta_learner as ml
    import experiment_runner

    say()
    say("== Part 3: run_experiment on its 24 default problems (BBOB, dim 10, default seed), "
        "meta-search cut to 2 configurations x 1 generation x 1 run ==")
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        old_dir, experiment_runner.RESULTS_DIR = experiment_runner.RESULTS_DIR, tmp
        try:
            for fid in range(1, 25):
                meta_runs, built = [], []

                class RecordingEA(EvolutionaryAlgorithm):
                    def __init__(self, config):
                        meta_runs.append(config.get("algorithm", "no algorithm key"))
                        super().__init__(config)

                def recording_build(config):
                    alg = build_algorithm(config)
                    built.append(repr(alg))
                    return alg

                ml.EvolutionaryAlgorithm, ev.build_algorithm = RecordingEA, recording_build
                problem = CountingProblem(bbob_class(fid)(dim=10))
                reseed()
                with quiet():
                    result = experiment_runner.run_experiment(problems=[problem], meta_generations=1,
                                                              meta_population_size=2, runs_per_eval=1, verbose=False)
                entry = result[problem.name]
                rows.append({"problem": problem.name, "dim": len(problem.bounds()[0]), "evaluations": problem.calls,
                             "meta_search_runs": len(meta_runs),
                             "meta_search_ran": "EvolutionaryAlgorithm for every candidate",
                             "meta_search_algorithm_keys": sorted(set(meta_runs)),
                             "best_config": entry["meta_learning"]["best_config"],
                             "llm_designer_config": entry["llm_designer"]["config"],
                             "llm_designer_evaluation_ran": built[0],
                             "final_evaluation_ran": built[1]})
        finally:
            ml.EvolutionaryAlgorithm, ev.build_algorithm = EvolutionaryAlgorithm, build_algorithm
            experiment_runner.RESULTS_DIR = old_dir
    write_csv("audit_runner_trace.csv", rows)
    say(f"{len(rows)} problems ran. Meta-search algorithm keys seen: {sorted({k for r in rows for k in r['meta_search_algorithm_keys']})}")
    say(f"LLM designer's evaluation built: {sorted({r['llm_designer_evaluation_ran'].split(',')[0] for r in rows})}")
    say(f"final evaluation built: {sorted({r['final_evaluation_ran'].split(',')[0] for r in rows})}")


def main():
    os.makedirs(OUT, exist_ok=True)
    audit_bbob()
    audit_parameters()
    per_epoch = audit_evaluations_per_epoch()
    audit_equal_budget(per_epoch)
    audit_runner()
    with open(os.path.join(OUT, "audit_report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT) + "\n")


if __name__ == "__main__":
    main()
