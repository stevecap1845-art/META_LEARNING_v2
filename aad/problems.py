"""
problems.py
-----------
Optimisation problem interface and a collection of benchmark functions.

Classes
-------
OptimizationProblem          : Abstract base class for all problems.
SphereProblem                : Sphere (unimodal, continuous).
RastriginProblem             : Rastrigin (highly multimodal, continuous).
RosenbrockProblem            : Rosenbrock (narrow valley, continuous).
AckleyProblem                : Ackley (nearly flat outer region, one global min).
ZDT1Problem                  : ZDT1 (multi-objective, convex Pareto front).
ZDT2Problem                  : ZDT2 (multi-objective, non-convex Pareto front).

BBOB suite (24 functions, COCO/BBOB 2009)
------------------------------------------
BBOB_F1_Sphere                    : F1  – Sphere
BBOB_F2_EllipsoidalSeparable      : F2  – Ellipsoidal (separable)
BBOB_F3_RastriginSeparable        : F3  – Rastrigin (separable)
BBOB_F4_BucheRastrigin            : F4  – Büche-Rastrigin
BBOB_F5_LinearSlope               : F5  – Linear slope
BBOB_F6_AttractiveSector          : F6  – Attractive sector
BBOB_F7_StepEllipsoidal           : F7  – Step ellipsoidal
BBOB_F8_Rosenbrock                : F8  – Rosenbrock (original)
BBOB_F9_RosenbrockRotated         : F9  – Rosenbrock (rotated)
BBOB_F10_EllipsoidalRotated       : F10 – Ellipsoidal (rotated)
BBOB_F11_Discus                   : F11 – Discus
BBOB_F12_BentCigar                : F12 – Bent cigar
BBOB_F13_SharpRidge               : F13 – Sharp ridge
BBOB_F14_DifferentPowers          : F14 – Different powers
BBOB_F15_RastriginRotated         : F15 – Rastrigin (rotated)
BBOB_F16_Weierstrass              : F16 – Weierstrass
BBOB_F17_SchaffersF7              : F17 – Schaffer's F7
BBOB_F18_SchaffersF7IllConditioned: F18 – Schaffer's F7 (ill-conditioned)
BBOB_F19_GriewankRosenbrock       : F19 – Composite Griewank-Rosenbrock
BBOB_F20_Schwefel                 : F20 – Schwefel
BBOB_F21_Gallagher101             : F21 – Gallagher 101-me peaks
BBOB_F22_Gallagher21              : F22 – Gallagher 21-hi peaks
BBOB_F23_Katsuura                 : F23 – Katsuura
BBOB_F24_LunacekBiRastrigin       : F24 – Lunacek bi-Rastrigin
"""

from abc import ABC, abstractmethod

import numpy as np


class OptimizationProblem(ABC):
    """
    Abstract interface that every optimisation problem must implement.

    Subclasses must define:
        evaluate(solution) -> float | list[float]
        bounds()           -> (list[float], list[float])   # (lower, upper)
        is_multiobjective()-> bool
    """

    @abstractmethod
    def evaluate(self, solution):
        """
        Evaluate a candidate solution.

        Parameters
        ----------
        solution : array-like of shape (dim,)

        Returns
        -------
        float for single-objective problems, list[float] for multi-objective.
        """

    @abstractmethod
    def bounds(self):
        """
        Return the search-space bounds.

        Returns
        -------
        (lb, ub) : tuple of two lists of length *dim*.
        """

    @abstractmethod
    def is_multiobjective(self):
        """Return True if the problem has more than one objective."""

    @property
    def name(self):
        """Human-readable problem name (defaults to class name)."""
        return self.__class__.__name__

    @property
    def dimension(self):
        """Number of decision variables."""
        return len(self.bounds()[0])


# ---------------------------------------------------------------------------
# Single-objective benchmark problems
# ---------------------------------------------------------------------------

class SphereProblem(OptimizationProblem):
    """
    Sphere function:  f(x) = sum_i x_i^2

    Global minimum at x = 0 with f(0) = 0.
    Unimodal and separable – useful as a baseline.
    """

    def __init__(self, dim: int = 10):
        self.dim = dim

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        return float(np.sum(x ** 2))

    def bounds(self):
        lb = [-5.12] * self.dim
        ub = [5.12] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return False


