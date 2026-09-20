"""Shared physical-time block utilities for the ACTOMICS statistical analysis.

Why this module exists
----------------------
The v1.0 / earlier v2.0 notebooks resampled fixed *row* blocks of
``L = 156`` samples, obtained as twice the ``1/e`` crossing of the residual
autocorrelation.  That choice has three defects that were raised in review:

1. ``L = 156`` was applied along the row axis of a file that contains a
   111-day gap, so a single block could straddle the gap.
2. The residual autocorrelation is not single-scaled: after a fast decay it
   retains a positive diurnal lobe (rho ~ 0.14 at 20-22 h).  A block length
   derived from the fast ``1/e`` crossing therefore *understates* the
   statistical uncertainty, and does not describe the full dependence.
3. ``L = 156`` was occasionally converted to a duration with a global
   12.9 s cadence, whereas the mean within-segment cadence is 21.1 s.

Consequently, no single nominal block length is adopted anywhere in the
analysis.  Instead the block duration is swept in *physical time* over
``D_LIST_HOURS`` and the coverage fraction of the block pool is reported for
each duration.

Blocks are built inside continuous segments (a gap longer than
``GAP_SECONDS`` ends a segment), so no block crosses a data gap.  Block
indices are inclusive: a block is ``(i0, i1)`` and covers rows
``i0 ... i1`` inclusive (``design[i0:i1 + 1]``), matching
``06_statistical_robustness.ipynb``.

This module is the single implementation shared by notebooks 01, 02, 03 and
06.  Do not re-implement the block construction locally.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: A gap longer than this splits the campaign into continuous segments.
GAP_SECONDS = 2 * 3600.0

#: Block durations in seconds, as actually swept (2012.4 s, 25800 s, 1 d, 2 d).
#: 2012.4 s = 156 x 12.9 s, the historical L = 156 anchor retained *only* as a
#: duration; it is not a row count and no cadence is re-used to convert it.
D_LIST_SECONDS = (2012.4, 25800.0, 86400.0, 172800.0)

#: The same durations expressed in hours (0.559 h, 7.1667 h, 24 h, 48 h).
#: Derived from ``D_LIST_SECONDS`` so that the two representations cannot
#: drift apart (an earlier revision listed 0.5598 h here against 2012.4 s
#: there, which made 06 report 1379 blocks while 01/02/03 reported 1376).
D_LIST_HOURS = tuple(s / 3600.0 for s in D_LIST_SECONDS)


def time_seconds(time_column):
    """POSIX seconds (float64) for a Series of timestamps.

    The conversion goes through ``datetime64[ns]`` so that fractional
    seconds are preserved: truncating to whole seconds (``datetime64[s]``)
    shifts every timestamp by up to 1 s relative to the epoch-second arrays
    built directly in notebooks 06 and 07, which can move a block boundary
    and hence the reported block counts.
    """
    series = pd.to_datetime(time_column, utc=True)
    return series.values.astype("datetime64[ns]").astype("int64") / 1e9


def segment_bounds(t, gap_seconds=GAP_SECONDS):
    """Inclusive (first, last) index pairs of the continuous segments of ``t``.

    ``t`` must be sorted ascending; segments are separated by gaps longer
    than ``gap_seconds``.
    """
    t = np.asarray(t, dtype=float)
    dt = np.diff(t)
    starts = np.concatenate([[0], np.where(dt > gap_seconds)[0] + 1])
    stops = np.concatenate([starts[1:] - 1, [len(t) - 1]])
    return list(zip(starts.tolist(), stops.tolist()))


def build_blocks(t, duration_seconds, seg_bounds=None, min_frac=0.5):
    """Physical-time blocks spanning ``duration_seconds`` within segments.

    Each block starts at the first unused sample of a segment and extends
    until it spans at least ``duration_seconds``; the next block then starts
    at the following sample, so blocks are non-overlapping and tile the
    segment.  A trailing partial block is kept only if it spans at least
    ``min_frac * duration_seconds``, and is otherwise dropped from the pool.

    Returns a list of inclusive ``(i0, i1)`` index pairs.  Identical to
    ``build_blocks`` in ``06_statistical_robustness.ipynb``.
    """
    t = np.asarray(t, dtype=float)
    if seg_bounds is None:
        seg_bounds = segment_bounds(t)
    blocks = []
    for (a, b) in seg_bounds:
        i0 = int(a)
        if i0 >= len(t):
            continue
        while i0 <= b:
            i1 = i0
            while i1 < b and t[i1] - t[i0] < duration_seconds:
                i1 += 1
            if t[i1] - t[i0] >= min_frac * duration_seconds:
                blocks.append((i0, int(i1)))
            i0 = i1 + 1
    return blocks


def coverage(blocks, n):
    """Fraction of the ``n`` observations represented by the block pool."""
    return sum(i1 - i0 + 1 for i0, i1 in blocks) / float(n)


def block_grid_summary(t, durations_hours=D_LIST_HOURS):
    """Per-duration block count, observations used and coverage fraction."""
    t = np.asarray(t, dtype=float)
    rows = []
    for D in durations_hours:
        blocks = build_blocks(t, D * 3600.0)
        used = sum(i1 - i0 + 1 for i0, i1 in blocks)
        rows.append(dict(D_hours=float(D),
                         n_blocks=len(blocks),
                         n_used=int(used),
                         coverage=used / float(len(t))))
    return rows


def block_sufficient_stats(design, y_list, blocks):
    """Per-block ``X'X`` and ``X'y`` sufficient statistics.

    Parameters
    ----------
    design : (N, p) ndarray of regressors, including the intercept column
    y_list : sequence of (N,) response vectors
    blocks : list of inclusive (i0, i1) index pairs

    Returns
    -------
    W : (n_blocks, p * p) flattened per-block ``X'X``
    U : (n_blocks, len(y_list), p) per-block ``X'y`` for each response
    """
    design = np.asarray(design, dtype=float)
    p = design.shape[1]
    W = np.empty((len(blocks), p * p))
    U = np.empty((len(blocks), len(y_list), p))
    for b, (i0, i1) in enumerate(blocks):
        Xb = design[i0:i1 + 1]
        W[b] = (Xb.T @ Xb).ravel()
        for j, y in enumerate(y_list):
            U[b, j] = Xb.T @ np.asarray(y, dtype=float)[i0:i1 + 1]
    return W, U


def bootstrap_row_chunks(blocks, n_draws=5000, seed=42):
    """Yield row-index arrays for ``n_draws`` block resamples.

    Useful for statistics that are not a plain OLS coefficient (e.g. ratios
    of residual standard deviations).  Each draw resamples ``len(blocks)``
    blocks with replacement.
    """
    rng = np.random.default_rng(seed)
    n_blocks = len(blocks)
    for _ in range(n_draws):
        picks = rng.integers(0, n_blocks, size=n_blocks)
        yield np.concatenate([np.arange(blocks[b][0], blocks[b][1] + 1)
                              for b in picks])


def coefficient_bootstrap(design, y, blocks, n_draws=5000, seed=42):
    """Moving-block bootstrap of one model's coefficients.

    Returns an (n_draws, p) array of bootstrap coefficient vectors.
    """
    W, U = block_sufficient_stats(design, [y], blocks)
    design = np.asarray(design, dtype=float)
    p = design.shape[1]
    n_blocks = len(blocks)
    rng = np.random.default_rng(seed)
    out = np.empty((n_draws, p))
    for i in range(n_draws):
        picks = rng.integers(0, n_blocks, size=n_blocks)
        XtX = W[picks].sum(axis=0).reshape(p, p)
        out[i] = np.linalg.solve(XtX, U[picks, 0].sum(axis=0))
    return out


def paired_coefficient_bootstrap(design, y_a, y_b, blocks, n_draws=5000, seed=42):
    """Paired moving-block bootstrap of ``beta_a - beta_b``.

    The same resampled blocks are used for both models, which preserves the
    correlation between the two estimates.  Returns an (n_draws, p) array of
    coefficient differences.
    """
    W, U = block_sufficient_stats(design, [y_a, y_b], blocks)
    design = np.asarray(design, dtype=float)
    p = design.shape[1]
    n_blocks = len(blocks)
    rng = np.random.default_rng(seed)
    out = np.empty((n_draws, p))
    for i in range(n_draws):
        picks = rng.integers(0, n_blocks, size=n_blocks)
        XtX = W[picks].sum(axis=0).reshape(p, p)
        beta_a = np.linalg.solve(XtX, U[picks, 0].sum(axis=0))
        beta_b = np.linalg.solve(XtX, U[picks, 1].sum(axis=0))
        out[i] = beta_a - beta_b
    return out


def sweep_summary(draws, labels, coverage_fraction=None):
    """Summarise a bootstrap draw array for reporting.

    Returns a list of dicts with the standard error and the 95 % percentile
    interval for each column, tagged with its label.
    """
    rows = []
    for j, lab in enumerate(labels):
        col = draws[:, j]
        lo, hi = np.percentile(col, [2.5, 97.5])
        rows.append(dict(label=lab,
                         mean=float(col.mean()),
                         se=float(col.std(ddof=1)),
                         lo=float(lo),
                         hi=float(hi),
                         coverage=coverage_fraction))
    return rows
