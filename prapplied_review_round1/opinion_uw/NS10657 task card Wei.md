# Task card — NS10657 reanalysis

**Paper:** Wavelength-specific refractive-index calibration of air at 1762 nm
**Owner:** Wei Wu   ·   **Status:** major revision, PRApplied (fresh referee next round)
**Companion:** *NS10657 — companion technical note* (arithmetic, specifications, references). Card cross-refs it as [CN §x].

---

## Objective and decision gate

The referee is constructive and wants major revisions, not rejection. Re-running the numbers to answer them surfaced two issues to settle before defending anything:

- The **85 % compensation improvement** is a comparison artifact — ≈ 5 % once both models share one baseline calibration. Already fixed by our own numbers. [CN §1]
- The **+17.2 % humidity enhancement** is very likely a temperature-reference artifact; a same-temperature comparison gives ≈ −4.4 %. Very likely, not proven — Task 1 decides it. [CN §1]

The task is to discover the correct result, not defend the previous one. **Run Tasks 1–2 first, present them to all three authors, and freeze the outcome before any manuscript editing** (checkpoint below). Do not draft the response letter until the outcome is frozen.

---

## Decisive — do first

### ☐ Task 1 — Campaign-equivalent Mathar comparison  *(determines the headline)*
Fit the same linear surrogate n = n₀ + α_T T + α_H H + α_P P to a Mathar cloud generated at the identical observed (T, H, P)ᵢ, and compare coefficients. Two matched analyses on **identical rows**:
- **Primary, in-domain:** 10 ≤ T ≤ 25 °C (Mathar's validity; P and H are in range throughout — verified [CN §3]).
- **Secondary, full campaign:** all rows, T > 25 °C flagged as Mathar extrapolation.

Required output — one table, both datasets:

| Analysis | N | α_H^data | α_H^Mathar-surrogate | Difference | 95 % interval |
|---|---|---|---|---|---|
| In-domain (10–25 °C) |  |  |  |  |  |
| Full campaign |  |  |  |  |  |

The difference interval uses a **paired temporal-block** procedure (data and surrogate share rows). Also report the **fraction of observations above 25 °C**.

Blocked out-of-sample validation:
- block length justified from residual autocorrelation;
- identical folds for both models;
- offset estimated from training folds only;
- no global preprocessing before splitting.

**Done when:** the table and validation plots exist, and we can state whether a genuine wavelength-specific discrepancy survives a same-temperature comparison.

### ☐ Task 2 — Offset-fair improvement
Remove the constant term from **both** models (one baseline-phase calibration). Report both metrics with block-bootstrap intervals:
- I_amplitude = 1 − σ_emp / σ_Mathar
- I_variance = 1 − σ_emp² / σ_Mathar²

**Done when:** the improvement is quantified unambiguously (our numbers point to ≈ 5 %) and the 85 % / 4.31-rad framing is retired unless it survives. [CN §1]

---

## Parallel — start alongside

### ☐ Task 3 — Humidity-sensor scale  *(the evidence required to support any surviving enhancement)*
Bench-calibrate the **actual campaign BME280** against a traceable reference across 20–45 % RH and 15–35 °C, sweeping RH up **and** down. Gain / nonlinearity / temperature dependence — not offset — is what biases the slope.
**Fallback** if the unit or a reference is unavailable: bound the gain uncertainty from the manufacturer spec + stability (0.5 %RH/yr) + any cross-sensor logs, and state plainly that a 17 %-level scale error is not excluded. That still yields an honest paper — it means the enhancement cannot be claimed as real. [CN §4]

**Done when:** a measured (or bounded) RH gain and its uncertainty for the campaign sensor.

### ☐ Task 4 — Uncertainty-budget audit
Determine the **exact formula that produced each SM Table I entry** — they are not reproducible from the stated method (only the humidity entry is near ÷√N; T ~8×, P ~750× smaller [CN §2]). Check whether entries mix per-observation residual scatter, coefficient standard errors, sensor tolerances, and frequency-reference uncertainty — different measurands that cannot be root-sum-squared. Rebuild for a defined measurand, entering sensor error as persistent nuisance parameters, and propagate Task 3's systematic into the significance of any residual discrepancy.

**Done when:** every entry traces to version-controlled code with a stated measurand.

### ☐ Task 5 — Reparametrise humidity  *(recommended)*
Refit against water-vapour mole fraction / density, Ciddor-style with the enhancement factor (formulas in [CN §5]), rather than %RH. Removes much of the leading RH-to-water-content temperature dependence; residual T-dependence remains (compressibility, polarizability, dry-air displacement, sensor cross-sensitivity — expected).

**Done when:** coefficients refit against x_w / ρ_w with the reduced T-dependence documented.

---

## Post-gate — manuscript work (after the outcome is frozen)

### ☐ Task 6 — Referee points
- **Table I:** add uncertainties (statistical/HAC and systematic separately); cut sig-figs to what the systematic supports.
- **Kramers–Kronig:** soften to "qualitatively compatible with water-vapour dispersion (sign and order of magnitude)"; state that our own analysis reproduces Mathar, not the excess. [CN §6]
- **Gate infidelity:** state the ¹³⁸Ba⁺ optical-qubit mechanism (I = 0, no hyperfine → directly-driven optical qubit; the referee's Raman/microwave cases do not apply) and the θ-dependent formula (3×10⁻⁴ at π/2, 6×10⁻⁴ at π). **PSD requirement (revised):** the interferometer samples every 10–20 s, so estimate the residual-phase PSD over the *experimentally accessible* bandwidth, integrate above the proposed correction bandwidth, and state the *unmeasured* high-frequency band explicitly. If a defensible bound needs higher-bandwidth phase data, obtain that measurement or remove the gate-infidelity claim. A measured quasi-static phase is a frame update, not an infidelity. [CN §7]
- **Motivation:** narrow to direct phase-coherent optical control, free-space clock comparison, and single-photon/single-click protocols whose entangled-state phase carries the path phase; note two-photon schemes are insensitive to the optical carrier/path phase. Align the intro with the local-beamline body. [CN §8]
- **Abbreviations:** define ULE, OLS, GPS, NIST, RH, RSS.

### ☐ Hard boundary — absolute baseline offset
Treat the 1.166×10⁻⁶ absolute discrepancy between data and Mathar as an **unresolved interferometric / anchoring offset** unless an independent absolute calibration shows otherwise. It blocks any absolute-n or "Mathar-is-correct-in-absolute-terms" claim. Any surviving null result concerns the environmental **coefficients** (where the offset cancels), not absolute n. [CN §9]

---

## Ownership, checkpoint, provenance
- **Checkpoint after Tasks 1–2:** Wei presents the reproducible table and validation plots to all three authors. The authors freeze **Outcome A or B** before further editing. Suggested criterion: |α_H^data − α_H^Mathar-surrogate| below 3× combined (statistical + systematic) uncertainty → Outcome B; above → Outcome A, **conditional on Task 3 validating the sensor gain**.
- **Provenance:** every result generated from version-controlled code, with the data snapshot / hash, computational environment, and random seeds recorded.

---

## Two scientifically coherent outcomes
- **Discrepancy survives Tasks 1–4:** the enhancement is real and bulletproofed against the objections a fresh referee will raise — the highlight of a stronger paper.
- **It does not:** reframe around the first long-duration, atom-frequency-referenced differential benchmark of air refractivity at 1762 nm (a priority claim — confirm with a targeted literature check), the ~146k-point open dataset, the measurement architecture, and — pending the offset — a validation of Mathar's environmental *response*. We will assess whether the resulting methodology-and-dataset paper retains sufficient PRApplied significance once the uncertainty audit is complete.

Run Task 1, and we know which paper we are writing.
