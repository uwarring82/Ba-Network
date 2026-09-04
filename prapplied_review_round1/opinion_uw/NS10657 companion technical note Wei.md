# NS10657 — Companion technical note (for Wei)

Backing for the reanalysis task card: the arithmetic behind the two findings, the specifications behind each task, and the verified references. Read alongside the task card; section numbers match its **[CN §x]** cross-references. Every number here should be reproduced from version-controlled code before it enters the response letter.

---

## §1 The two findings

### The 85 % improvement is a static-offset artifact — settled
Mathar's quoted residual combines a static offset and residual scatter in quadrature:
√((1.166×10⁻⁶)² + (1.93×10⁻⁷)²) = 1.182×10⁻⁶ ≈ the quoted RMSE 1.18×10⁻⁶.
The offset alone is 4.16 rad over 1 m at 1762 nm — nearly the entire quoted 4.31-rad Mathar residual *amplitude*. Any deployed feed-forward system removes a constant phase with one initial calibration. Offset-removed, the residual standard deviations are **1.84×10⁻⁷ (empirical) vs 1.93×10⁻⁷ (Mathar) — a 4.7 % improvement, not 85 %.** The 85 % figure compares an intercept-fitted empirical model against a non-offset-corrected Mathar baseline. Reporting both I_amplitude and I_variance (Task 2) keeps the amplitude / variance / RMSE distinction explicit and avoids the earlier "96 %" phrasing, which mixed the two.

### The +17.2 % enhancement is very likely a temperature-reference artifact — Task 1 decides
Our quoted "Mathar" α_H (−1.1219×10⁻⁸ %RH⁻¹) matches Mathar evaluated at ≈ 20 °C to four figures, but the campaign mean is 24.7 °C. Mathar's humidity derivative grows with temperature because water content per 1 % RH tracks the saturation vapour pressure, which rises ~33 % from 20 to 24.7 °C (Magnus: e_s(20 °C) = 23.3 hPa, e_s(24.7 °C) = 31.0 hPa). A first-principles estimate gives |α_H| about +31 % higher at 24.7 °C; the full Mathar parametrisation gives +23 % (cross-terms account for the difference). Hence:
- measured vs Mathar @ 20 °C: **+17.2 %** — reproduces our headline, i.e. Mathar was evaluated at a ≈ 20 °C reference;
- measured vs Mathar @ 24.7 °C: **−4.4 %** — same-temperature comparison.

The −4.4 % is a single *local* derivative at the mean, not the definitive figure — it compares a campaign-wide OLS slope against one point. Task 1's surrogate fit over the full cloud (leverage-weighted across 15–35 °C) is decisive; the exact reproduction at 20 °C is strong evidence of an inconsistent reference temperature, but "confirmed" waits on that fit.

**Task 1 methodology rationale.** Generating Mathar at the identical (T, H, P)ᵢ and fitting the *same* OLS surrogate removes the local-derivative-vs-global-slope confound entirely — both coefficients then answer the same question over the same data cloud. The two coefficients are estimated on shared rows, so the uncertainty on their *difference* must use a **paired** temporal-block procedure, not independent errors. Block length is set from the residual autocorrelation time (as in the existing HAC / block-bootstrap diagnostics). Identical folds and training-only offset estimation prevent leakage; global preprocessing (e.g. de-meaning) before splitting would leak test information into training.

---

## §2 Why the uncertainty budget is not reproducible
Direct propagation of the absolute sensor tolerances (systematic; does not average down):
|α_T|·0.5 K = 4.4×10⁻⁷, |α_H|·3 % = 3.9×10⁻⁸, |α_P|·1 hPa = 2.6×10⁻⁷.
Dividing by √N (N = 145 784): 1.16×10⁻⁹ (T), 1.03×10⁻¹⁰ (H), 6.80×10⁻¹⁰ (P).
SM Table I lists: 1.42×10⁻¹⁰ (T), 1.25×10⁻¹⁰ (H), 9.11×10⁻¹³ (P).
Only humidity is near the √N value; **temperature is ~8× smaller and pressure ~750× smaller.** The entries follow neither direct propagation nor simple √N averaging, and the SM does not document the method that produced them — Task 4 must find the exact per-entry formula. Separately, the SM text models the tolerances as independent per-sample Gaussians, which is the wrong model for persistent calibration effects (offset, gain, nonlinearity, hysteresis, drift): those do not average down and bias the coefficients rather than adding random scatter.

---

## §3 Mathar validity domain (verified)
Mathar 2007 (J. Opt. A 9, 470; arXiv physics/0610256) states the fits are least-squares to highly-resolved spectra over **T = 10–25 °C, P = 500–1023 hPa, RH = 5–60 %**. Campaign pressure (965–1000 hPa) and RH (20–45 %) are within range throughout; the binding constraint for the in-domain analysis is temperature — exclude T > 25 °C (campaign reaches 35 °C).

---

## §4 Sensor scale — rationale and feasibility
A constant offset shifts the fitted intercept, not the slope; a gain error biases α_H ~proportionally, so a 17 % RH-scale error is indistinguishable from a 17 % "enhancement." The ±3 % BME280 figure is an absolute-accuracy spec and does not bound the relative gain to < 17 % over a 25 %-RH span. A post-campaign bench calibration bounds only the sensor's *current* gain; it cannot reconstruct eight months of historical gain and drift, so combine it with the stability spec and any contemporaneous cross-sensor logs. If neither the unit nor a reference is available, bound the gain from specs + stability + cross-sensor data and state that a 17 %-level error is not excluded — honest, but it precludes claiming the enhancement is real.