class RastriginProblem(OptimizationProblem):
    """
    Rastrigin function:  f(x) = 10n + sum_i [x_i^2 - 10*cos(2*pi*x_i)]

    Highly multimodal with many local minima.
    Global minimum at x = 0 with f(0) = 0.
    """

    def __init__(self, dim: int = 10):
        self.dim = dim

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = len(x)
        return float(10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x)))

    def bounds(self):
        lb = [-5.12] * self.dim
        ub = [5.12] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return False


class RosenbrockProblem(OptimizationProblem):
    """
    Rosenbrock (banana) function:
        f(x) = sum_{i=1}^{n-1} [100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2]

    Global minimum at x = 1 with f(1,...,1) = 0.
    Narrow, curved valley makes it challenging for simple optimisers.
    """

    def __init__(self, dim: int = 10):
        self.dim = dim

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        return float(
            np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1.0 - x[:-1]) ** 2)
        )

    def bounds(self):
        lb = [-5.0] * self.dim
        ub = [5.0] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return False


class AckleyProblem(OptimizationProblem):
    """
    Ackley function:
        f(x) = -a*exp(-b*sqrt(mean(x^2))) - exp(mean(cos(c*x))) + a + e

    Nearly flat outer region with a single global minimum at x = 0 (f = 0).
    Tests the ability to escape shallow local optima.
    """

    def __init__(self, dim: int = 10, a: float = 20.0, b: float = 0.2,
                 c: float = 2 * np.pi):
        self.dim = dim
        self.a = a
        self.b = b
        self.c = c

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = len(x)
        term1 = -self.a * np.exp(-self.b * np.sqrt(np.sum(x ** 2) / n))
        term2 = -np.exp(np.sum(np.cos(self.c * x)) / n)
        return float(term1 + term2 + self.a + np.e)

    def bounds(self):
        lb = [-32.768] * self.dim
        ub = [32.768] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return False


# ---------------------------------------------------------------------------
# Multi-objective benchmark problems (ZDT family)
# ---------------------------------------------------------------------------

class ZDT1Problem(OptimizationProblem):
    """
    ZDT1:  f1 = x1,  f2 = g * h,  h = 1 - sqrt(f1/g)
           g = 1 + 9 * sum(x_{2..n}) / (n-1)

    Convex Pareto-optimal front.
    """

    def __init__(self, dim: int = 30):
        self.dim = dim

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        f1 = float(x[0])
        g = 1.0 + 9.0 * np.sum(x[1:]) / (self.dim - 1)
        h = 1.0 - np.sqrt(f1 / g)
        f2 = float(g * h)
        return [f1, f2]

    def bounds(self):
        lb = [0.0] * self.dim
        ub = [1.0] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return True


class ZDT2Problem(OptimizationProblem):
    """
    ZDT2:  f1 = x1,  f2 = g * h,  h = 1 - (f1/g)^2
           g = 1 + 9 * sum(x_{2..n}) / (n-1)

    Non-convex Pareto-optimal front.
    """

    def __init__(self, dim: int = 30):
        self.dim = dim

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        f1 = float(x[0])
        g = 1.0 + 9.0 * np.sum(x[1:]) / (self.dim - 1)
        h = 1.0 - (f1 / g) ** 2
        f2 = float(g * h)
        return [f1, f2]

    def bounds(self):
        lb = [0.0] * self.dim
        ub = [1.0] * self.dim
        return lb, ub

    def is_multiobjective(self):
        return True


# ---------------------------------------------------------------------------
# Black Box Optimization Benchmark (BBOB / COCO) – all 24 functions
# ---------------------------------------------------------------------------

