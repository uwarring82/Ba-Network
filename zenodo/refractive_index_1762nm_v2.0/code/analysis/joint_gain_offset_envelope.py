#!/usr/bin/env python3
"""Step 6 - joint gain-offset envelope (NS10657, Task 7).

Why this exists
---------------
Table S1b of the SM quotes an "endpoint" gain sensitivity obtained by rescaling ONLY the
fitted coefficient (`single_branch_estimate`: alpha_X * (g_X - 1)).  Task 7 requires the
calibration hypothesis to be propagated CONSISTENTLY through the three branches that share
the environmental readings (Ciddor anchor, regression predictors, Mathar comparison), and
the systematic to be assessed over a JUSTIFIED JOINT (g, b) envelope instead of a single
one-dimensional slice.

Feasible envelope
-----------------
For channel X, centred on the pivot X0,

    X_read - X0 = g_X (X_true - X0) + b_X        e_X(X) = (g_X - 1)(X - X0) + b_X

The BME280 accuracy bound |e_X| <= delta_X over the campaign range [X_min, X_max] defines a
parallelogram in (g, b).  Its vertices, in hull order, are

    (1, +delta)                                            (1, -delta)
    (1 - gamma_max, +delta + gamma_max * (X_min - X0))
    (1 + gamma_max, +delta - gamma_max * (X_max - X0))

with gamma_max = 2 delta_X / span.  That worst-case gain deviation reproduces the SM
numbers exactly (H 30.3 %, T 11.7 %, P 4.7 %), so the envelope ASSUMPTION is unchanged --
only the propagation is.  The uncentred hypothesis X_read = g X_true, i.e.
b = (g - 1) X0, is NOT inside this envelope for the quoted endpoint gains; it is evaluated
below only as a reference.

What is reported
----------------
For every evaluated calibration theta = (g_T,b_T,g_H,b_H,g_P,b_P) the script records the
slope difference in the COMMON (read) coordinate, d_beta_read, so numbers are comparable
across gain hypotheses.  The headline quantity is

    delta_H(theta) = d_alpha_H_read(theta) - d_alpha_H_read(baseline)

and analogously for T and P.  Three envelopes are given per response channel:

  * E_vertices   max |delta| over the 4^3 = 64 joint vertices (corner evaluation);
  * E_sampled    max |delta| over every evaluated point (vertices + edges + random +
                 local refinement);
  * E_linearised first-order estimate from the baseline Jacobian (central differences)
                 over the bounding box of the parallelogram.  This is NOT guaranteed to
                 bound the maximum; report it as a linearity check.  If it falls below
                 E_sampled the response is non-linear and E_sampled is the number to
                 quote.

E_vertices and E_sampled use only points inside the feasible envelope.  The SM-style
uncentred / centred-at-pivot slices are evaluated separately as reference rows because they
leave the envelope at the quoted endpoint gains.

Usage
-----
    python3 joint_gain_offset_envelope.py                    # production (full resolution)
    python3 joint_gain_offset_envelope.py --quick            # coarse calibration set
    python3 joint_gain_offset_envelope.py --quick --subsample 20   # ~1 min smoke test
    python3 joint_gain_offset_envelope.py --u-comb 1.32e-9   # also report delta / u_comb

Paths are resolved relative to THIS FILE, so the script can be run from any directory.
Use --data / --models / --out to override.

Outputs
-------
    joint_gain_offset_envelope.json           summary + envelope + attained calibrations
    joint_gain_offset_envelope_samples.csv    every evaluated calibration
    joint_gain_offset_envelope.md             human-readable report (tables)

Dependencies: numpy, pandas, and whatever chain_propagation's models import (the bundled
Mathar module imports matplotlib at module level, so matplotlib must be importable).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent
REPO_DIR = CODE_DIR.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from chain_propagation import (  # noqa: E402
    Calibration,
    Models,
    calibrate_K,
    d_beta_identity,
    propagate,
)

DEFAULT_MODELS_DIR = CODE_DIR / 'models'
DEFAULT_DATA = REPO_DIR / 'data' / 'processed' / 'full_data.csv'
DEFAULT_OUT = HERE / 'joint_gain_offset_envelope.json'

# Full-resolution archived values (read coordinate), used as a self-check.
ARCHIVED_DALPHA_H = 4.3334e-09
ARCHIVED_RESID_RMS = 1.9304e-07

COLUMN = {'T': 'temperature', 'H': 'humidity', 'P': 'pressure'}
IDX = {'T': 1, 'H': 2, 'P': 3}                 # position in d_beta_read
CHANNELS = ('T', 'H', 'P')
DELTA = {'T': 1.0, 'H': 4.0, 'P': 1.0}         # BME280 accuracy bounds: degC, %RH, hPa
PIVOT = {'T': 25.0, 'H': 30.0, 'P': 985.0}     # must match Calibration defaults

# kinds that live INSIDE the feasible envelope; the reference slices do not
FEASIBLE_PREFIXES = ('vertex', 'edge_', 'random', 'refine_', 'channel_only_')
REFERENCE_PREFIXES = ('uncentred_endpoint', 'centred_b0_endpoint', 'feasible_endpoint')

assert (PIVOT['T'], PIVOT['H'], PIVOT['P']) == (
    Calibration().T0, Calibration().H0, Calibration().P0), \
    'PIVOT must match the Calibration defaults used by the toolset'


# --------------------------------------------------------------------- envelope

class Envelope:
    """Feasible (g, b) parallelogram for one channel: |(g-1)(X-X0) + b| <= delta."""

    def __init__(self, name, xmin, xmax, delta, x0):
        self.name = name
        self.delta = float(delta)
        self.x0 = float(x0)
        self.xmin, self.xmax = float(xmin), float(xmax)
        self.dmin = self.xmin - self.x0
        self.dmax = self.xmax - self.x0
        self.span = self.xmax - self.xmin
        self.gamma_max = 2.0 * self.delta / self.span

    def vertices(self):
        d, gm = self.delta, self.gamma_max
        return [(1.0, +d),
                (1.0 - gm, +d + gm * self.dmin),
                (1.0, -d),
                (1.0 + gm, +d - gm * self.dmax)]

    def b_bounds(self, g):
        gm = g - 1.0
        if abs(gm) > self.gamma_max + 1e-12:
            return None
        lo = max(-self.delta - gm * self.dmin, -self.delta - gm * self.dmax)
        hi = min(+self.delta - gm * self.dmin, +self.delta - gm * self.dmax)
        return lo, hi

    def clip(self, g, b):
        g = float(np.clip(g, 1.0 - self.gamma_max, 1.0 + self.gamma_max))
        lo, hi = self.b_bounds(g)
        return g, float(np.clip(b, lo, hi))

    def edge_samples(self, n_per_edge):
        """Interior points on the four edges (vertices excluded)."""
        V = self.vertices()
        pts = []
        for (g1, b1), (g2, b2) in zip(V, V[1:] + V[:1]):
            for t in np.linspace(0.0, 1.0, n_per_edge + 2)[1:-1]:
                pts.append(self.clip(g1 + t * (g2 - g1), b1 + t * (b2 - b1)))
        return pts

    def max_abs_b(self):
        """max |b| over the parallelogram (used as the first-order bound on b)."""
        return max(abs(b) for _, b in self.vertices())

    def max_gain_at_zero_offset(self):
        """Largest |g-1| for which b = 0 is still inside the envelope."""
        return self.delta / max(abs(self.dmin), abs(self.dmax))

    def describe(self):
        return (f'range [{self.xmin:.4f}, {self.xmax:.4f}] span {self.span:.4f} '
                f'gamma_max {self.gamma_max:+.5f} (g_max {1 + self.gamma_max:.4f}) '
                f'|b|_max {self.max_abs_b():.4f} '
                f'b at g_max {self.vertices()[3][1]:+.4f}')


# ------------------------------------------------------------------- evaluation

def make_calib(theta, pivots=None):
    pivots = pivots or {}
    return Calibration(
        g_T=theta['T'][0], b_T=theta['T'][1], T0=pivots.get('T', PIVOT['T']),
        g_H=theta['H'][0], b_H=theta['H'][1], H0=pivots.get('H', PIVOT['H']),
        g_P=theta['P'][0], b_P=theta['P'][1], P0=pivots.get('P', PIVOT['P']),
    )


def evaluate(models, T, H, P, R, K, base_read, kind, theta, pivots=None):
    r = propagate(models, T, H, P, R, K, make_calib(theta, pivots))
    row = {'kind': kind,
           'resid_rms': float(r.resid_offset_removed_rms),
           'resid_offset': float(r.resid_offset)}
    for ch in CHANNELS:
        row[f'g_{ch}'] = theta[ch][0]
        row[f'b_{ch}'] = theta[ch][1]
        val = float(r.d_beta_read[IDX[ch]])
        row[f'd_alpha_{ch}_read'] = val
        row[f'delta_{ch}'] = val - base_read[ch]
    return row


def perturb(env, g0, b0, scale, rng):
    g = float(np.clip(g0 + scale * env.gamma_max * rng.normal(),
                      1.0 - env.gamma_max, 1.0 + env.gamma_max))
    lo, hi = env.b_bounds(g)
    b = float(np.clip(b0 + scale * (hi - lo) * rng.normal(), lo, hi))
    return g, b


def linearised_jacobian(models, T, H, P, R, K, base_read, env, frac=0.05):
    """Central-difference sensitivities d delta_resp / d (g_c, b_c) at the baseline."""
    J = {}
    for c in CHANNELS:
        e = env[c]
        steps = {'g': frac * e.gamma_max, 'b': frac * e.delta}
        J[c] = {}
        for pname, step in steps.items():
            vals = {}
            for sgn in (+1.0, -1.0):
                theta = {x: (1.0, 0.0) for x in CHANNELS}
                g, b = 1.0, 0.0
                if pname == 'g':
                    g += sgn * step
                else:
                    b += sgn * step
                theta[c] = (g, b)
                row = evaluate(models, T, H, P, R, K, base_read, 'jacobian', theta)
                vals[sgn] = {r: row[f'delta_{r}'] for r in CHANNELS}
            J[c][pname] = {r: (vals[+1.0][r] - vals[-1.0][r]) / (2.0 * step)
                           for r in CHANNELS}
    return J


# ----------------------------------------------------------------------- report

def _f(x, spec='+.4e'):
    if x is None:
        return 'n/a'
    try:
        return format(float(x), spec)
    except (TypeError, ValueError):
        return str(x)


def _ratio(x, spec='.2f'):
    return 'n/a' if x is None else format(float(x), spec)


def write_report(path, summary):
    m = summary['meta']
    L = []
    L.append('# Step 6 - joint gain-offset envelope')
    L.append('')
    L.append(f"- generated: {m['timestamp']}")
    L.append(f"- rows: {m['rows']} (subsample={m['subsample']}, quick={m['quick']})")
    L.append(f"- evaluations: {m['evaluations']}, seed: {m['seed']}, "
             f"elapsed: {m['elapsed_s']} s")
    L.append('')

    L.append('## 1. Envelope assumption (unchanged, restated)')
    L.append('')
    L.append('| ch | range | span | gamma_max | g_max | |b|_max | b at g_max | '
             'uncentred b at g_max | uncentred / spec |')
    L.append('|---|---|---|---|---|---|---|---|---|')
    for ch in CHANNELS:
        e = summary['envelope'][ch]
        L.append(f"| {ch} | [{e['min']:.4f}, {e['max']:.4f}] | {e['span']:.4f} | "
                 f"{e['gamma_max']:+.5f} | {e['g_max']:.4f} | {e['max_abs_b']:.4f} | "
                 f"{e['b_at_g_max']:+.4f} | {e['uncentred_b_at_g_max']:+.4f} | "
                 f"{e['uncentred_exceeds_spec_by']:.2f}x |")
    L.append('')
    L.append('gamma_max = 2*delta/span reproduces the SM endpoint gains exactly, so the '
             'envelope assumption is unchanged; only the propagation is. The uncentred '
             'hypothesis b = (g-1)*X0 exceeds the stated sensor specification and is kept '
             'only as a reference.')
    L.append('')

    L.append('## 2. Baseline (g = 1, b = 0)')
    L.append('')
    L.append('| ch | d_alpha_read | alpha_data (corrected coord.) |')
    L.append('|---|---|---|')
    for ch in CHANNELS:
        L.append(f"| {ch} | {_f(summary['baseline']['d_alpha_read'][ch])} | "
                 f"{_f(summary['baseline']['alpha_data'][ch])} |")
    L.append('')
    L.append(f"- offset-removed residual RMS: "
             f"{_f(summary['baseline']['resid_rms'])} (RI units)")
    sc = summary.get('self_check') or {}
    if sc:
        if sc.get('archived_checked'):
            L.append(f"- self-check vs archived full-resolution value "
                     f"({_f(ARCHIVED_DALPHA_H)}): "
                     f"rel. deviation {_f(sc.get('d_alpha_H_rel_dev'), '.2e')} "
                     f"[{'PASS' if sc.get('d_alpha_H_ok') else 'CHECK'}]")
        else:
            L.append('- self-check vs archived full-resolution value: skipped '
                     '(subsample != 1)')
        L.append(f"- max |identity - propagate|: "
                 f"{_f(sc.get('identity_max_abs'), '.2e')}")
    L.append('')

    L.append('## 3. Worst case over the joint envelope')
    L.append('')
    L.append('| response | interval over envelope | E (64 joint vertices) | '
             'E (all sampled) | E (linearised) | E/sqrt(3) | SM single-branch | SM / consistent |')
    L.append('|---|---|---|---|---|---|---|---|')
    for ch in CHANNELS:
        w = summary['worst_case'][ch]
        L.append(f"| d_alpha_{ch} | [{_f(w['delta_min'])}, {_f(w['delta_max'])}] | "
                 f"{_f(w['E_vertices'])} | {_f(w['E_sampled'])} | "
                 f"{_f(w['E_linearised'])} | {_f(w['u_syst_rectangular'])} | "
                 f"{_f(w['sm_single_branch'])} | "
                 f"{_ratio(w['sm_over_consistent'])}x |")
    L.append('')
    L.append('E is the half-width of the attained interval for the read-coordinate slope '
             'difference. E_vertices is a pure corner evaluation; E_sampled adds edges, '
             'random interior draws and local refinement; E_linearised is a first-order '
             'estimate from the baseline Jacobian over the bounding box of the '
             'parallelogram. E_linearised is NOT guaranteed to bound the maximum: if it '
             'falls below E_sampled the response is non-linear and E_sampled is the '
             'number to quote. E_vertices and E_sampled use only points INSIDE the '
             'feasible envelope; the reference slices below are outside it.')
    L.append('')

    L.append('')
    L.append('### 3b. Channel-resolved contributions (own-channel vertices, others at '
             'identity)')
    L.append('')
    L.append('| response | T-only | H-only | P-only | sum (triangle) | joint max | '
             'SM endpoint |')
    L.append('|---|---|---|---|---|---|---|')
    for ch in CHANNELS:
        co = summary['channel_only']
        parts = [co[c][ch] for c in CHANNELS]
        L.append(f"| d_alpha_{ch} | {_f(parts[0])} | {_f(parts[1])} | {_f(parts[2])} | "
                 f"{_f(sum(parts))} | {_f(summary['worst_case'][ch]['E_sampled'])} | "
                 f"{_f(summary['worst_case'][ch]['sm_single_branch'])} |")
    L.append('')
    L.append('The SM endpoint rescales only the coefficient of the SAME channel. Here the '
             'H-only column is the directly comparable consistent-propagated number; the '
             'joint maximum is larger because temperature and pressure gain errors also '
             'move the humidity coefficient through the shared Ciddor anchor. For a linear '
             'response the triangle sum would bound the joint maximum; where the joint '
             'maximum exceeds that sum the response is non-linear, consistent with '
             'E_linearised falling below E_sampled.')
    L.append('')

    L.append('## 4. Attained worst-case calibrations')
    L.append('')
    L.append('| response | kind | g_T | b_T | g_H | b_H | g_P | b_P | delta | resid RMS |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    for ch in CHANNELS:
        w = summary['worst_case'][ch]
        a = w['attained_calibration']
        L.append(f"| d_alpha_{ch} | {w['attained_kind']} | {a['g_T']:.5f} | "
                 f"{a['b_T']:+.4f} | {a['g_H']:.5f} | {a['b_H']:+.4f} | "
                 f"{a['g_P']:.5f} | {a['b_P']:+.4f} | {_f(w['attained_delta'])} | "
                 f"{_f(w['resid_rms_at_max'])} |")
    L.append('')

    L.append('## 5. Reference slices (gain-only hypotheses at the endpoint gain)')
    L.append('')
    L.append('These are NOT part of the feasible envelope; they reproduce the SM-style '
             'gain-only hypotheses for comparison. `uncentred_endpoint` sets '
             'b = (g-1)*X0 and exceeds the sensor specification; `centred_b0_endpoint` '
             'assumes exactness at the pivot and also leaves the envelope at g_max for H '
             'and T; `feasible_endpoint` is the actual envelope vertex.')
    L.append('')
    L.append('| slice | channel | g | b | delta | resid RMS |')
    L.append('|---|---|---|---|---|---|')
    for s in summary['reference_slices']:
        L.append(f"| {s['kind']} | {s['channel']} | {s['g']:.5f} | {s['b']:+.4f} | "
                 f"{_f(s['delta'])} | {_f(s['resid_rms'])} |")
    L.append('')

    pc = summary.get('pivot_recentring')
    if pc:
        L.append('## 6. Pivot re-centring invariance')
        L.append('')
        L.append('Re-centring the same physical hypothesis on a different pivot (X0 = 0) '
                 'must not change any output; max abs deviations:')
        L.append('')
        for k, v in pc.items():
            L.append(f"- {k}: {_f(v, '.2e')}")
        L.append('')

    sig = summary.get('significance_H')
    if sig:
        L.append('## 7. Significance of Delta alpha_H with the revised systematic')
        L.append('')
        L.append(f"- Delta alpha_H = {_f(sig['d_alpha_H'])}")
        L.append(f"- u_stat (paired bootstrap, from the SM) = {_f(sig['u_stat'])}")
        L.append(f"- SM u_syst (H) = {_f(sig['sm_u_syst'])} -> u_comb = "
                 f"{_f(sig['sm_u_comb'])} -> {sig['sm_significance']:.2f} u_comb")
        L.append(f"- consistent joint envelope u_syst = {_f(sig['revised_u_syst'])} "
                 f"(E/sqrt3) -> u_comb = {_f(sig['revised_u_comb'])} -> "
                 f"{sig['revised_significance']:.2f} u_comb")
        L.append('')
        L.append('The revised systematic uses the joint envelope half-width divided by '
                 'sqrt(3); the statistical term is unchanged. This quantifies the '
                 'significance statement, it does not by itself establish a physical '
                 'effect: the limiting constraints (time dependence, Mathar domain '
                 'coverage) still have to be carried explicitly.')
        L.append('')

    L.append('## 8. Reading')
    L.append('')
    L.append('- The envelope assumption is unchanged from the SM; only the propagation '
             'through the three branches is made consistent.')
    L.append('- E_sampled and E_linearised should be compared before quoting a bound: if the '
             'linearised estimate is at or above the sampled maximum the sampling is '
             'adequate; if it is below, the response is non-linear and the sampled '
             'maximum is the number to quote.')
    L.append('- A bound small compared with the other budget terms supports the statement '
             '"gain is not the limiting systematic", NOT the existence of a physical '
             'effect. Carry the limiting constraints (time dependence, Mathar domain '
             'coverage) explicitly.')
    L.append('')

    Path(path).write_text('\n'.join(L), encoding='utf-8')


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description='Step 6 - joint gain-offset envelope for the 1762 nm calibration chain.')
    ap.add_argument('--subsample', type=int, default=1,
                    help='use every Nth row (default 1 = full resolution)')
    ap.add_argument('--quick', action='store_true', help='coarse calibration set')
    ap.add_argument('--edge', type=int, default=None, help='interior points per edge')
    ap.add_argument('--random', type=int, default=None, help='random joint draws')
    ap.add_argument('--refine', type=int, default=None,
                    help='local draws per best point per channel')
    ap.add_argument('--no-linear-bound', action='store_true',
                    help='skip the first-order Jacobian bound')
    ap.add_argument('--u-comb', type=float, default=None,
                    help='combined standard uncertainty, to also report delta/u_comb')
    ap.add_argument('--u-stat', type=float, default=None,
                    help='paired-bootstrap SE of the H difference (SM: 1.30e-9); when '
                         'given, the revised significance of Delta alpha_H is reported')
    ap.add_argument('--sm-u-syst', type=float, default=2.30e-9,
                    help='SM systematic uncertainty for the H coefficient (default 2.30e-9)')
    ap.add_argument('--data', default=str(DEFAULT_DATA))
    ap.add_argument('--models', default=str(DEFAULT_MODELS_DIR))
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    n_edge = args.edge if args.edge is not None else (2 if args.quick else 5)
    n_rand = args.random if args.random is not None else (0 if args.quick else 80)
    n_refine = args.refine if args.refine is not None else (0 if args.quick else 6)

    # ---------------------------------------------------------------- data
    data_path = Path(args.data)
    models_dir = Path(args.models)
    out_path = Path(args.out)
    print(f'data   : {data_path}')
    print(f'models : {models_dir}')
    if not data_path.is_file():
        sys.exit(f'ERROR: data file not found: {data_path}')
    if not (models_dir / 'nist' / 'refractive_index.py').is_file():
        sys.exit(f'ERROR: NIST model not found under {models_dir}')

    models = Models(str(models_dir / 'nist' / 'refractive_index.py'),
                    str(models_dir / 'mathar' / 'Mathar2007.py'))
    df = pd.read_csv(data_path)
    d = df.iloc[::args.subsample]
    T, H, P, R, y = (d.temperature.values, d.humidity.values, d.pressure.values,
                     d.counts_ratio.values, d.n_1762.values)
    print(f'rows: {len(d)} of {len(df)} (subsample={args.subsample})')

    # ------------------------------------------------------------ baseline
    t_start = time.time()
    K, _ = calibrate_K(models, T, H, P, R, y)
    base = propagate(models, T, H, P, R, K)
    base_read = {ch: float(base.d_beta_read[IDX[ch]]) for ch in CHANNELS}
    base_alpha = {ch: float(base.beta_data[IDX[ch]]) for ch in CHANNELS}
    print('baseline d_alpha_read: ' +
          '  '.join(f'{ch}={base_read[ch]:+.4e}' for ch in CHANNELS))
    print('baseline alpha_data:   ' +
          '  '.join(f'{ch}={base_alpha[ch]:+.4e}' for ch in CHANNELS))

    # ------------------------------------------------------- self-checks
    ident = d_beta_identity(models, T, H, P, R, K, Calibration())
    identity_max = float(np.abs(ident - base.d_beta).max())
    rel_dev = abs(base_read['H'] - ARCHIVED_DALPHA_H) / abs(ARCHIVED_DALPHA_H)
    self_check = {'identity_max_abs': identity_max,
                  'archived_checked': bool(args.subsample == 1),
                  'd_alpha_H_rel_dev': float(rel_dev),
                  'd_alpha_H_ok': bool(args.subsample == 1 and rel_dev < 1e-4),
                  'archived_d_alpha_H': ARCHIVED_DALPHA_H,
                  'archived_resid_rms': ARCHIVED_RESID_RMS,
                  'resid_rms_rel_dev': float(
                      abs(base.resid_offset_removed_rms - ARCHIVED_RESID_RMS)
                      / ARCHIVED_RESID_RMS)}
    print(f'self-check: max |identity - propagate| = {identity_max:.3e}')
    if args.subsample == 1:
        flag = 'PASS' if self_check['d_alpha_H_ok'] else 'CHECK'
        print(f'self-check: d_alpha_H(read) vs archived {ARCHIVED_DALPHA_H:+.4e} '
              f'-> rel. dev {rel_dev:.2e}  [{flag}]')
        if not self_check['d_alpha_H_ok']:
            print('  WARNING: full-resolution baseline does not reproduce the archived '
                  'value - check the data file and the toolset version before quoting.')
    else:
        print('self-check: archived comparison skipped (subsample != 1)')

    # ------------------------------------------------------------- envelope
    env = {ch: Envelope(ch, d[COLUMN[ch]].min(), d[COLUMN[ch]].max(),
                        DELTA[ch], PIVOT[ch]) for ch in CHANNELS}
    for ch in CHANNELS:
        print(f'{ch}: {env[ch].describe()}')

    # ------------------------------------------------------------- plan
    n_vertices = 4 ** len(CHANNELS)
    n_channel_only = 4 * len(CHANNELS)
    n_edges = sum(len(env[ch].edge_samples(n_edge)) for ch in CHANNELS)
    n_refs = 3 * len(CHANNELS)
    n_refine_total = 3 * 3 * n_refine if n_refine else 0
    n_jac = 0 if args.no_linear_bound else 4 * len(CHANNELS)
    n_plan = (n_vertices + n_channel_only + n_edges + n_rand + n_refs
              + n_refine_total + n_jac + 2)
    print(f'\nplanned evaluations: {n_plan} '
          f'(joint vertices {n_vertices}, channel-only {n_channel_only}, '
          f'edges {n_edges}, random {n_rand}, '
          f'reference {n_refs}, refine {n_refine_total}, jacobian {n_jac}, pivot 2)')

    # ------------------------------------------------- first-order bound
    linear_bound = None
    if not args.no_linear_bound:
        print('first-order Jacobian at the baseline ...', flush=True)
        J = linearised_jacobian(models, T, H, P, R, K, base_read, env)
        bmax = {ch: env[ch].max_abs_b() for ch in CHANNELS}
        linear_bound = {
            resp: float(sum(
                abs(J[c]['g'][resp]) * env[c].gamma_max + abs(J[c]['b'][resp]) * bmax[c]
                for c in CHANNELS))
            for resp in CHANNELS}
        jacobian = {c: {p: {r: J[c][p][r] for r in CHANNELS} for p in ('g', 'b')}
                    for c in CHANNELS}
        print('first-order (linearised) estimate: ' +
              '  '.join(f'{r}={linear_bound[r]:.4e}' for r in CHANNELS))
    else:
        jacobian = None

    # ------------------------------------------------------ sample the set
    thetas = []   # (kind, theta)

    for combo in product(*[env[ch].vertices() for ch in CHANNELS]):
        thetas.append(('vertex', dict(zip(CHANNELS, combo))))

    # one channel at a time: its four vertices, the others at the identity calibration
    for ch in CHANNELS:
        for g, b in env[ch].vertices():
            theta = {c: (1.0, 0.0) for c in CHANNELS}
            theta[ch] = (g, b)
            thetas.append((f'channel_only_{ch}', theta))

    for ch in CHANNELS:
        for g, b in env[ch].edge_samples(n_edge):
            theta = {c: (1.0, 0.0) for c in CHANNELS}
            theta[ch] = (g, b)
            thetas.append((f'edge_{ch}', theta))

    # Uniform on the parallelogram: for each m = g-1 the b-slice has constant width
    # 2*delta, so uniform(m) x uniform(b | m) is exactly uniform on the set.
    for _ in range(n_rand):
        theta = {}
        for ch in CHANNELS:
            e = env[ch]
            g = rng.uniform(1.0 - e.gamma_max, 1.0 + e.gamma_max)
            lo, hi = e.b_bounds(g)
            theta[ch] = (g, rng.uniform(lo, hi))
        thetas.append(('random', theta))

    # reference slices: SM endpoint hypotheses (gain-only), one channel at a time
    for ch in CHANNELS:
        e = env[ch]
        gmax = 1.0 + e.gamma_max
        for label, b in (('uncentred_endpoint', (gmax - 1.0) * e.x0),
                         ('centred_b0_endpoint', 0.0),
                         ('feasible_endpoint', e.vertices()[3][1])):
            theta = {c: (1.0, 0.0) for c in CHANNELS}
            theta[ch] = (gmax, b)
            thetas.append((f'{label}_{ch}', theta))

    print(f'\nevaluating {len(thetas)} calibrations ...', flush=True)
    rows, t0 = [], time.time()
    for i, (kind, theta) in enumerate(thetas):
        rows.append(evaluate(models, T, H, P, R, K, base_read, kind, theta))
        if i == 0:
            dt = time.time() - t0
            print(f'  first evaluation {dt:.2f} s -> '
                  f'ETA {dt * len(thetas) / 60.0:.1f} min for the sweep', flush=True)
        if (i + 1) % 25 == 0 or (i + 1) == len(thetas):
            print(f'  {i + 1}/{len(thetas)}  {time.time() - t0:.1f}s', flush=True)

    tbl = pd.DataFrame(rows)
    feas = tbl[tbl['kind'].str.startswith(FEASIBLE_PREFIXES)]

    # --------------------------------------------------- local refinement
    if n_refine:
        extra = []
        for ch in CHANNELS:
            col = f'delta_{ch}'
            best = feas.reindex(feas[col].abs().sort_values(ascending=False).index[:3])
            for _, r in best.iterrows():
                for _ in range(n_refine):
                    theta = {}
                    for c in CHANNELS:
                        theta[c] = perturb(env[c], r[f'g_{c}'], r[f'b_{c}'], 0.25, rng)
                    extra.append((f'refine_{ch}', theta))
        print(f'\nrefining with {len(extra)} local draws ...', flush=True)
        for i, (kind, theta) in enumerate(extra):
            rows.append(evaluate(models, T, H, P, R, K, base_read, kind, theta))
            if (i + 1) % 25 == 0 or (i + 1) == len(extra):
                print(f'  {i + 1}/{len(extra)}  {time.time() - t0:.1f}s', flush=True)
        tbl = pd.DataFrame(rows)
        feas = tbl[tbl['kind'].str.startswith(FEASIBLE_PREFIXES)]

    # ------------------------------------------------- pivot consistency
    r0 = feas.loc[feas['delta_H'].abs().idxmax()]
    theta_a = {ch: (float(r0[f'g_{ch}']), float(r0[f'b_{ch}'])) for ch in CHANNELS}
    zero_pivot = {'T': 0.0, 'H': 0.0, 'P': 0.0}
    theta_b = {ch: (theta_a[ch][0],
                    theta_a[ch][1] + (theta_a[ch][0] - 1.0)
                    * (zero_pivot[ch] - PIVOT[ch]))
               for ch in CHANNELS}
    ra = evaluate(models, T, H, P, R, K, base_read, 'pivot_check_a', theta_a)
    rb = evaluate(models, T, H, P, R, K, base_read, 'pivot_check_b', theta_b,
                  pivots=zero_pivot)
    pivot_check = {}
    for key in ('resid_rms', 'resid_offset'):
        pivot_check[key] = float(abs(ra[key] - rb[key]))
    for ch in CHANNELS:
        pivot_check[f'd_alpha_{ch}_read'] = float(
            abs(ra[f'd_alpha_{ch}_read'] - rb[f'd_alpha_{ch}_read']))
    print('pivot re-centring invariance (max abs deviation): ' +
          '  '.join(f'{k}={v:.2e}' for k, v in pivot_check.items()))

    # ------------------------------------------------------------ summary
    elapsed = time.time() - t_start
    summary = {'meta': {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'script': Path(__file__).name,
        'data': str(data_path), 'models': str(models_dir),
        'subsample': args.subsample, 'rows': int(len(d)), 'rows_total': int(len(df)),
        'quick': bool(args.quick), 'edge_points_per_edge': n_edge,
        'random_draws': n_rand, 'refine_draws_per_best': n_refine,
        'linear_bound': not args.no_linear_bound,
        'evaluations': int(len(tbl)), 'evaluations_feasible': int(len(feas)),
        'channel_only_evaluations': n_channel_only,
        'seed': args.seed,
        'delta': DELTA, 'pivot': PIVOT, 'u_comb': args.u_comb,
        'elapsed_s': round(elapsed, 1),
    }, 'self_check': self_check,
       'envelope': {ch: {'min': float(env[ch].xmin), 'max': float(env[ch].xmax),
                       'span': float(env[ch].span),
                       'gamma_max': float(env[ch].gamma_max),
                       'g_max': float(1.0 + env[ch].gamma_max),
                       'max_abs_b': float(env[ch].max_abs_b()),
                       'b_at_g_max': float(env[ch].vertices()[3][1]),
                       'max_gain_at_zero_offset': float(
                           env[ch].max_gain_at_zero_offset()),
                       'uncentred_b_at_g_max': float(env[ch].gamma_max * env[ch].x0),
                       'uncentred_exceeds_spec_by': float(
                           env[ch].gamma_max * env[ch].x0 / env[ch].delta)}
                  for ch in CHANNELS},
       'baseline': {'d_alpha_read': base_read, 'alpha_data': base_alpha,
                    'resid_rms': float(base.resid_offset_removed_rms),
                    'resid_offset': float(base.resid_offset), 'K': float(K)},
       'worst_case': {}, 'reference_slices': [], 'channel_only': {},
       'pivot_recentring': pivot_check, 'jacobian': jacobian}

    print('\n' + '=' * 104)
    print(f"{'response':>12} {'E vertices':>13} {'E sampled':>13} {'E linearised':>13} "
          f"{'E/sqrt3':>12} {'SM single':>12} {'SM/E':>8}")
    print('=' * 104)
    for ch in CHANNELS:
        col = f'delta_{ch}'
        rmax = feas.loc[feas[col].abs().idxmax()]
        E_all = abs(float(rmax[col]))
        sub_v = feas[feas['kind'].str.startswith('vertex')]
        E_v = abs(float(sub_v.loc[sub_v[col].abs().idxmax()][col]))
        sm = abs(base_alpha[ch]) * env[ch].gamma_max
        E_lin = (linear_bound or {}).get(ch)
        worst = {
            'E_vertices': E_v, 'E_sampled': E_all,
            'E_linearised': E_lin,
            'linearised_below_sampled': (None if E_lin is None
                                         else bool(E_lin < E_all)),
            'u_syst_rectangular': E_all / np.sqrt(3.0),
            'sm_single_branch': float(sm),
            'sm_over_consistent': float(sm / E_all) if E_all > 0 else None,
            'delta_min': float(feas[col].min()), 'delta_max': float(feas[col].max()),
            'attained_kind': str(rmax['kind']),
            'attained_calibration': {k: float(rmax[k]) for k in
                                     ('g_T', 'b_T', 'g_H', 'b_H', 'g_P', 'b_P')},
            'attained_delta': float(rmax[col]),
            'attained_d_alpha_read': {c: float(rmax[f'd_alpha_{c}_read'])
                                      for c in CHANNELS},
            'resid_rms_at_max': float(rmax['resid_rms']),
        }
        if args.u_comb:
            worst['E_over_u_comb'] = float(E_all / args.u_comb)
            worst['baseline_over_u_comb'] = float(abs(base_read[ch]) / args.u_comb)
        summary['worst_case'][ch] = worst
        print(f'{("d_alpha_" + ch):>12} {E_v:>13.4e} {E_all:>13.4e} '
              f'{(E_lin if E_lin is not None else float("nan")):>13.4e} '
              f'{E_all / np.sqrt(3.0):>12.4e} {sm:>12.4e} '
              f'{(sm / E_all if E_all else float("nan")):>7.2f}x')
    print('=' * 104)
    if args.u_comb:
        print(f'with u_comb = {args.u_comb:.3e}:  ' + '  '.join(
            f'{ch}: E={summary["worst_case"][ch]["E_over_u_comb"]:.2f} u, '
            f'baseline={summary["worst_case"][ch]["baseline_over_u_comb"]:.2f} u'
            for ch in CHANNELS))

    if args.u_stat:
        d_h = abs(base_read['H'])
        u_syst_rev = summary['worst_case']['H']['u_syst_rectangular']
        u_comb_sm = float(np.hypot(args.u_stat, args.sm_u_syst))
        u_comb_rev = float(np.hypot(args.u_stat, u_syst_rev))
        summary['significance_H'] = {
            'd_alpha_H': d_h, 'u_stat': args.u_stat,
            'sm_u_syst': args.sm_u_syst, 'sm_u_comb': u_comb_sm,
            'sm_significance': d_h / u_comb_sm,
            'revised_u_syst': float(u_syst_rev), 'revised_u_comb': u_comb_rev,
            'revised_significance': d_h / u_comb_rev,
            'sm_endpoint': summary['worst_case']['H']['sm_single_branch']}
        print(f'\nDelta alpha_H = {d_h:.4e}, u_stat = {args.u_stat:.3e}')
        print(f"  SM        : u_syst {args.sm_u_syst:.3e} -> u_comb {u_comb_sm:.3e} "
              f"-> {d_h / u_comb_sm:.2f} u_comb")
        print(f"  consistent: u_syst {u_syst_rev:.3e} -> u_comb {u_comb_rev:.3e} "
              f"-> {d_h / u_comb_rev:.2f} u_comb")

    print('\nchannel-resolved envelope contributions (own-channel vertices only):')
    for c in CHANNELS:
        sub = feas[feas['kind'] == f'channel_only_{c}']
        summary['channel_only'][c] = {
            r: float(abs(sub[f'delta_{r}']).max()) for r in CHANNELS}
    print(f"{'':>12}" + ''.join(f'{("from " + c):>14}' for c in CHANNELS))
    for r in CHANNELS:
        print(f'  d_alpha_{r:<3}' + ''.join(
            f"{summary['channel_only'][c][r]:>14.4e}" for c in CHANNELS))
    print('  (the SM endpoint rescales only the same channel; the joint maximum above '
          'includes the cross-channel terms)')

    print('\nreference slices (gain-only hypotheses at the endpoint gain; OUTSIDE the '
          'feasible envelope):')
    for _, r in tbl[tbl['kind'].str.startswith(REFERENCE_PREFIXES)].iterrows():
        ch = r['kind'].split('_')[-1]
        print(f"  {r['kind']:<28} g_{ch}={r[f'g_{ch}']:.5f} "
              f"b_{ch}={r[f'b_{ch}']:+.4f}  delta_{ch}={r[f'delta_{ch}']:+.4e}")
        summary['reference_slices'].append({
            'kind': str(r['kind']), 'channel': ch,
            'g': float(r[f'g_{ch}']), 'b': float(r[f'b_{ch}']),
            'delta': float(r[f'delta_{ch}']),
            'resid_rms': float(r['resid_rms'])})

    # ------------------------------------------------------------- write
    out_json = out_path
    out_csv = out_path.with_name(out_path.stem + '_samples.csv')
    out_md = out_path.with_name(out_path.stem + '.md')
    out_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    tbl.to_csv(out_csv, index=False)
    write_report(out_md, summary)
    print(f'\nwrote {out_json}')
    print(f'wrote {out_csv}')
    print(f'wrote {out_md}')
    print(f'total {len(tbl)} evaluations in {elapsed:.1f}s')


if __name__ == '__main__':
    main()
