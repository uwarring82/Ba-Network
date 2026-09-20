# Step 6 - joint gain-offset envelope

- generated: 2026-09-09T14:02:04Z
- rows: 145784 (subsample=1, quick=False)
- evaluations: 216, seed: 42, elapsed: 37.2 s

## 1. Envelope assumption (unchanged, restated)

| ch | range | span | gamma_max | g_max | |b|_max | b at g_max | uncentred b at g_max | uncentred / spec |
|---|---|---|---|---|---|---|---|---|
| T | [17.5182, 34.6225] | 17.1043 | +0.11693 | 1.1169 | 1.0000 | -0.1252 | +2.9232 | 2.92x |
| H | [18.9356, 45.3206] | 26.3850 | +0.30320 | 1.3032 | 4.0000 | -0.6452 | +9.0961 | 2.27x |
| P | [964.6050, 1006.7743] | 42.1693 | +0.04743 | 1.0474 | 1.0000 | -0.0327 | +46.7165 | 46.72x |

gamma_max = 2*delta/span reproduces the SM endpoint gains exactly, so the envelope assumption is unchanged; only the propagation is. The uncentred hypothesis b = (g-1)*X0 exceeds the stated sensor specification and is kept only as a reference.

## 2. Baseline (g = 1, b = 0)

| ch | d_alpha_read | alpha_data (corrected coord.) |
|---|---|---|
| T | -3.1064e-09 | -8.8474e-07 |
| H | +4.3334e-09 | -1.3152e-08 |
| P | +2.3946e-09 | +2.5949e-07 |

- offset-removed residual RMS: +1.9304e-07 (RI units)
- self-check vs archived full-resolution value (+4.3334e-09): rel. deviation 1.23e-06 [PASS]
- max |identity - propagate|: 8.15e-16

## 3. Worst case over the joint envelope

| response | interval over envelope | E (64 joint vertices) | E (all sampled) | E (linearised) | E/sqrt(3) | SM single-branch | SM / consistent |
|---|---|---|---|---|---|---|---|
| d_alpha_T | [-1.4842e-09, +1.1415e-09] | +1.4842e-09 | +1.4842e-09 | +1.9182e-09 | +8.5691e-10 | +1.0345e-07 | 69.70x |
| d_alpha_H | [-5.7727e-10, +1.0239e-09] | +1.0239e-09 | +1.0239e-09 | +9.1484e-10 | +5.9116e-10 | +3.9878e-09 | 3.89x |
| d_alpha_P | [-2.3242e-10, +1.7437e-10] | +2.3242e-10 | +2.3242e-10 | +2.2541e-10 | +1.3419e-10 | +1.2307e-08 | 52.95x |

E is the half-width of the attained interval for the read-coordinate slope difference. E_vertices is a pure corner evaluation; E_sampled adds edges, random interior draws and local refinement; E_linearised is a first-order estimate from the baseline Jacobian over the bounding box of the parallelogram. E_linearised is NOT guaranteed to bound the maximum: if it falls below E_sampled the response is non-linear and E_sampled is the number to quote. E_vertices and E_sampled use only points INSIDE the feasible envelope; the reference slices below are outside it.


### 3b. Channel-resolved contributions (own-channel vertices, others at identity)

| response | T-only | H-only | P-only | sum (triangle) | joint max | SM endpoint |
|---|---|---|---|---|---|---|
| d_alpha_T | +7.5714e-10 | +6.2977e-10 | +7.7034e-12 | +1.3946e-09 | +1.4842e-09 | +1.0345e-07 |
| d_alpha_H | +2.9276e-10 | +6.5872e-10 | +4.1830e-13 | +9.5189e-10 | +1.0239e-09 | +3.9878e-09 |
| d_alpha_P | +3.7765e-11 | +8.6558e-11 | +9.7351e-11 | +2.2167e-10 | +2.3242e-10 | +1.2307e-08 |

The SM endpoint rescales only the coefficient of the SAME channel. Here the H-only column is the directly comparable consistent-propagated number; the joint maximum is larger because temperature and pressure gain errors also move the humidity coefficient through the shared Ciddor anchor. For a linear response the triangle sum would bound the joint maximum; where the joint maximum exceeds that sum the response is non-linear, consistent with E_linearised falling below E_sampled.