class _BBOBBase(OptimizationProblem):
    """
    Base class for the BBOB 2009 single-objective benchmark suite.

    All 24 BBOB functions share:
    - Search domain  : [-5, 5]^n
    - Global optimum : xopt drawn uniformly from [-4, 4]^n (seeded)
    - Two random rotation matrices R and Q (seeded)
    - Standard transformations T_osz and T_asy

    Parameters
    ----------
    dim  : int   – problem dimensionality (default 10)
    seed : int   – RNG seed for reproducible xopt / rotation matrices
    """

    _fid: int = 0  # BBOB function index (1-24)

    def __init__(self, dim: int = 10, seed: int = 42):
        self.dim = dim
        rng = np.random.RandomState(seed)
        n = dim

        # Global optimum (uniform in [-4, 4]^n)
        self.xopt = rng.uniform(-4.0, 4.0, size=n)

        # Two independent random rotation matrices
        self.R = self._random_rotation(n, rng)
        self.Q = self._random_rotation(n, rng)

        # Diagonal scaling matrices as 1-D arrays
        if n > 1:
            idx = np.arange(n, dtype=float)
            self._lam10 = 10.0 ** (6.0 * idx / (n - 1))      # cond 10^6
            self._lam100 = 10.0 ** (4.0 * idx / (n - 1))     # cond 10^4
        else:
            self._lam10 = np.ones(1)
            self._lam100 = np.ones(1)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _random_rotation(n: int, rng: np.random.RandomState) -> np.ndarray:
        """Random orthogonal matrix via QR decomposition."""
        A = rng.standard_normal((n, n))
        Q, _ = np.linalg.qr(A)
        return Q

    @staticmethod
    def _t_osz(x: np.ndarray) -> np.ndarray:
        """Oscillation transformation T_osz (applied element-wise)."""
        y = np.zeros_like(x, dtype=float)
        nz = x != 0.0
        x_hat = np.where(nz, np.log(np.abs(np.where(nz, x, 1.0))), 0.0)
        c1 = np.where(x > 0, 10.0, 5.5)
        c2 = np.where(x > 0, 7.9, 3.1)
        y = np.where(
            nz,
            np.sign(x) * np.exp(x_hat + 0.049 * (np.sin(c1 * x_hat) + np.sin(c2 * x_hat))),
            0.0,
        )
        return y

    @staticmethod
    def _t_asy(x: np.ndarray, beta: float = 0.5) -> np.ndarray:
        """Asymmetry transformation T_asy^beta."""
        n = len(x)
        if n == 1:
            return x.copy()
        y = x.copy()
        idx = np.arange(n, dtype=float)
        pos = x > 0
        exponents = 1.0 + beta * (idx / (n - 1)) * np.sqrt(np.where(pos, x, 0.0))
        y = np.where(pos, np.where(pos, x, 1.0) ** exponents, x)
        return y

    @staticmethod
    def _f_pen(x: np.ndarray) -> float:
        """Penalty for leaving [-5, 5]^n."""
        return float(np.sum(np.maximum(0.0, np.abs(x) - 5.0) ** 2))

    def bounds(self):
        return [-5.0] * self.dim, [5.0] * self.dim

    def is_multiobjective(self):
        return False

    @property
    def name(self):
        return f"BBOB_F{self._fid}_{type(self).__name__.replace('BBOB_F', '').split('_', 1)[-1]}"


# ---- Group 1: Separable functions (F1-F5) --------------------------------

class BBOB_F1_Sphere(_BBOBBase):
    """
    BBOB F1 – Sphere function.
    f(x) = ||z||^2,  z = x - xopt.
    Unimodal, separable, highly symmetric.
    """
    _fid = 1

    def evaluate(self, solution):
        z = np.asarray(solution, dtype=float) - self.xopt
        return float(np.dot(z, z))


class BBOB_F2_EllipsoidalSeparable(_BBOBBase):
    """
    BBOB F2 – Separable ellipsoidal function.
    f(x) = sum_i 10^{6(i-1)/(n-1)} * z_i^2,  z = T_osz(x - xopt).
    Unimodal, separable, ill-conditioned (cond = 10^6).
    """
    _fid = 2

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self._t_osz(x - self.xopt)
        return float(np.dot(self._lam10, z ** 2))


class BBOB_F3_RastriginSeparable(_BBOBBase):
    """
    BBOB F3 – Separable Rastrigin function.
    f(x) = 10*(n - sum cos(2*pi*z_i)) + ||z||^2,
    z = Lambda^10 * T_asy^0.2(T_osz(x - xopt)).
    Highly multimodal, separable.
    """
    _fid = 3

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self._lam10 * self._t_asy(self._t_osz(x - self.xopt), beta=0.2)
        n = self.dim
        return float(10.0 * (n - np.sum(np.cos(2.0 * np.pi * z))) + np.dot(z, z))


