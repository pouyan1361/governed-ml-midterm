# BANA 690A Midterm: Written Answers

**Name:** Sharon Das
**Last-name group (A to H, I to P, Q to Z):** A to H (recency and extremes)
**GitHub username:** SharonDas99

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).

All four are detective controls: they inspect the processed data itself rather than trusting the policy's lists.
- `test_no_zip_like_column` (detective): found a five-digit code column, `zip`, in the training table.
- `test_no_date_like_column` (detective): found a date column, `date_of_birth`, in the training table.
- `test_no_suspiciously_predictive_column` (detective): `adjuster_fraud_review` correlated 0.845 with the label, above the 0.60 limit.
- `test_policy_agrees_with_data_dictionary` (detective): compared the policy with `data/data_dictionary.csv` and reported "Add to pii_columns: ['zip', 'date_of_birth']. Add to leakage_columns: ['adjuster_fraud_review']."

The seven that passed from the start (for example `test_no_pii_columns`, `test_no_known_leakage_columns`) are list controls: they only check columns the policy already named, so they could not see what the policy forgot.

**1.2** What did you add to `governance/policy.json`, and under which keys?

Under `pii_columns` I added `zip` and `date_of_birth`, which the data dictionary classes as quasi-identifiers. Under `leakage_columns` I added `adjuster_fraud_review`, which the dictionary classes as an outcome recorded "after policy year". I did not change `max_feature_label_correlation`. After the fix the Lab 1 tests show 11 passed, and `git diff --name-only` showed only `governance/policy.json`.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

`src/prepare.py` already enforces whatever the policy lists, so the gap was in the rules, not the code. Keeping the lists in the versioned policy gives one source of truth that the committee owns and CI checks; hard-coding names in the code would create a second, unreviewed copy of the policy.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Total at-fault claims filed in months 1 to 24, divided by 24. | Drivers who filed claims before tend to file again, so a higher rate means a lower chance of a claim-free year. |
| months_since_last_claim | recency | 25 minus the most recent month with a claim; drivers with no claim in the window get 25. | A recent claim signals current risk; a long gap or no claim signals a safer driver. |
| max_hard_brakes_per_1k | extremes | Hard brakes per 1,000 miles computed for each month, then the maximum month per driver. | The worst month captures aggressive or distracted driving that an average can hide. |
| speeding_velocity | velocity | Speeding events per 1,000 miles in the last 6 months divided by the 24-month rate (plus 0.1 to avoid dividing by zero). | A value above 1 means speeding is accelerating recently, which points to rising risk. |
| night_share_mean | ratio | Average share of miles driven at night over months 1 to 24. | Night driving has lower visibility and more fatigue, so a higher share means more exposure to crashes. |
| miles_volatility | volatility | Standard deviation of monthly miles divided by mean monthly miles. | Erratic driving patterns can signal unstable exposure; implemented but not used in the final model. |
| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13 to 24 minus the rate in months 1 to 12. | A positive value means braking behavior is getting worse; implemented but not used in the final model. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The test gives each feature function a history table that also contains months 25 to 30 (the policy year) filled with absurd values, and checks that the output does not change. It passes only because every function calls `as_of(history)` first, which keeps months 1 to 24, the information that actually exists on the decision date. If a feature had failed it, the model would have been trained on information from the future: test scores would look better than reality, and in production, where months 25 to 30 do not exist yet at decision time, the feature would be wrong or missing and the model would underperform.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | Below 0.60, and the dictionary says it counts claims in the 3 years BEFORE the history window, so it is known at the decision. It is filled unevenly (fill_pos 0.146, fill_neg 0.350) only because drivers with no prior claims have nothing to record, which is a real risk signal, not leakage. |
| renewal_offered | leakage | 0.549 | end of policy year | Below the 0.60 correlation limit, but the timeline test fails: Sierra decides renewal at the END of the policy year, after the claim outcome is known, so it partly encodes the label. It is also filled very unevenly (fill_pos 0.959, fill_neg 0.500). Added to `leakage_columns`. |
| annual_mileage_declared | allowed | 0.280 | at application | Below 0.60, filled almost equally for both classes (0.970 vs 0.966), and declared by the applicant on the application form, so it exists at decision time. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

