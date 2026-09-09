"""
chain_propagation.py - measurement-chain propagation for the 1762 nm refractometry campaign.

Implements a retrospective sensor-calibration hypothesis and propagates it CONSISTENTLY
through all three branches that share the environmental readings:

    (1) the Ciddor anchor used to derive n_1762 from the recorded fringe-count ratio,
    (2) the predictors used to fit the measured coefficients,
    (3) the Mathar predictions used for comparison.

Calibration hypothesis (explicit, per channel X in {T, H, P}), CENTRED on a stated pivot X0:

    X_read - X0 = g_X * (X_true - X0) + b_X   =>   X_true = X0 + (X_read - X0 - b_X)/g_X

IMPORTANT: changing the pivot while holding b = 0 changes the PHYSICAL hypothesis.
The uncentred form X_read = g*X_true is reproduced only with

    b_X = (g_X - 1) * X0            [see equivalent_uncentred()]

With b = 0 the centred form instead asserts the sensor is exact at X0. Both are legitimate
scenarios; they are not the same one. Assess a justified joint gain-offset envelope rather
than treating a single slice as the calibration bound.

The recorded fringe-count ratio R(t) is an INSTRUMENT OUTPUT and is held FIXED under
any retrospective calibration correction. Only the environmental coordinates change.

Derived index (measurement equation):

    n_1762(t) = K * n_Ciddor(T_g, H_g, P_g) / R(t),      K = f_780 / f_1762

Reporting conventions (both are provided, because they answer different questions):

  * coefficient differences  d_beta = beta_data - beta_mathar, fitted on the SAME
    corrected design matrix X_g.  NOTE: rescaling a humidity coordinate also rescales
    the slope's units, so d_beta values at different g are NOT directly comparable.
  * offset-removed residual  (n_data - n_mathar), constant removed.  This is expressed
    in refractive-index units and is INVARIANT to the humidity coordinate, so it
    distinguishes a real change in agreement from a change in slope scale.

Regression identity used for the analytical check:

    d_beta_g = (X_g^T X_g)^-1 X_g^T ( n_data,g - n_mathar,g )

i.e. the perturbation changes BOTH the residual vector and its regression onto the
environmental variables. A local Ciddor derivative alone cannot establish the
campaign-wide cancellation.
"""

from __future__ import annotations
import importlib.util
from dataclasses import dataclass
import numpy as np


# --------------------------------------------------------------------------- models

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Models:
    """Thin wrapper giving vectorised access to the repository's Ciddor and Mathar code."""

    def __init__(self, nist_path, mathar_path):
        self.C = _load(nist_path, "nist_ri")
        self.M = _load(mathar_path, "mathar")

    def ciddor(self, wave_nm, T_C, P_hPa, RH_pct):
        """Vectorised Ciddor. The repo's rh2mole_fraction is scalar-only, so xv is
        built element-wise and ciddor_ri (array-safe) does the heavy lifting."""
        T_C = np.asarray(T_C, float); P_hPa = np.asarray(P_hPa, float)
        RH_pct = np.asarray(RH_pct, float)
        P_Pa = P_hPa * 100.0
        xv = np.fromiter(
            (self.C.rh2mole_fraction(rh=float(r), p=float(p), t=float(t))
             for r, p, t in zip(np.ravel(RH_pct), np.ravel(P_Pa), np.ravel(T_C))),
            dtype=float, count=RH_pct.size,
        ).reshape(RH_pct.shape)
        return self.C.ciddor_ri(wave_nm, T_C, P_Pa, xv)

    def mathar(self, wave_um, T_C, P_hPa, RH_pct):
        return self.M.n(wave_um, np.asarray(T_C, float) + 273.15,
                        np.asarray(P_hPa, float) * 100.0, np.asarray(RH_pct, float))


# ---------------------------------------------------------------- calibration model

