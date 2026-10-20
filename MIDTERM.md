# BANA 690A Midterm: Written Answers

**Name:Zhihao Xia
**Last-name group (A to H, I to P, Q to Z):Q to Z
**GitHub username:Xavier980711

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).

All four failures were detective controls, because each one inspects the data itself rather than a list in the policy:
- `test_no_zip_like_column`: detective (caught a five-digit code column, `zip`)
- `test_no_date_like_column`: detective (caught a date column, `date_of_birth`)
- `test_no_suspiciously_predictive_column`: detective (caught `adjuster_fraud_review`, correlated with the label above 0.60)
- `test_policy_agrees_with_data_dictionary`: detective (compared the policy to `data/data_dictionary.csv` and listed the columns it forgot)

The list controls (`test_no_pii_columns`, `test_no_known_leakage_columns`) passed from the start. They only check what the policy already wrote down, so they could not catch what it missed.

**1.2** What did you add to `governance/policy.json`, and under which keys?

I added `"zip"` and `"date_of_birth"` to `pii_columns`, because `data/data_dictionary.csv` classes both as quasi-identifier. I added `"adjuster_fraud_review"` to `leakage_columns`, because the dictionary classes it as outcome, recorded "after policy year". I did not change `max_feature_label_correlation`; it stays at 0.60.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

`src/prepare.py` already enforces whatever the policy lists, so the gap was in the policy, not the code. Fixing the policy keeps one source of truth that the Model Risk Officer owns and CI Stage A reviews, and it applies to every future run. Patching the code, or weakening a test, would hide the decision from governance.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.


| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Sum of claim_filed over months 1 to 24, divided by 24. | Drivers who filed claims often in the past are more likely to file again. |
| months_since_last_claim | recency | 25 minus the most recent month with claim_filed == 1, or 25 if the driver never claimed. | A recent claim signals current risk; a long gap or no claim suggests a safer driver. |
| speeding_velocity | velocity | Speeding events per 1,000 miles in the last 6 months, divided by (the 24-month speeding rate per 1,000 miles + 0.1). | A value above 1 means speeding is accelerating recently, a sign of rising risk. |
| miles_volatility | volatility | Standard deviation of monthly miles divided by mean monthly miles over 24 months. | Erratic mileage reflects unstable driving exposure and habits. |
| max_hard_brakes_per_1k | extremes | Hard brakes per 1,000 miles computed for each month, then the maximum per driver. | The worst month captures risky episodes that an average would hide. |
| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13 to 24 minus the same rate in months 1 to 12. | A positive value means braking behavior is getting worse over time. |
| night_share_mean | ratio | Average night_miles_share per driver over the 24 months. | Night driving means lower visibility and more fatigue, so a higher share means more claims. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The temporal fence test (`test_temporal_fence_no_future_data` in `tests/test_lab2_features.py`) appends fake months 25 to 30 with absurd values: 500 hard brakes, 500 speeding events, and a claim every month. It then checks that no feature value changes. If one did change, that feature used data from after the decision date, which is leakage. Such a model would look very accurate in testing because it is peeking at the policy year. In production those months don't exist yet when the applicant applies, so the feature would be computed differently and the model's performance would collapse. Every function in `src/features.py` calls `as_of()` first, so all 7 features pass the fence.---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | Comes from the industry claims database and covers the 3 years BEFORE the history window, so it was known at the decision. Real past behavior, not future information. |
| renewal_offered | leakage | 0.549 | end of policy year | Sierra decides renewal after seeing the policy year's claims, so the column encodes the outcome. It is filled for 95.9% of claim-free drivers but only 50% of claim filers (`src/leakage_checks.py`). It cannot exist at application time. |
| annual_mileage_declared | allowed | 0.280 | at application | Declared by the applicant on the application form before the decision. Fill rates are balanced (0.970 vs 0.966), so there is no one-class pattern. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

`renewal_offered` has a correlation of 0.549, below the 0.60 limit, so the "too good" correlation test clears it. Correlation measures how strong a relationship is, not when the data was recorded, so a column from the future can still look only moderately predictive. The timeline test catches it: `data/data_dictionary.csv` says it was recorded at the "end of policy year", after the decision, so it cannot be used however modest its correlation. I ruled it leakage in `column_rulings` and added it to `leakage_columns` so the pipeline actually drops it.