class BBOB_F4_BucheRastrigin(_BBOBBase):
    """
    BBOB F4 – Büche-Rastrigin function.
    Like F3 but with a skewed scaling to break separability partially.
    Multimodal, non-separable.
    """
    _fid = 4

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        # Ensure xopt[0::2] > 0 (odd-indexed coordinates positive)
        self.xopt[0::2] = np.abs(self.xopt[0::2])

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        z_raw = self._t_osz(x - self.xopt)
        # Scaling: s_i = 10^{(i)/(2*(n-1))} for even i with xopt_i > 0
        s = np.ones(n)
        for i in range(0, n, 2):
            s[i] = 10.0 ** (0.5 * i / max(n - 1, 1))
        z = s * z_raw
        return float(
            10.0 * (n - np.sum(np.cos(2.0 * np.pi * z)))
            + np.dot(z, z)
            + 100.0 * self._f_pen(x)
        )


class BBOB_F5_LinearSlope(_BBOBBase):
    """
    BBOB F5 – Linear slope.
    f(x) = -sum_i s_i * z_i,  z_i = clamp(x_i, -5*sign(xopt_i), 5*sign(xopt_i)).
    No global curvature; tests ability to follow a gradient.
    """
    _fid = 5

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        n = self.dim
        # Force xopt to boundary ±5
        self.xopt = 5.0 * np.sign(self.xopt)
        idx = np.arange(n, dtype=float)
        self._s = np.sign(self.xopt) * 10.0 ** (idx / max(n - 1, 1))

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = np.where(
            self.xopt > 0,
            np.minimum(x, self.xopt),
            np.maximum(x, self.xopt),
        )
        return float(-np.dot(self._s, z))


# ---- Group 2: Low / moderate conditioning (F6-F9) ------------------------

class BBOB_F6_AttractiveSector(_BBOBBase):
    """
    BBOB F6 – Attractive sector function.
    The global basin of attraction is a narrow sector around xopt.
    f(x) = T_osz(sum_i (s_i * z_i)^2)^{0.9},
    z = Q * Lambda^10 * R * (x - xopt).
    """
    _fid = 6

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.Q @ (self._lam10 * (self.R @ (x - self.xopt)))
        # Sector weighting
        s = np.where(z * self.xopt > 0, 100.0, 1.0)
        val = self._t_osz(np.array([np.sum((s * z) ** 2)]))[0]
        return float(val ** 0.9)


class BBOB_F7_StepEllipsoidal(_BBOBBase):
    """
    BBOB F7 – Step ellipsoidal function.
    Uses floor() to create plateaus; tests exploitation of steps.
    """
    _fid = 7

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z_hat = self._lam10 ** 0.5 * (self.R @ (x - self.xopt))
        z = np.where(
            np.abs(z_hat) > 0.5,
            np.floor(0.5 + z_hat),
            np.floor(0.5 + 10.0 * z_hat) / 10.0,
        )
        n = self.dim
        idx = np.arange(n, dtype=float)
        w = 10.0 ** (2.0 * idx / max(n - 1, 1))
        return float(0.1 * max(np.abs(z_hat[0]) / 1e4, np.dot(w, z ** 2)) + self._f_pen(x))


class BBOB_F8_Rosenbrock(_BBOBBase):
    """
    BBOB F8 – Rosenbrock function (original).
    Shifted/scaled Rosenbrock; narrow curved valley.
    """
    _fid = 8

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        scale = max(1.0, np.sqrt(self.dim) / 8.0)
        z = scale * (x - self.xopt) + 1.0
        return float(np.sum(100.0 * (z[:-1] ** 2 - z[1:]) ** 2 + (z[:-1] - 1.0) ** 2))


class BBOB_F9_RosenbrockRotated(_BBOBBase):
    """
    BBOB F9 – Rosenbrock function (rotated).
    Same as F8 but the initial rotation removes separability.
    """
    _fid = 9

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        scale = max(1.0, np.sqrt(self.dim) / 8.0)
        z = scale * (self.R @ x) + 0.5
        return float(np.sum(100.0 * (z[:-1] ** 2 - z[1:]) ** 2 + (z[:-1] - 1.0) ** 2))


# ---- Group 3: High conditioning (F10-F14) --------------------------------

