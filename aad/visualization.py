"""
visualization.py
----------------
Plotting utilities for the AAD framework.

All plots use Matplotlib with a non-interactive (``Agg``) backend so they
work in headless / server environments.  Figures are saved to disk and the
file path is returned for easy integration into experiment runners.

Functions / Methods
-------------------
plot_fitness_curves      : convergence curves for multiple EA runs
plot_pareto_front        : 2-D Pareto front scatter for multi-objective
plot_meta_convergence    : meta-level best-performance over generations
plot_algorithm_comparison: bar chart comparing multiple configs
"""

import os

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import numpy as np


class Visualizer:
    """
    Save plots to *output_dir*.

    Parameters
    ----------
    output_dir : str, default ``"results"``
        Directory where figures are saved.  Created if it does not exist.
    """

    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _save(self, fig, filename: str) -> str:
        """Save *fig* and return the absolute file path."""
        fpath = os.path.join(self.output_dir, filename)
        fig.tight_layout()
        fig.savefig(fpath, dpi=150)
        plt.close(fig)
        print(f"  [Visualizer] saved -> {fpath}")
        return fpath

    # ------------------------------------------------------------------
    # Fitness convergence curves
    # ------------------------------------------------------------------

    def plot_fitness_curves(
        self,
        histories: list,
        title: str = "Fitness Convergence",
        filename: str = "fitness_curves.png",
    ) -> str:
        """
        Plot one convergence curve per run plus a thick mean curve.

        Parameters
        ----------
        histories : list of list[float]  – one history per run
        title     : str
        filename  : str  – saved under *output_dir*

        Returns
        -------
        str – absolute path to the saved figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        for i, hist in enumerate(histories):
            ax.plot(hist, alpha=0.45, linewidth=1.5, label=f"Run {i + 1}")

        if len(histories) > 1:
            max_len = max(len(h) for h in histories)
            padded = [h + [h[-1]] * (max_len - len(h)) for h in histories]
            mean_curve = np.mean(padded, axis=0)
            ax.plot(mean_curve, "k-", linewidth=2.5, label="Mean", zorder=10)

        ax.set_xlabel("Generation", fontsize=12)
        ax.set_ylabel("Best Fitness", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Log scale if all values are strictly positive
        all_vals = [v for h in histories for v in h]
        if all_vals and min(all_vals) > 0:
            ax.set_yscale("log")

        return self._save(fig, filename)

    # ------------------------------------------------------------------
    # Pareto front
    # ------------------------------------------------------------------

    def plot_pareto_front(
        self,
        fitnesses: list,
        title: str = "Pareto Front",
        filename: str = "pareto_front.png",
    ) -> str:
        """
        Scatter plot of a 2-D Pareto front.

        Parameters
        ----------
        fitnesses : list of [f1, f2]
        title     : str
        filename  : str

        Returns
        -------
        str – absolute path to the saved figure, or empty string if
              the data does not have exactly 2 objectives.
        """
        if not fitnesses or len(fitnesses[0]) < 2:
            print("[Visualizer] Pareto plot skipped: need 2-D objective vector.")
            return ""

        f1 = [f[0] for f in fitnesses]
        f2 = [f[1] for f in fitnesses]

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(f1, f2, c="steelblue", alpha=0.6, s=40, edgecolors="k",
                   linewidths=0.3)
        ax.set_xlabel("f₁", fontsize=12)
        ax.set_ylabel("f₂", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.grid(True, alpha=0.3)

        return self._save(fig, filename)

    # ------------------------------------------------------------------
    # Meta-learning convergence
    # ------------------------------------------------------------------

    def plot_meta_convergence(
        self,
        meta_convergence: list,
        title: str = "Meta-Learning Convergence",
        filename: str = "meta_convergence.png",
    ) -> str:
        """
        Plot best EA performance at each meta-generation.

        Parameters
        ----------
        meta_convergence : list[float]
        title            : str
        filename         : str

        Returns
        -------
        str – absolute path
        """
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(
            meta_convergence, "b-o", linewidth=2, markersize=6, label="Best EA perf."
        )
        ax.set_xlabel("Meta-Generation", fontsize=12)
        ax.set_ylabel("Best EA Performance (avg fitness)", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        return self._save(fig, filename)

    # ------------------------------------------------------------------
    # Algorithm comparison bar chart
    # ------------------------------------------------------------------

    def plot_algorithm_comparison(
        self,
        comparison_results: list,
        title: str = "Algorithm Comparison",
        filename: str = "algorithm_comparison.png",
    ) -> str:
        """
        Bar chart comparing multiple EA configurations by best fitness.

        Parameters
        ----------
        comparison_results : list of (config_dict, metrics_dict)
        title              : str
        filename           : str

        Returns
        -------
        str – absolute path
        """
        labels = [f"Config {i + 1}" for i in range(len(comparison_results))]
        best_fits = [r[1]["best_fitness"] for r in comparison_results]

        fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.2), 6))
        bars = ax.bar(labels, best_fits, color="steelblue", alpha=0.8,
                      edgecolor="k", linewidth=0.5)

        for bar, val in zip(bars, best_fits):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.4f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_ylabel("Best Fitness (lower = better)", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.grid(True, alpha=0.3, axis="y")
        plt.xticks(rotation=30, ha="right")

        return self._save(fig, filename)