---

## Lab 4: Run v1 and v2, explain the block
**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

- v1: overall AUC 0.7046. `DECISION: PASS. This model may proceed to deployment review.`
- v2: overall AUC 0.7224. `DECISION: BLOCKED. This model may NOT be deployed.`
  Failed checks: subgroup_auc[rural] 0.5937 (< 0.64), subgroup_tpr[rural] 0.5588 (< 0.70), approval_disparity_ratio 0.5596 (< 0.80), tpr_ratio 0.5888 (< 0.80).
- Rural approval fell from 0.7749 (v1) to 0.5146 (v2), and rural TPR fell from 0.8647 to 0.5588, while urban approval rose from 0.8951 to 0.9196.

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

v2 adds one feature, `territory_risk_index`, which `data/data_dictionary.csv` lists as supplied by a third-party vendor.
- Line 136: `territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)`. The index is almost entirely the rural flag plus noise, so it works as a stand-in for `area`.
- Line 132: `logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)`. The historical label subtracts 1.10 for every rural driver regardless of how they drive, which is the unjustified penalty.

Together, the model uses the index to learn the rural penalty back. Its AUC rises because it reproduces the biased label, not because it predicts driving risk better. Claim-free rural drivers are then approved far less often (rural TPR 0.5588), so the gate blocks it.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

`no_prohibited_features` is a preventive check that only compares feature NAMES against the `prohibited_features` list in `governance/policy.json`. `territory_risk_index` is not on that list, so it passed, even though the column carries the same information as `area`. A proxy is defined by what it does, not by its name, so only checks on OUTCOMES per group can see it. The detective checks that blocked v2 were `subgroup_auc[rural]`, `subgroup_tpr[rural]`, `approval_disparity_ratio` and `tpr_ratio`: they measured the model's results for rural vs urban drivers and found the gap.
---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I added `"min_fpr_ratio": 0.80` to `governance/policy.json` and changed `policy_version` from "1.0" to "1.1". In `src/gate.py`, under the "# 5. LAB 5" comment, I added a conditional `fpr_ratio` check that only runs when that key is present.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 because it matches the four-fifths screen the policy already uses for `min_approval_disparity_ratio` and `min_tpr_ratio`, so the false-positive side of the error is held to the same standard as the true-positive side. The value comes from that principle, not from what a particular model scores. A false positive is a driver who did file an at-fault claim but was approved at the standard rate. For Sierra Mutual that is an underpriced policy and a direct loss. When FPR differs by area, equally risky drivers are treated differently because of where they live. In v2 the urban FPR is 0.8168 but the rural FPR is only 0.4709 (fpr_ratio 0.5765): risky urban drivers get the benefit of the doubt while risky rural drivers are sent to manual review at a higher rate. Rural drivers are held to a stricter standard, which is a fairness harm on top of the profit problem.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

`test_gate_blocks_fpr_gap` builds fake metrics where every other check passes and only `fpr_ratio` changes. It asserts that `threshold - 0.10` is BLOCKED and that exactly the threshold is PASS. This proves the check itself works: it fires below the threshold, and the boundary is `>=`. A single pipeline run cannot show that, because v2 is already blocked by four other checks, so its run doesn't prove the FPR check alone would stop a model. The test also runs on every push in CI, so if someone later removes or breaks the check, the build fails.

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

| check | value | threshold | result |
|---|---|---|---|
| no_prohibited_features | none | none | pass |
| overall_auc | 0.8219 | 0.68 | pass |
| subgroup_auc[rural] | 0.8009 | 0.64 | pass |
| subgroup_tpr[rural] | 0.9059 | 0.70 | pass |
| subgroup_auc[urban] | 0.8334 | 0.64 | pass |
| subgroup_tpr[urban] | 0.9220 | 0.70 | pass |
| approval_disparity_ratio | 0.8742 | 0.80 | pass |
| tpr_ratio | 0.9825 | 0.80 | pass |
| fpr_ratio | 0.8906 | 0.80 | pass |

`DECISION: PASS. This model may proceed to deployment review.` (model v3, policy v1.1)

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