class BBOB_F10_EllipsoidalRotated(_BBOBBase):
    """
    BBOB F10 – Ellipsoidal function (rotated, ill-conditioned).
    f(x) = sum_i 10^{6*(i-1)/(n-1)} * z_i^2, z = R * T_osz(x - xopt).
    """
    _fid = 10

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ self._t_osz(x - self.xopt)
        return float(np.dot(self._lam10, z ** 2))


class BBOB_F11_Discus(_BBOBBase):
    """
    BBOB F11 – Discus / Tablet function.
    f(x) = 10^6 * z_1^2 + sum_{i=2}^n z_i^2, z = R * T_osz(x - xopt).
    One dominant direction (high condition number).
    """
    _fid = 11

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ self._t_osz(x - self.xopt)
        return float(1e6 * z[0] ** 2 + np.dot(z[1:], z[1:]))


class BBOB_F12_BentCigar(_BBOBBase):
    """
    BBOB F12 – Bent cigar function.
    f(x) = z_1^2 + 10^6 * sum_{i=2}^n z_i^2,
    z = R * T_asy^0.5(R * (x - xopt)).
    Elongated, rotated, asymmetric.
    """
    _fid = 12

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ self._t_asy(self.R @ (x - self.xopt), beta=0.5)
        return float(z[0] ** 2 + 1e6 * np.dot(z[1:], z[1:]))


class BBOB_F13_SharpRidge(_BBOBBase):
    """
    BBOB F13 – Sharp ridge function.
    f(x) = z_1^2 + 100 * sqrt(sum_{i=2}^n z_i^2),
    z = R * Lambda^10 * Q * (x - xopt).
    """
    _fid = 13

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ (self._lam10 * (self.Q @ (x - self.xopt)))
        ridge = np.sqrt(np.dot(z[1:], z[1:])) if self.dim > 1 else 0.0
        return float(z[0] ** 2 + 100.0 * ridge)


class BBOB_F14_DifferentPowers(_BBOBBase):
    """
    BBOB F14 – Sum of different powers.
    f(x) = sqrt(sum_i |z_i|^{2+4*(i-1)/(n-1)}), z = R * (x - xopt).
    Varying curvature along rotated axes.
    """
    _fid = 14

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        n = self.dim
        idx = np.arange(n, dtype=float)
        self._powers = 2.0 + 4.0 * idx / max(n - 1, 1)

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ (x - self.xopt)
        return float(np.sqrt(np.sum(np.abs(z) ** self._powers)))


# ---- Group 4: Multi-modal functions (F15-F19) ----------------------------

class BBOB_F15_RastriginRotated(_BBOBBase):
    """
    BBOB F15 – Rastrigin function (rotated).
    f(x) = 10*(n - sum cos(2*pi*z_i)) + ||z||^2,
    z = R * Lambda^10 * Q * T_asy^0.2(R * T_osz(x - xopt)).
    Non-separable, highly multimodal.
    """
    _fid = 15

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self.R @ (self._lam10 * (self.Q @ self._t_asy(
            self.R @ self._t_osz(x - self.xopt), beta=0.2
        )))
        n = self.dim
        return float(10.0 * (n - np.sum(np.cos(2.0 * np.pi * z))) + np.dot(z, z))


class BBOB_F16_Weierstrass(_BBOBBase):
    """
    BBOB F16 – Weierstrass function.
    f(x) = sum_i sum_{k=0}^{11} 0.5^k cos(2*pi*3^k*(z_i+0.5)) - n*f0 + penalty,
    z = R * Lambda^{1/100} * Q * T_osz(R * (x - xopt)).
    Continuous but non-differentiable at the optimum.
    """
    _fid = 16

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        k = np.arange(12, dtype=float)
        self._ak = 0.5 ** k
        self._bk = 3.0 ** k
        self._f0 = float(np.sum(self._ak * np.cos(np.pi * self._bk)))

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        lam = 10.0 ** (-2.0 * np.arange(n, dtype=float) / max(n - 1, 1))
        z = self.R @ (lam * (self.Q @ self._t_osz(self.R @ (x - self.xopt))))
        val = 0.0
        for zi in z:
            val += np.sum(self._ak * np.cos(2.0 * np.pi * self._bk * (zi + 0.5)))
        return float(10.0 * (val / n - self._f0) ** 3 + 10.0 / n * self._f_pen(x))