---

## §5 Reparametrisation formulas (Ciddor-style)
Use water-vapour mole fraction with the enhancement factor f(T,p), as Ciddor does, then density:
- x_w = (H/100) · f(T,p) · p_sv(T) / p    [mole fraction]
- c_w = x_w · p / (Z · R · T)             [molar density, mol m⁻³]
- ρ_w = M_w · c_w                          [mass density, kg m⁻³]

(The earlier "ρ_w ≈ p_w/(Z_w R T)" was a molar density mislabelled as mass; use c_w for molar or multiply by M_w for mass.) f and Z are part of the Ciddor conversion. This removes much of the leading RH-to-water-content temperature dependence; residual T-dependence persists via moist-air compressibility, polarizability, dry-air displacement, and sensor cross-sensitivity. It does not replace the sensor calibration or the full-Mathar comparison — the BME280 still reports RH, so RH → x_w folds in T and e_s(T).

---

## §6 Kramers–Kronig
The SM's own KK calculation (Table III) gives α_H ≈ −1.09×10⁻⁸ %RH⁻¹ at mean conditions — close to the Mathar value (−1.12×10⁻⁸), not the measured −1.32×10⁻⁸. It reproduces the sign and order of magnitude of the humidity coefficient but **not the excess over Mathar.** The abstract's "consistent with a Kramers–Kronig analysis" should claim only qualitative compatibility (sign and order of magnitude), and state explicitly that the line-by-line spectrum does not reproduce the enhancement.

---

## §7 Gate infidelity
For an untracked azimuthal phase error δφ on a direct optical rotation by θ, the average infidelity is r ≈ (2/3) sin²(θ/2) δφ². With δφ = 0.03: **3×10⁻⁴ at π/2, 6×10⁻⁴ at π** — so "below 3×10⁻⁴" is π/2-specific; state θ and the fidelity convention (average vs process). ¹³⁸Ba⁺ has I = 0 (no hyperfine), so the qubit at 1762 nm is the directly-driven optical qubit whose rotation axis is set by the optical phase; the referee's Raman / microwave counterexamples do not apply.

Infidelity comes only from the **untracked residual** phase at gate time. A *measured* quasi-static phase is absorbed into the control phase or qubit frame — a frame update, not an error. The residual is the integral of the phase-noise PSD **above the correction bandwidth**. The interferometer samples every 10–20 s (≈ 0.03 Hz Nyquist), so it can characterise only the accessible low-frequency band; gate-timescale (and acoustic / turbulent) phase noise lies above that band and is unmeasured. Estimate the PSD over the accessible band, integrate above the correction bandwidth, and state the unmeasured high-frequency band explicitly. A defensible gate-infidelity bound requires either higher-bandwidth phase data or removal of the claim; a 10-minute update interval alone does not establish the untracked phase at gate time.

---

## §8 Motivation and phase-sensitivity taxonomy
**Phase-robust** (insensitive to the optical carrier / path phase — though still requiring temporal overlap, spectral indistinguishability, polarization control):
- Simon and Irvine, PRL 91, 110405 (2003): two trapped ions entangled by joint detection of two photons; two-photon interference gives entanglement free of interferometric sensitivity to the photons' path length. *(Verified against source.)*
- Stephenson et al., PRL 124, 110501 (2020): ⁸⁸Sr⁺, two 422 nm photons interfered on a beam splitter, heralded. *(Verified.)*

**Phase-sensitive** (entangled-state phase carries the path phase — our legitimate target):
- Slodička et al., PRL 110, 083603 (2013): single-photon (Cabrillo) heralding; control of the entangled-state phase demonstrated by varying the single-photon interferometer path length. *(Verified.)*

Narrow the introduction to direct phase-coherent optical control, free-space clock comparison, and these single-photon protocols; state that two-photon coincidence schemes are insensitive to the optical carrier / path phase. Align the intro with the body, which already delivers the local-beamline compensation case.

---

## §9 Absolute baseline offset
Treat the 1.166×10⁻⁶ absolute discrepancy between data and Mathar as an **unresolved interferometric or anchoring offset** unless an independent absolute calibration demonstrates otherwise. Do not attribute it to a Mathar error using an assumed Mathar absolute accuracy — that accuracy is unvalidated at 1762 nm, which is the paper's own motivation. (Physically, a real ~0.4 %-of-refractivity Mathar error between 780 and 1762 nm would be surprising given the smooth dispersion, which is a reason to check for an instrumental origin, not a conclusion.) The offset blocks any absolute-n claim; a surviving null result concerns the environmental coefficients, where the offset cancels.

---

## §10 Citation status
Verified against source (existence, venue, and the physics claimed): Simon and Irvine PRL 91 110405 (2003); Stephenson et al. PRL 124 110501 (2020); Slodička et al. PRL 110 083603 (2013); Mathar 2007 J. Opt. A 9 470 (validity domain, §3).
To confirm against the PDF before the response letter: Yum et al. JOSA B 34 1632 (2017) — direct 1762 nm 6S₁/₂ ↔ 5D₅/₂ optical-qubit rotations (supports §7; already manuscript ref [10]); Mathar 2007 Eqs. 6–7 — the quadratic and TH / TP / HP cross terms underlying referee point 6.