The final model uses four engineered features: `claims_per_month` (frequency), `speeding_velocity` (velocity), `max_hard_brakes_per_1k` (extremes) and `night_share_mean` (ratio). It uses them with logistic regression on the six declared fields. `max_hard_brakes_per_1k` mattered most. When I removed it and reran, overall AUC fell from 0.8219 to 0.7556, by far the largest drop, and the run is recorded in `artifacts/audit_log.jsonl`. Using all seven engineered features gave 0.8212, slightly lower than these four, so the other three added nothing and I left them out to keep the model simpler.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Yes. Adding `territory_risk_index` raised overall AUC from 0.8212 to 0.8449, but the gate BLOCKED it. `approval_disparity_ratio` fell to 0.6525 and `fpr_ratio` to 0.6010, both below 0.80, and rural approval dropped to 0.5643 against 0.8648 for urban drivers. The AUC went up because the index is mostly the rural flag (`data/generate_data.py` line 136), which lets the model relearn the biased rural penalty built into the label (line 132). A higher AUC only means closer agreement with a biased historical label. A deployable model must also meet the policy for every group. I did not lower `min_fpr_ratio` to let it through, because that would be fitting the control to the model.
---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?

It is a preventive, human-in-the-loop approval control enforcing separation of duties: code from a fork cannot run in the repository's CI until someone with authority approves it. Owner: the repository owner (the instructor / policy owner), not the model author. Trigger: a pull request from a fork to `pouyan1361/governed-ml-midterm` main, which pauses the Governance Gate workflow. Evidence: GitHub records who approved the run and when, and the workflow log plus the uploaded `governance-evidence` artifacts (gate report, model card, audit log) are kept with the pull request.

**7.2** After approval, what did Stage A print about your governance change? Quote it.

Stage A printed:
"GOVERNANCE CHANGE DETECTED (routed to policy owner for review): governance/policy.json, src/gate.py, tests/test_lab5_gate.py. protections added: pii_columns gained ['date_of_birth', 'zip']; leakage_columns gained ['adjuster_fraud_review', 'renewal_offered']; new threshold min_fpr_ratio = 0.8. Governance change is a tightening or an addition. Allowed, pending owner review. Integrity check passed."
My changes only added protections, so the integrity check reported them for owner review and let the pull request continue to Stages B and C.

---

## Lab 8 (bonus): Break it and watch it stop

**8.1** What did you change on your second branch, and what did `python run_pipeline.py --config configs/v2.json` print locally?

On branch `student/zhihao-xia-cheat` I lowered `min_approval_disparity_ratio`, `min_subgroup_tpr`, `min_tpr_ratio` and `min_fpr_ratio` to 0.50 and `min_subgroup_auc` to 0.55 in `governance/policy.json`. Locally, v2 then printed `DECISION: PASS. This model may proceed to deployment review.` Every check passed: for example subgroup_auc[rural] 0.5937 vs 0.55, approval_disparity_ratio 0.5596 vs 0.50, and fpr_ratio 0.5765 vs 0.50. Nothing on my own machine stopped the biased model.

**8.2** What did Stage A print on GitHub? Quote the refusal line.

"REFUSED: this pull request LOOSENS governance:
  - min_subgroup_auc LOOSENED from 0.64 to 0.55
  - min_subgroup_tpr LOOSENED from 0.7 to 0.5
  - min_approval_disparity_ratio LOOSENED from 0.8 to 0.5
  - min_tpr_ratio LOOSENED from 0.8 to 0.5
A model author may tighten a control or add one. Loosening needs the AI Risk Committee, in its own pull request."

**8.3** Which control would NOT have stopped this change on its own, and why do we need both?

The deployment gate (`src/gate.py`, run by the pipeline and in Stage C) would not stop it on its own. It compares the model's metrics against whatever thresholds the policy says, so once the policy is loosened it approves the biased v2 model. The gate controls the model; Stage A controls the policy, so the person being judged cannot rewrite the rules. That is separation of duties. Stage A alone is not enough either: it never evaluates the model, and it only compares against the base branch. My `min_fpr_ratio` drop to 0.50 was reported only as "new threshold min_fpr_ratio = 0.5", not as a loosening, because the base policy has no such key. Owner review through CODEOWNERS is the extra layer that catches that.

---

## Declaration

I completed this exam individually, using only the permitted materials.

**Signature (type your name):Zhihao Xia