class BBOB_F17_SchaffersF7(_BBOBBase):
    """
    BBOB F17 – Schaffer's F7 function.
    Tests performance on non-separable, multi-modal landscape with
    a moderate conditioning number.
    """
    _fid = 17

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        z = self._lam10 ** 0.5 * (self.Q @ self._t_asy(self.R @ (x - self.xopt), beta=0.5))
        n = self.dim
        if n < 2:
            return 0.0
        s = np.sqrt(z[:-1] ** 2 + z[1:] ** 2)
        val = np.mean(np.sqrt(s) * (1.0 + np.sin(50.0 * s ** 0.2) ** 2)) ** 2
        return float(val + 10.0 / n * self._f_pen(x))


class BBOB_F18_SchaffersF7IllConditioned(_BBOBBase):
    """
    BBOB F18 – Schaffer's F7 (ill-conditioned).
    Same structure as F17 but with condition number 1000^2 instead of 10.
    """
    _fid = 18

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        if n > 1:
            lam = 1000.0 ** (np.arange(n, dtype=float) / (n - 1))
        else:
            lam = np.ones(1)
        z = lam * (self.Q @ self._t_asy(self.R @ (x - self.xopt), beta=0.5))
        if n < 2:
            return 0.0
        s = np.sqrt(z[:-1] ** 2 + z[1:] ** 2)
        val = np.mean(np.sqrt(s) * (1.0 + np.sin(50.0 * s ** 0.2) ** 2)) ** 2
        return float(val + 10.0 / n * self._f_pen(x))


class BBOB_F19_GriewankRosenbrock(_BBOBBase):
    """
    BBOB F19 – Composite Griewank-Rosenbrock (F8F2).
    Combines the structure of Rosenbrock with Griewank-like cosine terms.
    """
    _fid = 19

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        scale = max(1.0, np.sqrt(self.dim) / 8.0)
        z = scale * (self.R @ x) + 0.5
        s = 100.0 * (z[:-1] ** 2 - z[1:]) ** 2 + (z[:-1] - 1.0) ** 2
        val = np.sum(s / 4000.0 - np.cos(s)) + 1.0
        return float(10.0 * val / (self.dim - 1) if self.dim > 1 else 0.0)


# ---- Group 5: Weakly structured multi-modal (F20-F24) --------------------

class BBOB_F20_Schwefel(_BBOBBase):
    """
    BBOB F20 – Schwefel function.
    Global optimum is far from many strong local optima.
    Tests ability to locate the correct basin.
    """
    _fid = 20

    _OFFSET = 4.189828872724338  # approx 0.42*10

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        x_hat = 2.0 * np.sign(self.xopt) * x
        # Cumulative transformation
        z = np.empty(n)
        z[0] = x_hat[0]
        for i in range(1, n):
            z[i] = x_hat[i] + 0.25 * (x_hat[i - 1] - 2.0 * np.abs(self.xopt[i - 1]))
        z = 100.0 * (z - 2.0 * np.abs(self.xopt)) + 2.0 * np.abs(self.xopt)
        val = -np.mean(z * np.sin(np.sqrt(np.abs(z))))
        return float(val + self._OFFSET + 100.0 * self._f_pen(x / 100.0 + 0.5))


class BBOB_F21_Gallagher101(_BBOBBase):
    """
    BBOB F21 – Gallagher's Gaussian 101-me peaks function.
    101 optima of varying height; tests global search ability.
    """
    _fid = 21
    _N_PEAKS = 101

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        rng = np.random.RandomState(seed + 1000)
        n, k = self.dim, self._N_PEAKS
        # Peak locations y_i in [-5, 5]^n; first peak at xopt
        self._peaks = rng.uniform(-5.0, 5.0, size=(k, n))
        self._peaks[0] = self.xopt
        # Heights w_i
        self._w = np.concatenate([[10.0], rng.uniform(1.1, 9.1, size=k - 1)])
        # Condition numbers (random)
        alpha = np.concatenate([[1000.0], 1000.0 ** rng.uniform(0, 1, size=k - 1)])
        # Rotation + scaling matrix per peak: C_i = R * diag(lam_i) * R^T
        self._C = []
        for i in range(k):
            perm = rng.permutation(n)
            lam = alpha[i] ** (np.arange(n, dtype=float) / max(n - 1, 1))
            lam = lam[perm]
            Ri = self._random_rotation(n, rng)
            self._C.append(Ri @ np.diag(lam) @ Ri.T)

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        best = -np.inf
        for i, (w, y, C) in enumerate(zip(self._w, self._peaks, self._C)):
            d = x - y
            val = w * np.exp(-1.0 / (2.0 * self.dim) * d @ C @ d)
            if val > best:
                best = val
        return float(self._t_osz(np.array([10.0 - best]))[0] ** 2 + self._f_pen(x))