`renewal_offered` correlates only 0.549 with `claim_free`, under the 0.60 limit, because renewal depends on other business factors too, so the outcome is diluted rather than copied. A correlation test only measures how strongly a column predicts the label; it cannot see WHEN the column was created. The timeline test catches it: `data/data_dictionary.csv` records it as "end of policy year", after the decision, so it cannot exist when Sierra makes the underwriting decision, no matter how weak or strong the correlation is.

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

- v1: overall AUC 0.7046. `DECISION: PASS. This model may proceed to deployment review.` Rural approval 0.7749, rural TPR 0.8647; disparity ratio 0.8657, TPR ratio 0.9170, FPR ratio 0.9427.
- v2: overall AUC 0.7224. `DECISION: BLOCKED. This model may NOT be deployed.` Rural approval 0.5146, rural TPR 0.5588; disparity ratio 0.5596, TPR ratio 0.5888. Failed checks: `subgroup_auc[rural]` 0.5937, `subgroup_tpr[rural]` 0.5588, `approval_disparity_ratio` 0.5596, `tpr_ratio` 0.5888 (and, after Lab 5, `fpr_ratio` 0.5765).

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

v2 adds one feature compared with v1, `territory_risk_index`, which `data/data_dictionary.csv` lists as supplied by a third-party vendor.
- Line 136: `territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)`. The index is built mostly from the rural flag plus noise, so it is a stand-in for area.
- Line 132: `logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)`. The historical label subtracts 1.10 for rural drivers regardless of how they drive, which is the biased underwriting baked into `claim_free`.

Together, the model uses the proxy to learn the rural penalty back: AUC rises to 0.7224, but rural approval falls from 0.7749 to 0.5146 and the disparity ratio falls to 0.5596, so the gate blocks it.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

`no_prohibited_features` only compares feature NAMES with the banned list (area, gender, zip, date_of_birth, and so on). `territory_risk_index` is not on that list, so it passes, even though it carries the same information as `area`. Only checks on OUTCOMES by group can see the effect: `approval_disparity_ratio` (0.5596 vs 0.80), `tpr_ratio` (0.5888 vs 0.80), `subgroup_tpr[rural]` (0.5588 vs 0.70) and `subgroup_auc[rural]` (0.5937 vs 0.64) all failed in `artifacts/gate_report.json`.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I added `"min_fpr_ratio": 0.80` to `governance/policy.json` and changed `policy_version` from "1.0" to "1.1". In `src/gate.py` I added a conditional `fpr_ratio` check that only runs when the key is present.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 before running any model with it, so it matches the four-fifths standard the policy already uses for approval disparity and TPR ratio rather than fitting a model. A false positive means Sierra approved at the standard rate a driver who then filed an at-fault claim: Sierra loses money on an underpriced policy. Unequal FPR is also a fairness problem: if one area's risky drivers get the benefit of the doubt far more often than the other's, the stricter group is held to a harsher standard for the same behavior and pays more through manual review, which is unequal treatment, not only a pricing loss.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

`test_gate_blocks_fpr_gap` builds fake metrics with an `fpr_ratio` 0.10 below `POLICY["min_fpr_ratio"]` and asserts the gate returns BLOCKED, then builds metrics exactly at the threshold and asserts PASS. A pipeline run only shows the gate's behavior on one real model, which might never come near the threshold; the test proves the check actually fires on a bad value and allows a good one, so the control works on any future model. With it, `tests/test_lab5_gate.py` shows 5 passed, 0 skipped.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

Model v3, policy v1.1, logistic regression, threshold 0.5:
- overall AUC 0.8217 (minimum 0.68)
- approval_disparity_ratio 0.8659 (0.80)
- tpr_ratio 0.9841 (0.80)
- fpr_ratio 0.9304 (0.80)
- subgroup AUC rural 0.8016 / urban 0.8332; subgroup TPR rural 0.9059 / urban 0.9205
- `DECISION: PASS. This model may proceed to deployment review.`

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