@dataclass(frozen=True)
class Calibration:
    """Gains are defined ABOUT A STATED REFERENCE POINT X0:

        X_read - X0 = g_X * (X_true - X0) + b_X
        =>  X_true  = X0 + (X_read - X0 - b_X) / g_X

    The reference point matters: a gain-only temperature scan about 0 depends on whether
    the coordinate is Celsius or kelvin, and a pressure gain about 0 couples a slope change
    to a large baseline correction. Defaults X0 are campaign-representative; set explicitly.
    Bounds on g and b must jointly respect the assumed calibration envelope."""
    g_T: float = 1.0; b_T: float = 0.0; T0: float = 25.0     # degC
    g_H: float = 1.0; b_H: float = 0.0; H0: float = 30.0     # %RH
    g_P: float = 1.0; b_P: float = 0.0; P0: float = 985.0    # hPa

    def apply(self, T_read, H_read, P_read):
        """Return the corrected ('true') coordinates implied by this hypothesis."""
        f = lambda X, X0, g, b: X0 + (np.asarray(X, float) - X0 - b) / g
        return (f(T_read, self.T0, self.g_T, self.b_T),
                f(H_read, self.H0, self.g_H, self.b_H),
                f(P_read, self.P0, self.g_P, self.b_P))

    def gain_of(self, channel):
        return {"T": self.g_T, "H": self.g_H, "P": self.g_P}[channel]


# ------------------------------------------------------------------------ machinery

def ols(y, T, H, P):
    """Design matrix [1, T, H, P]; returns beta and the design matrix."""
    X = np.column_stack([np.ones_like(T), T, H, P])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, X


def calibrate_K(models, T, H, P, R, n_1762, wave_780=780.24):
    """Recover K = f_780/f_1762 implied by the archived data and the Ciddor anchor."""
    n780 = models.ciddor(wave_780, T, P, H)
    return float(np.mean(n_1762 * R / n780)), n780


@dataclass
class ChainResult:
    calib: Calibration
    beta_data: np.ndarray
    beta_mathar: np.ndarray
    d_beta: np.ndarray                # slopes in the CORRECTED coordinate X_g
    d_beta_read: np.ndarray           # same slopes expressed against the ORIGINAL readings
    resid_offset_removed_rms: float   # RI units; invariant under reparameterisation,
                                      # but NOT under the physical calibration hypothesis
    fitted_H_term_rms: float          # RMS of the FITTED humidity term, |d_alpha_read|*std(H).
                                      # NOT a variance allocation: humidity correlates with the
                                      # other predictors, and the multiplier is fixed, so its
                                      # fractional change equals the coefficient's by construction.
    fitted_H_term_rms_perp: float     # same using std(H_perp), H residualised on (1, T, P)
    resid_offset: float
    n_used: int

    @property
    def d_alpha_H(self): return self.d_beta[2]
    @property
    def d_alpha_T(self): return self.d_beta[1]
    @property
    def d_alpha_P(self): return self.d_beta[3]
    @property
    def d_alpha_H_read(self): return self.d_beta_read[2]   # PRIMARY comparison across gains


def propagate(models, T_read, H_read, P_read, R, K,
              calib: Calibration | None = None,
              wave_780=780.24, wave_1762_um=1.762) -> ChainResult:
    """Propagate a calibration hypothesis through all three branches and refit.

    R is held fixed (instrument output). Both models are evaluated at the SAME
    corrected coordinates and fitted on the SAME design matrix.
    """
    calib = calib or Calibration()
    Tg, Hg, Pg = calib.apply(T_read, H_read, P_read)

    # branch 1: Ciddor anchor -> re-derived measurement
    n780_g = models.ciddor(wave_780, Tg, Pg, Hg)
    n_data_g = K * n780_g / R

    # branch 3: Mathar surrogate at the same corrected conditions
    n_math_g = models.mathar(wave_1762_um, Tg, Pg, Hg)

    # branch 2: predictors
    beta_d, X = ols(n_data_g, Tg, Hg, Pg)
    beta_m, _ = ols(n_math_g, Tg, Hg, Pg)

    resid = n_data_g - n_math_g
    off = float(np.mean(resid))
    d_beta = beta_d - beta_m

    # Slopes against the ORIGINAL readings: dn/dX_read = (dn/dX_g)*(dX_g/dX_read) = d_beta/g.
    # The INTERCEPT must be transformed too, or the returned vector mixes coordinates:
    #   dbeta0_read = dbeta0_g + sum_j dbeta_j,g * [ X0_j*(1 - 1/g_j) - b_j/g_j ]
    d_beta_read = d_beta.copy()
    pivots = {"T": (calib.T0, calib.g_T, calib.b_T),
              "H": (calib.H0, calib.g_H, calib.b_H),
              "P": (calib.P0, calib.g_P, calib.b_P)}
    shift = 0.0
    for k, ch in ((1, "T"), (2, "H"), (3, "P")):
        X0, g, b = pivots[ch]
        d_beta_read[k] = d_beta[k] / g
        shift += d_beta[k] * (X0 * (1.0 - 1.0 / g) - b / g)
    d_beta_read[0] = d_beta[0] + shift

    # RMS of the fitted humidity term (NOT an independent error contribution - see ChainResult).
    H_read = np.asarray(H_read, float)
    T_read = np.asarray(T_read, float); P_read = np.asarray(P_read, float)
    Xc = np.column_stack([np.ones_like(T_read), T_read, P_read])
    H_perp = H_read - Xc @ np.linalg.lstsq(Xc, H_read, rcond=None)[0]
    fH = float(abs(d_beta_read[2]) * np.std(H_read))
    fHp = float(abs(d_beta_read[2]) * np.std(H_perp))

    return ChainResult(calib, beta_d, beta_m, d_beta, d_beta_read,
                       float(np.std(resid - off)), fH, fHp, off, len(R))


