"""
surrogate_model.py
------------------
Surrogate model that predicts EA performance from a feature vector,
enabling the meta-learner to screen configurations cheaply before
committing to expensive real evaluations.

Two backends are supported:
  - ``"rf"``  : scikit-learn RandomForestRegressor  (default, robust)
  - ``"gp"``  : scikit-learn GaussianProcessRegressor (more principled
                uncertainty estimates, slower for large datasets)

Both backends benefit from input / output standardisation, which is
applied automatically.
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.preprocessing import StandardScaler


class SurrogateModel:
    """
    Surrogate regression model for EA performance prediction.

    Parameters
    ----------
    model_type : str, default ``"rf"``
        Backend: ``"rf"`` for Random Forest, ``"gp"`` for Gaussian Process.

    Attributes
    ----------
    is_fitted : bool
        True after at least one call to :meth:`fit`.
    """

    def __init__(self, model_type: str = "rf"):
        self.model_type = model_type
        self.is_fitted = False
        self._scaler_X = StandardScaler()
        self._scaler_y = StandardScaler()

        if model_type == "rf":
            self._model = RandomForestRegressor(
                n_estimators=50,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif model_type == "gp":
            kernel = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=2.5)
            self._model = GaussianProcessRegressor(
                kernel=kernel,
                n_restarts_optimizer=5,
                normalize_y=True,
            )
        else:
            raise ValueError(
                f"Unknown model_type '{model_type}'. Choose 'rf' or 'gp'."
            )

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, X, y) -> None:
        """
        Fit the surrogate on observed (feature_vector, performance) pairs.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
        y : array-like of shape (n_samples,)
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).reshape(-1, 1)

        X_s = self._scaler_X.fit_transform(X)
        y_s = self._scaler_y.fit_transform(y).ravel()

        self._model.fit(X_s, y_s)
        self.is_fitted = True

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, X) -> np.ndarray:
        """
        Predict performance for one or more feature vectors.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features) or (n_features,)

        Returns
        -------
        np.ndarray of shape (n_samples,)
        """
        if not self.is_fitted:
            raise RuntimeError("SurrogateModel has not been fitted yet.")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        X_s = self._scaler_X.transform(X)
        y_s = self._model.predict(X_s)
        return self._scaler_y.inverse_transform(y_s.reshape(-1, 1)).ravel()

    def predict_with_uncertainty(self, X):
        """
        Predict performance with uncertainty estimates.

        For the GP backend the posterior standard deviation is returned.
        For the RF backend the inter-tree variance is used as a proxy.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features) or (n_features,)

        Returns
        -------
        means : np.ndarray of shape (n_samples,)
        stds  : np.ndarray of shape (n_samples,)
        """
        if not self.is_fitted:
            raise RuntimeError("SurrogateModel has not been fitted yet.")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        X_s = self._scaler_X.transform(X)

        if self.model_type == "gp":
            y_mean_s, y_std_s = self._model.predict(X_s, return_std=True)
            # Invert scaling for mean only (std is in normalised space)
            y_mean = self._scaler_y.inverse_transform(
                y_mean_s.reshape(-1, 1)
            ).ravel()
            return y_mean, y_std_s

        # RF: use variance across estimators
        tree_preds = np.stack(
            [t.predict(X_s) for t in self._model.estimators_], axis=0
        )
        y_mean_s = tree_preds.mean(axis=0)
        y_std_s = tree_preds.std(axis=0)
        y_mean = self._scaler_y.inverse_transform(
            y_mean_s.reshape(-1, 1)
        ).ravel()
        return y_mean, y_std_s
