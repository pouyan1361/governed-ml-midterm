# BANA 690A Midterm: Written Answers

**Name:**
**Last-name group (A to H, I to P, Q to Z):**
**GitHub username:**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Four tests initially failed:

1. `test_no_zip_like_column` — Detective control that identified ZIP codes remaining in the processed data.
2. `test_no_date_like_column` — Detective control that detected dates of birth remaining in the processed data.
3. `test_no_suspiciously_predictive_column` — Detective control that flagged `adjuster_fraud_review` because its correlation with `claim_free` was 0.845, exceeding the policy threshold of 0.60.
4. `test_policy_agrees_with_data_dictionary` — Detective control that compared the policy against the data dictionary and identified missing PII and leakage protections.

**1.2** I updated `governance/policy.json` by adding `zip` and `date_of_birth` to `pii_columns` and `adjuster_fraud_review` to `leakage_columns`. These changes resolved the four initial failures, and all 11 compliance tests passed.

**1.3** The fix belongs in `governance/policy.json` because the governance policy is the central source of rules defining which columns must be excluded. The existing `src/prepare.py` reads and enforces those rules automatically, so updating the policy maintains consistency without modifying the data preparation code.
---

## Lab 2: Build features from driving history

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Total claims filed during months 1–24 divided by 24. | Drivers with more previous claims may be more likely to file future claims. |
| months_since_last_claim | recency | Subtract the month of the most recent claim from 24, using 25 for drivers with no previous claims. | Drivers who have gone longer without filing a claim may be less likely to file another claim. |
| speeding_velocity | velocity | Divide the speeding-event rate per 1,000 miles during the last six months by the rate over all 24 months plus 0.001. | An increase in recent speeding behavior may indicate higher accident risk. |
| miles_volatility | volatility | Divide the standard deviation of monthly mileage by the average monthly mileage over 24 months. | Large changes in driving activity may indicate inconsistent driving patterns and changing risk exposure. |
| hard_brake_trend | trend | Subtract the hard-braking rate per 1,000 miles in months 1–12 from the rate in months 13–24. | An increasing hard-braking rate may indicate worsening driving behavior and greater claim risk. |

**2.1** The temporal fence test checks that engineered features use only driving history available before the underwriting decision, which is months 1–24. It adds future data from months 25–30 and verifies that the feature values do not change. If a feature failed this test, the model could learn from information that would not be available when evaluating a real applicant, resulting in data leakage, misleading evaluation scores, and unreliable predictions in production.
---

## Lab 3: Hunt the leakage

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | At application | Previous claims history is available before the underwriting decision and can legitimately help predict future claims. |
| renewal_offered | leakage | 0.549 | End of policy year | The renewal decision occurs after the original underwriting decision, so this information would not be available when predicting claim_free. |
| annual_mileage_declared | allowed | 0.280 | At application | Applicants declare their expected annual mileage when applying, making it available at decision time and potentially useful for predicting claim risk. |

**3.1** The correlation test missed `renewal_offered` because its correlation with `claim_free` was 0.549, below the policy threshold of 0.60. However, the column was recorded at the end of the policy year, after the underwriting decision. This demonstrates that low correlation does not necessarily mean a feature is safe. A timeline-based leakage check using the data dictionary's `when_recorded` information can identify this problem even when the statistical correlation test does not flag it.
---

## Lab 4: Run v1 and v2, explain the block

**4.1** I ran both models using `run_pipeline.py`.

- **v1:** Overall AUC = 0.7046. DECISION: PASS. This model may proceed to deployment review.
- **v2:** Overall AUC = 0.7224. DECISION: BLOCKED. This model may NOT be deployed.

**4.2** Although v2 achieved a higher overall AUC, it failed four governance checks: rural subgroup AUC (0.5937), rural subgroup TPR (0.5588), approval disparity ratio (0.5596), and TPR ratio (0.5888). In `data/generate_data.py`, line 136 creates `territory_risk_index` using `42 + 30 * rural + noise`, making it a proxy for geographic location. Line 132 introduces a historical rural penalty through `- 1.10 * rural` in the `claim_free` label. This allows v2 to learn historical geographic bias rather than relying solely on legitimate driving-risk factors.

**4.3** The `no_prohibited_features` check passed because v2 did not directly use a feature listed as prohibited. However, `territory_risk_index` indirectly encodes the protected attribute `area`, so a preventive feature-list check cannot identify the proxy. The detective deployment-gate checks identified the resulting disparities, particularly the approval disparity ratio (0.5596 versus the required 0.80) and TPR ratio (0.5888 versus the required 0.80).

---

## Lab 5: Change the governance

**5.1** I added `min_fpr_ratio` to `governance/policy.json` with a threshold of 0.80. I also updated `src/gate.py` to compare the model's FPR ratio against this threshold and block deployment when it falls below 0.80.

**5.2** I chose 0.80 to maintain consistency with the existing approval disparity and TPR ratio thresholds. A false positive occurs when the model approves a driver for the standard insurance rate even though the driver subsequently files an at-fault claim. This can increase Sierra Mutual's claim costs, while the driver receives an approval based on an incorrect prediction. Unequal FPR across urban and rural drivers is a fairness concern because drivers who actually file claims have different probabilities of receiving the standard rate depending on their area, potentially creating unequal treatment beyond financial consequences.

**5.3** I replaced the skipped test in `tests/test_lab5_gate.py` with `test_gate_blocks_fpr_gap()`. The test uses `fake_metrics()` to simulate an FPR ratio below the policy threshold and verifies that the gate returns `BLOCKED`. It then tests a ratio equal to the threshold and confirms that the gate returns `PASS`. Unlike running the pipeline on a real model, this test deliberately creates both scenarios to verify that the FPR governance control itself operates correctly.

---

## Lab 6: Beat the gate

## Lab 6: Beat the gate

**6.1** My final v3 logistic regression model achieved the following deployment-gate results:

| Metric | Value |
|---|---|
| Overall AUC | 0.7290 |
| Approval disparity ratio | 0.8761 |
| TPR ratio | 0.9415 |
| FPR ratio | 0.9460 |
| DECISION | PASS |

All governance checks passed, including the new FPR-ratio requirement of 0.80. These results were verified using `python run_pipeline.py` and recorded in `artifacts/gate_report.json`.

**6.2** My final model uses four engineered features: `claims_per_month`, `months_since_last_claim`, `speeding_velocity`, and `hard_brake_trend`. Based on feature-ablation experiments using the original 11-feature model, `hard_brake_trend` had the largest observed contribution. Removing it reduced overall AUC from 0.7283 to 0.7240, a decrease of 0.0043. This suggests that changes in hard-braking behavior provide useful predictive information for identifying claim-free drivers.

**6.3** I examined `territory_risk_index` through the provided v2 model, which achieved a higher AUC than v1 (0.7224 versus 0.7046) but was blocked by the governance gate. The feature indirectly encodes rural status, as shown in `data/generate_data.py` (line 136), while the historical label includes an artificial rural penalty (line 132). I did not separately test this feature in my v3 configuration. The v2 results demonstrate that better overall predictive performance does not necessarily make a model deployable when it violates subgroup-performance and fairness requirements.

---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?

**7.2** After approval, what did Stage A print about your governance change? Quote it.

---

## Lab 8 (bonus): Break it and watch it stop

**8.1** What did you change on your second branch, and what did `python run_pipeline.py --config configs/v2.json` print locally?

**8.2** What did Stage A print on GitHub? Quote the refusal line.

**8.3** Which control would NOT have stopped this change on its own, and why do we need both?

---

## Declaration

I completed this exam individually, using only the permitted materials.

**Signature (type your name):**