## 4. Attained worst-case calibrations

| response | kind | g_T | b_T | g_H | b_H | g_P | b_P | delta | resid RMS |
|---|---|---|---|---|---|---|---|---|---|
| d_alpha_T | joint_vertex | 0.88307 | +0.1252 | 1.00000 | -4.0000 | 1.00000 | -1.0000 | -1.4842e-09 | +1.9423e-07 |
| d_alpha_H | joint_vertex | 1.00000 | +1.0000 | 0.69680 | +0.6452 | 1.04743 | -0.0327 | +1.0239e-09 | +1.9300e-07 |
| d_alpha_P | joint_vertex | 1.00000 | -1.0000 | 0.69680 | +0.6452 | 1.04743 | -0.0327 | -2.3242e-10 | +1.9283e-07 |

## 5. Reference slices (gain-only hypotheses at the endpoint gain)

These are NOT part of the feasible envelope; they reproduce the SM-style gain-only hypotheses for comparison. `uncentred_endpoint` sets b = (g-1)*X0 and exceeds the sensor specification; `centred_b0_endpoint` assumes exactness at the pivot and also leaves the envelope at g_max for H and T; `feasible_endpoint` is the actual envelope vertex.

| slice | channel | g | b | delta | resid RMS |
|---|---|---|---|---|---|
| uncentred_endpoint | T | 1.11693 | +2.9232 | +1.5475e-09 | +1.9280e-07 |
| centred_b0_endpoint | T | 1.11693 | +0.0000 | +6.2355e-10 | +1.9278e-07 |
| feasible_endpoint | T | 1.11693 | -0.1252 | +5.7632e-10 | +1.9278e-07 |
| uncentred_endpoint | H | 1.30320 | +9.0961 | -3.8550e-10 | +1.9207e-07 |
| centred_b0_endpoint | H | 1.30320 | +0.0000 | -3.5539e-10 | +1.9305e-07 |
| feasible_endpoint | H | 1.30320 | -0.6452 | -3.5325e-10 | +1.9312e-07 |
| uncentred_endpoint | P | 1.04743 | +46.7165 | -8.8571e-11 | +1.9294e-07 |
| centred_b0_endpoint | P | 1.04743 | +0.0000 | -8.8536e-11 | +1.9303e-07 |
| feasible_endpoint | P | 1.04743 | -0.0327 | -8.8536e-11 | +1.9303e-07 |

## 6. Pivot re-centring invariance

Re-centring the same physical hypothesis on a different pivot (X0 = 0) must not change any output; max abs deviations:

- resid_rms: 5.48e-21
- resid_offset: 4.45e-21
- d_alpha_T_read: 7.94e-21
- d_alpha_H_read: 1.46e-22
- d_alpha_P_read: 2.88e-19

## 7. Significance of Delta alpha_H with the revised systematic

- Delta alpha_H = +4.3334e-09
- u_stat (paired bootstrap, from the SM) = +1.3000e-09
- SM u_syst (H) = +2.3000e-09 -> u_comb = +2.6420e-09 -> 1.64 u_comb
- consistent joint envelope u_syst = +5.9116e-10 (E/sqrt3) -> u_comb = +1.4281e-09 -> 3.03 u_comb

The revised systematic uses the joint envelope half-width divided by sqrt(3); the statistical term is unchanged. This quantifies the significance statement, it does not by itself establish a physical effect: the limiting constraints (time dependence, Mathar domain coverage) still have to be carried explicitly.

## 8. Reading

- The envelope assumption is unchanged from the SM; only the propagation through the three branches is made consistent.
- E_sampled and E_linearised should be compared before quoting a bound: if the linearised estimate is at or above the sampled maximum the sampling is adequate; if it is below, the response is non-linear and the sampled maximum is the number to quote.
- A bound small compared with the other budget terms supports the statement "gain is not the limiting systematic", NOT the existence of a physical effect. Carry the limiting constraints (time dependence, Mathar domain coverage) explicitly.
