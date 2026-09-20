"""P2 checks for the NS10657 review round (Ulrich feedback, Sept 2026).

Run from this directory with Python 3.11:

    MPLCONFIGDIR=/tmp/mplcfg /opt/homebrew/bin/python3.11 p2_checks.py

Optional arguments:

    --v1 PATH     root of the v1.0 package (raw + processed data)
    --v2 PATH     root of the v2.0 package (processed data)
    --full-raw    also re-scan the raw interferometer/environmental files to
                  recompute the rejected-row statistics and the counter/sensor
                  time mismatch from scratch (slow: reads every daily CSV)

Checks
------
C1  Train/validation overlap
    Confirm the 3,459 shared timestamps between training_data.csv and
    validation_data.csv, and identify the calendar day(s) responsible.
    Ulrich asked whether any reported validation used overlapping observations.

C2  Rejected rows (requires --full-raw)
    The preprocessing filter is counts_ratio in [2.2584867, 3].  The lower
    bound equals the minimum of the retained data, i.e. it is data-defined.
    Report how many rows the filter removes and how their T/HR/P compare with
    the retained rows, to show whether the rejection is selectively removing
    valid high-humidity conditions.

C3  Counter/sensor time mismatch (requires --full-raw)
    The environmental channels are attached with merge_asof(direction='nearest'),
    so each counter row takes the nearest sensor sample.  Report the
    distribution of |dt| for the three channels.

C4  Constant-anchor-offset check
    n_1762 = (f_780 / f_1762) * n_780 / R(t).  A constant offset K on the
    780 nm anchor n_780 appears in n_1762 as a time-dependent term
    K * (f_780/f_1762) / R(t) whose amplitude is proportional to K * dR/R.
    Quantify it against the residual scatter and the humidity term.

Outputs p2_checks_results.json next to this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Fixed constants of the measurement (copied from
# v1.0/code/data_processing/preprocess_data.ipynb; do not edit here without
# editing PROVENANCE.md as well)
# ---------------------------------------------------------------------------
F_1762_HZ = 170.126432e12        # 1762 nm optical frequency
F_RB_HZ = 384.2281145e12         # rubidium-referenced 780 nm frequency
RATIO_NOMINAL = F_RB_HZ / F_1762_HZ          # = 2.2584857...
COUNTS_RATIO_MIN = 2.2584867
COUNTS_RATIO_MAX = 3.0

# Constant-anchor offset scanned in C4 (units of refractive index).
K_ANCHOR_DEFAULT = 5.2e-6
RESIDUAL_SCATTER = 1.8367e-7     # SM Table S1a residual scatter (sigma_n)

HERE = Path(__file__).resolve()
DEFAULT_V2 = HERE.parents[2]
DEFAULT_V1 = DEFAULT_V2.parent / "refractive_index_1762nm_v1.0"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _raw_loader(data_path: Path, start_date: str, end_date: str):
    """Replication of load_interferometer_data() from the v1.0 preprocessor.

    Returns the *unfiltered* per-type concatenated frames plus the filtered,
    merged frame, so that C2/C3 can be evaluated.
    """
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    date_range = [start + timedelta(days=i)
                  for i in range((end - start).days + 1)]

    frames = {"counts_ratio": [], "humidity": [], "temperature": [],
              "pressure": []}
    for date in date_range:
        d = date.strftime("%Y%m%d")
        paths = {
            "counts_ratio": data_path / "interferometer" / f"counts_ratio_data_{d}.csv",
            "humidity": data_path / "environmental" / f"humidity_data_{d}.csv",
            "pressure": data_path / "environmental" / f"pressure_data_{d}.csv",
            "temperature": data_path / "environmental" / f"temperature_data_{d}.csv",
        }
        if not all(p.exists() for p in paths.values()):
            continue
        for kind, path in paths.items():
            df = pd.read_csv(path)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
            frames[kind].append(df)

    raw = {}
    for kind, dfs in frames.items():
        if not dfs:
            raise SystemExit(f"no raw {kind} files found under {data_path}")
        raw[kind] = pd.concat(dfs, ignore_index=True).dropna(
            subset=["time"]).sort_values("time").reset_index(drop=True)

    raw["humidity"] = raw["humidity"].rename(
        columns={"humidity_wm_bme280": "humidity"})
    raw["temperature"] = raw["temperature"].rename(
        columns={"temperature_wm_bme280": "temperature"})
    raw["pressure"] = raw["pressure"].rename(
        columns={"pressure_wm_bme280": "pressure"})
    return raw


def _nearest_dt(left_times: pd.Series, env: pd.DataFrame,
                env_col: str) -> np.ndarray:
    """|dt| (seconds) of the merge_asof(direction='nearest') join."""
    right = env[["time", env_col]].rename(columns={"time": "t_env"})
    left = (left_times.rename("time").to_frame()
            .reset_index(drop=True))
    joined = pd.merge_asof(left, right, on="time", direction="nearest")
    dt = (joined["t_env"] - joined["time"]).dt.total_seconds()
    return dt.abs().to_numpy()


def _describe(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float)
    return {
        "n": int(values.size),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "max": float(values.max()),
        "frac_above_10s": float(np.mean(values > 10.0)),
        "frac_above_60s": float(np.mean(values > 60.0)),
    }


# ---------------------------------------------------------------------------
# C1 - train/validation overlap
# ---------------------------------------------------------------------------
def check_overlap(v2_processed: Path) -> dict:
    tr = pd.read_csv(v2_processed / "training_data.csv",
                     usecols=["time"], parse_dates=["time"])
    va = pd.read_csv(v2_processed / "validation_data.csv",
                     usecols=["time"], parse_dates=["time"])
    fu = pd.read_csv(v2_processed / "full_data.csv",
                     usecols=["time"], parse_dates=["time"])

    tr_t, va_t, fu_t = tr["time"], va["time"], fu["time"]
    n_tr, n_va, n_fu = len(tr_t), len(va_t), len(fu_t)
    shared = set(tr_t) & set(va_t)

    # sanity: full_data should be the union without duplication
    union = set(tr_t) | set(va_t)
    result = {
        "n_training": n_tr,
        "n_validation": n_va,
        "n_full": n_fu,
        "n_training_plus_validation": n_tr + n_va,
        "arithmetic_gap": n_tr + n_va - n_fu,
        "n_shared_timestamps": len(shared),
        "gap_equals_shared": (n_tr + n_va - n_fu) == len(shared),
        "n_union": len(union),
        "union_equals_full": len(union) == n_fu,
        "training_range": [str(tr_t.min()), str(tr_t.max())],
        "validation_range": [str(va_t.min()), str(va_t.max())],
        "full_range": [str(fu_t.min()), str(fu_t.max())],
    }
    if shared:
        s = pd.Series(sorted(shared))
        result["shared_days"] = {str(k): int(v) for k, v in
                                 s.dt.floor("D").value_counts().sort_index().items()}
    return result


# ---------------------------------------------------------------------------
# C2 + C3 - rejected rows and counter/sensor mismatch (raw scan)
# ---------------------------------------------------------------------------
def check_raw(raw_dir: Path, start_date: str, end_date: str,
              keep_frames: bool = True) -> dict:
    raw = _raw_loader(raw_dir, start_date, end_date)
    cr = raw["counts_ratio"]
    mask = ((cr["counts_ratio"] >= COUNTS_RATIO_MIN) &
            (cr["counts_ratio"] <= COUNTS_RATIO_MAX))
    kept, dropped = cr[mask], cr[~mask]

    out = {
        "n_counts_rows_total": int(len(cr)),
        "n_kept": int(len(kept)),
        "n_dropped": int(len(dropped)),
        "kept_fraction": float(len(kept) / len(cr)),
        "counts_ratio_kept_min": float(kept["counts_ratio"].min()),
        "counts_ratio_kept_max": float(kept["counts_ratio"].max()),
        "counts_ratio_span_rel": float(
            (kept["counts_ratio"].max() - kept["counts_ratio"].min()) /
            RATIO_NOMINAL),
        "counts_ratio_all_min": float(cr["counts_ratio"].min()),
        "counts_ratio_all_max": float(cr["counts_ratio"].max()),
    }
    if len(dropped):
        out["dropped_ratio_hist"] = {
            "below_min": int((dropped["counts_ratio"] < COUNTS_RATIO_MIN).sum()),
            "above_max": int((dropped["counts_ratio"] > COUNTS_RATIO_MAX).sum()),
            "below_min_values": [float(v) for v in
                                 dropped.loc[dropped["counts_ratio"] < COUNTS_RATIO_MIN,
                                             "counts_ratio"].head(20)],
        }
    out["dropped_by_month"] = (
        dropped.assign(m=dropped["time"].dt.to_period("M").astype(str))
        .groupby("m").size().to_dict() if len(dropped) else {})

    # Attach the environmental channels exactly as the preprocessor does, so
    # that the T/H/P comparison and the |dt| statistics are on the same rows.
    merged = kept
    dt_stats = {}
    for env_col in ("humidity", "temperature", "pressure"):
        dt_stats[env_col] = _describe(
            _nearest_dt(merged["time"], raw[env_col], env_col))
        merged = pd.merge_asof(merged, raw[env_col][["time", env_col]],
                               on="time", direction="nearest")

    dropped_env = dropped
    for env_col in ("humidity", "temperature", "pressure"):
        dropped_env = pd.merge_asof(dropped_env,
                                    raw[env_col][["time", env_col]],
                                    on="time", direction="nearest")

    def _range(df, col):
        v = df[col].dropna()
        return [float(v.min()), float(np.median(v)), float(v.max())]

    out["nearest_neighbour_dt_seconds"] = dt_stats
    out["env_ranges"] = {
        "kept": {c: _range(merged, c)
                 for c in ("temperature", "humidity", "pressure")},
        "dropped": {c: _range(dropped_env, c)
                    for c in ("temperature", "humidity", "pressure")},
    }
    out["env_ranges_legend"] = "[min, median, max]"

    # Does the rejection preferentially remove humid rows?
    if len(dropped) and len(merged):
        hi_kept = float((merged["humidity"] > 80).mean())
        hi_drop = float((dropped_env["humidity"] > 80).mean())
        out["fraction_rh_above_80pct"] = {"kept": hi_kept, "dropped": hi_drop}
    return out


# ---------------------------------------------------------------------------
# C4 - constant-anchor-offset check
# ---------------------------------------------------------------------------
def check_constant_anchor(v2_processed: Path,
                          K: float = K_ANCHOR_DEFAULT) -> dict:
    df = pd.read_csv(v2_processed / "full_data.csv")
    R = df["counts_ratio"].to_numpy(dtype=float)
    n1762 = df["n_1762"].to_numpy(dtype=float)

    # invert the measurement equation to recover the 780 nm anchor
    n780 = n1762 * R / RATIO_NOMINAL

    # a constant offset K on the anchor maps to  dn(t) = K * RATIO_NOMINAL / R
    dn = K * RATIO_NOMINAL / R
    dn_mod = dn - dn.mean()

    # residual scatter quoted in the SM is the OLS residual of the full model;
    # here we only need an order-of-magnitude reference, so use the scatter of
    # the series about a simple linear time trend.
    t = np.arange(len(n1762), dtype=float)
    trend = np.polyval(np.polyfit(t, n1762, 1), t)
    scatter = float(np.std(n1762 - trend))

    dr_over_r = float((R.max() - R.min()) / R.mean())
    return {
        "K": float(K),
        "R_mean": float(R.mean()),
        "R_min": float(R.min()),
        "R_max": float(R.max()),
        "dR_over_R_peak_to_peak": dr_over_r,
        "dn_dc_offset": float(dn.mean()),
        "dn_modulation_peak_to_peak": float(dn_mod.max() - dn_mod.min()),
        "dn_modulation_std": float(np.std(dn_mod)),
        "analytic_amplitude_K_times_dR_over_R": float(K * dr_over_r),
        "reference_residual_scatter_sm": RESIDUAL_SCATTER,
        "ratio_modulation_over_residual": float(
            (dn_mod.max() - dn_mod.min()) / RESIDUAL_SCATTER),
        "scatter_detrended_linear": scatter,
        "verdict": ("PASS - the constant-anchor term is many orders of "
                    "magnitude below the residual scatter"
                    if (dn_mod.max() - dn_mod.min()) < 1e-3 * RESIDUAL_SCATTER
                    else "REVIEW"),
    }


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v1", type=Path, default=DEFAULT_V1)
    ap.add_argument("--v2", type=Path, default=DEFAULT_V2)
    ap.add_argument("--full-raw", action="store_true",
                    help="re-scan all daily raw CSVs (C2/C3)")
    ap.add_argument("--start", default="20241230")
    ap.add_argument("--end", default="20250821")
    ap.add_argument("--K", type=float, default=K_ANCHOR_DEFAULT)
    args = ap.parse_args(argv)

    v2_proc = args.v2 / "data" / "processed"
    raw_dir = args.v1 / "data" / "raw"

    results = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "v2_processed": str(v2_proc),
        "raw_dir": str(raw_dir),
    }

    print("=" * 72)
    print("C1 - train/validation overlap")
    print("=" * 72)
    results["C1_overlap"] = check_overlap(v2_proc)
    for k, v in results["C1_overlap"].items():
        print(f"  {k}: {v}")

    print()
    print("=" * 72)
    print("C4 - constant-anchor-offset check")
    print("=" * 72)
    results["C4_constant_anchor"] = check_constant_anchor(v2_proc, K=args.K)
    for k, v in results["C4_constant_anchor"].items():
        print(f"  {k}: {v}")

    if args.full_raw:
        print()
        print("=" * 72)
        print("C2/C3 - raw scan (this reads every daily CSV; be patient)")
        print("=" * 72)
        out = check_raw(raw_dir, args.start, args.end)
        results["C2_rejected_rows"] = {
            k: v for k, v in out.items()
            if k in ("n_counts_rows_total", "n_kept", "n_dropped",
                     "kept_fraction", "counts_ratio_kept_min",
                     "counts_ratio_kept_max", "counts_ratio_span_rel",
                     "counts_ratio_all_min", "counts_ratio_all_max",
                     "dropped_ratio_hist", "dropped_by_month",
                     "fraction_rh_above_80pct")}
        results["C3_time_mismatch"] = {
            "nearest_neighbour_dt_seconds": out["nearest_neighbour_dt_seconds"],
            "env_ranges": out["env_ranges"],
            "env_ranges_legend": out["env_ranges_legend"]}
        for section in ("C2_rejected_rows", "C3_time_mismatch"):
            print(f"-- {section} --")
            for k, v in results[section].items():
                print(f"  {k}: {v}")
            print()
    else:
        print()
        print("C2/C3 skipped: re-run with --full-raw to scan the raw daily "
              "CSVs for the rejected-row statistics and the counter/sensor "
              "time mismatch.")

    out_path = HERE.parent / "p2_checks_results.json"
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)
    print()
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