I used four engineered features: `months_since_last_claim` (recency), `max_hard_brakes_per_1k` (extremes), `speeding_velocity` (velocity) and `night_share_mean` (ratio), on top of the six declared fields. `max_hard_brakes_per_1k` mattered most. I tested it by removing one feature at a time and rerunning: without `max_hard_brakes_per_1k` AUC fell from 0.8217 to 0.7543; without `night_share_mean` it fell to 0.8043; without `speeding_velocity` to 0.8196; without `months_since_last_claim` it stayed at 0.8217.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Yes. Adding `territory_risk_index` to my final features raised AUC from 0.8217 to 0.8447, but the gate BLOCKED it: `approval_disparity_ratio` fell to 0.6654 and `fpr_ratio` to 0.6332, both below 0.80. My own Lab 5 check was one of the two that caught it. A better model by AUC is not a deployable model: the extra accuracy came from a proxy for area that reproduces the historical rural penalty, so I removed it rather than lowering a threshold.

---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?

It is a preventive human-approval control on running code from a fork. Owner: the repository owner (the instructor, as the accountable reviewer). Trigger: every pull request from a fork, before any workflow runs. Evidence: the GitHub Actions approval record showing who approved the run and when, followed by the workflow logs and the uploaded governance evidence.

**7.2** After approval, what did Stage A print about your governance change? Quote it.

Stage A (`ci/check_policy_integrity.py`) listed `governance/policy.json`, `src/gate.py` and `tests/test_lab5_gate.py` under "GOVERNANCE CHANGE DETECTED (routed to policy owner for review)", with "protections added: pii_columns gained ['date_of_birth', 'zip']; leakage_columns gained ['adjuster_fraud_review', 'renewal_offered']; new threshold min_fpr_ratio = 0.8", and ended: "Governance change is a tightening or an addition. Allowed, pending owner review. Integrity check passed." My change only tightened or added controls, so it was allowed but still routed to the policy owner.

---

## Lab 8 (bonus): Break it and watch it stop

**8.1** What did you change on your second branch, and what did `python run_pipeline.py --config configs/v2.json` print locally?

On `student/sharon-das-cheat` I set `min_approval_disparity_ratio`, `min_subgroup_tpr`, `min_tpr_ratio` and `min_fpr_ratio` to 0.50 and `min_subgroup_auc` to 0.55 in `governance/policy.json`. Locally, v2 then passed every check (rural AUC 0.5937 vs 0.55, rural TPR 0.5588 vs 0.50, disparity 0.5596 vs 0.50, TPR ratio 0.5888 vs 0.50, FPR ratio 0.5765 vs 0.50) and printed "DECISION: PASS. This model may proceed to deployment review." Nothing on my own machine stopped the biased model.

**8.2** What did Stage A print on GitHub? Quote the refusal line.

"REFUSED: this pull request LOOSENS governance:" followed by "min_subgroup_auc LOOSENED from 0.64 to 0.55", "min_subgroup_tpr LOOSENED from 0.7 to 0.5", "min_approval_disparity_ratio LOOSENED from 0.8 to 0.5", "min_tpr_ratio LOOSENED from 0.8 to 0.5", and "A model author may tighten a control or add one. Loosening needs the AI Risk Committee, in its own pull request." (min_fpr_ratio did not appear as loosened because it is a new key compared with main, so it was reported as an addition.)

**8.3** Which control would NOT have stopped this change on its own, and why do we need both?

The deployment gate (`src/gate.py`) would not have stopped it on its own: the gate reads its thresholds from the policy file, so if the author lowers the thresholds, the gate faithfully passes the biased v2 model. The integrity check in CI Stage A compares the policy with main and refuses any loosening, enforcing separation of duties so the person building the model cannot change the rules that judge it. We need both: the gate judges the model against the rules, and the integrity check protects the rules themselves; either one alone can be defeated.

---

## Declaration

I completed this exam individually, using only the permitted materials.

**Signature (type your name):** Sharon Das

Dr. Eslami announced in class today, October 19, 2026, that GitHub is permitted.