class BBOB_F22_Gallagher21(_BBOBBase):
    """
    BBOB F22 – Gallagher's Gaussian 21-hi peaks function.
    Like F21 but with 21 peaks, the global peak considerably higher.
    """
    _fid = 22
    _N_PEAKS = 21

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        rng = np.random.RandomState(seed + 2000)
        n, k = self.dim, self._N_PEAKS
        self._peaks = rng.uniform(-5.0, 5.0, size=(k, n))
        self._peaks[0] = self.xopt
        self._w = np.concatenate([[10.0], rng.uniform(1.1, 9.1, size=k - 1)])
        alpha = np.concatenate([[1000.0], 1000.0 ** rng.uniform(0, 1, size=k - 1)])
        self._C = []
        for i in range(k):
            perm = rng.permutation(n)
            lam = alpha[i] ** (np.arange(n, dtype=float) / max(n - 1, 1))
            lam = lam[perm]
            Ri = self._random_rotation(n, rng)
            self._C.append(Ri @ np.diag(lam) @ Ri.T)

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        best = -np.inf
        for w, y, C in zip(self._w, self._peaks, self._C):
            d = x - y
            val = w * np.exp(-1.0 / (2.0 * self.dim) * d @ C @ d)
            if val > best:
                best = val
        return float(self._t_osz(np.array([10.0 - best]))[0] ** 2 + self._f_pen(x))


class BBOB_F23_Katsuura(_BBOBBase):
    """
    BBOB F23 – Katsuura function.
    Highly irregular, non-differentiable; tests resilience to fractal noise.
    """
    _fid = 23

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        z = self.Q @ (self._lam10 ** 0.5 * (self.R @ (x - self.xopt)))
        prod = 1.0
        for i, zi in enumerate(z):
            s = 0.0
            for j in range(1, 33):
                t = 2.0 ** j * zi
                s += abs(t - round(t)) / 2.0 ** j
            prod *= (1.0 + (i + 1) * s) ** (10.0 / n ** 1.2)
        val = 10.0 / n ** 2 * (prod - 1.0)
        return float(val + self._f_pen(x))


class BBOB_F24_LunacekBiRastrigin(_BBOBBase):
    """
    BBOB F24 – Lunacek bi-Rastrigin function.
    Two sphere basins of different depths combined with Rastrigin noise.
    Tests resistance to deceptive attraction.
    """
    _fid = 24

    def __init__(self, dim: int = 10, seed: int = 42):
        super().__init__(dim, seed)
        n = self.dim
        # mu_1 = 2.5, mu_2 from the standard formula
        self._mu1 = 2.5
        s = 1.0 - 1.0 / (2.0 * np.sqrt(n + 20.0) - 8.2)
        self._mu2 = -np.sqrt((self._mu1 ** 2 - 1.0) / s)
        # xopt restricted so that ||xopt|| is at first basin
        self.xopt = self._mu1 * np.sign(
            np.random.RandomState(seed).uniform(-1, 1, size=n)
        )

    def evaluate(self, solution):
        x = np.asarray(solution, dtype=float)
        n = self.dim
        x_hat = 2.0 * np.sign(self.xopt) * x
        z = self.R @ (x_hat - self._mu1)
        sphere1 = np.sum((x_hat - self._mu1) ** 2)
        sphere2 = n + np.sum((x_hat - self._mu2) ** 2)
        rastrigin = 10.0 * (n - np.sum(np.cos(2.0 * np.pi * z)))
        return float(min(sphere1, sphere2) + rastrigin + self._f_pen(x))