def equivalent_uncentred(g, X0):
    """Offset b that makes the CENTRED hypothesis reproduce the uncentred X_read = g*X_true.
    Use this whenever an existing (uncentred) hypothesis is being reproduced under a pivot."""
    return (g - 1.0) * X0


def d_beta_identity(models, T_read, H_read, P_read, R, K, calib, **kw):
    """Direct evaluation of d_beta = (Xg^T Xg)^-1 Xg^T (n_data,g - n_mathar,g).
    Should agree with propagate() to numerical precision; used as an analytical check."""
    calib = calib or Calibration()
    Tg, Hg, Pg = calib.apply(T_read, H_read, P_read)
    n_data_g = K * models.ciddor(kw.get("wave_780", 780.24), Tg, Pg, Hg) / R
    n_math_g = models.mathar(kw.get("wave_1762_um", 1.762), Tg, Pg, Hg)
    X = np.column_stack([np.ones_like(Tg), Tg, Hg, Pg])
    # lstsq rather than the normal equations: better conditioning.
    # NOTE: this checks ALGEBRAIC consistency only. It does not validate the calibration
    # convention, the model units, or the physics.
    return np.linalg.lstsq(X, n_data_g - n_math_g, rcond=None)[0]


def single_branch_estimate(alpha_H, g):
    """The SM's current treatment: rescale ONLY the fitted data coefficient.
    Refitting against H/g gives alpha_new = g*alpha_old, so the change is
    alpha_old*(g-1). Provided for comparison ONLY - it omits branches 1 and 3."""
    return alpha_H * (g - 1.0)


def gain_scan(models, T, H, P, R, K, gains, channel="H", uncentred=False):
    """Full propagation across a range of gains for one channel.

    uncentred=True reproduces X_read = g*X_true by setting b = (g-1)*X0. With the default
    (False) the scan instead assumes the sensor is exact at the pivot X0 - a DIFFERENT
    physical hypothesis. Report the two separately."""
    rows = []
    idx = {"T": 1, "H": 2, "P": 3}[channel]
    base = propagate(models, T, H, P, R, K)
    for g in gains:
        kw = {f"g_{channel}": float(g)}
        if uncentred:
            X0 = {"T": Calibration().T0, "H": Calibration().H0, "P": Calibration().P0}[channel]
            kw[f"b_{channel}"] = equivalent_uncentred(float(g), X0)
        r = propagate(models, T, H, P, R, K, Calibration(**kw))
        rows.append(dict(
            g=float(g),
            # PRIMARY: common (read) coordinate, comparable across gain hypotheses
            d_alpha_read=r.d_beta_read[idx],
            d_alpha_read_shift=r.d_beta_read[idx] - base.d_beta_read[idx],
            # corrected-coordinate value, NOT comparable across g (units rescale)
            d_alpha_corrected=r.d_beta[idx],
            # single-branch comparison for the SCANNED channel only
            single_branch=single_branch_estimate(base.beta_data[idx], g),
            resid_rms=r.resid_offset_removed_rms,
            fitted_H_rms=r.fitted_H_term_rms,
            fitted_H_rms_perp=r.fitted_H_term_rms_perp,
            resid_offset=r.resid_offset,
        ))
    return base, rows
