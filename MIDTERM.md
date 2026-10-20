# BANA 690A Midterm: Written Answers

**Name: Manchi Hsu
**Last-name group (A to H, I to P, Q to Z): B
**GitHub username: ManchiHsu

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
FAILED test_no_zip_like_column 
FAILED test_no_date_like_column 
FAILED test_no_suspiciously_predictive_column
FAILED test_policy_agrees_with_data_dictionary 

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added zip and date_of_birth to pii_columns,and adjuster_fraud_review to leakage_columns in `governance/policy.json`. After these change, all 11 Lan 1 tests passed

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
`src/prepare.py` already filters columns according to the policyl. The problem was missing entries in `governance/policy.json` , so completing the policy fixes the issue without changeing the enforcement code
---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Sum claims in months 1–24 and divide by 24. | More prior claims may indicate a lower chance of being claim-free. |
| months_since_last_claim | recency | Calculate 25 minus the latest prior claim month; use 25 if no claims occurred. | A longer gap since the last claim may indicate lower risk. |
| miles_volatility | volatility | Divide each driver's standard deviation of monthly miles by their mean monthly miles. | Greater mileage variation may indicate less consistent driving exposure. |
| max_hard_brakes_per_1k | extremes | Calculate hard brakes per 1,000 miles for each month, then take each driver's maximum. | A higher peak braking rate may indicate riskier driving. |
| night_share_mean | ratio | Calculate each driver's mean night_miles_share over months 1–24. | More nighttime driving may indicate greater accident risk. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The temporal fence test adds months 25–30 and checks that the engineered features remain unchanged. Each function uses as_of(history) to keep only months 1–24. If a feature failed this test, it would use future information unavailable at application time, making evaluation results unreliable and potentially hurting production performance.
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | Prior claims are historical information available when the application is evaluated. |
| renewal_offered | leakage | 0.549 | end of policy year | The renewal decision is recorded after the application decision and is unavailable at prediction time. |
| annual_mileage_declared | allowed | 0.280 | at application | Declared annual mileage is available at application time. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
renewal_offered is leakage even though its correlation of 0.549 is below the 0.60 threshold. A correlation test can miss future information that is not strongly correlated with the label. The timeline test catches it because data/data_dictionary.csv records this field at the end of the policy year, after the application decision.
---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

v1: Overall AUC = 0.7046.
DECISION: PASS. This model may proceed to deployment review.

v2: Overall AUC = 0.7224.
DECISION: BLOCKED. This model may NOT be deployed.
**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

In data/generate_data.py, line 136 creates territory_risk_index using +30 * rural, making the index a proxy for area. Line 132 creates the label's rural penalty through -1.10 * rural in the logit. v2 can learn this historical bias through the proxy. Although its overall AUC increases to 0.7224, it is blocked because rural AUC, rural TPR, approval disparity ratio, and TPR ratio fall below policy thresholds.
**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

The preventive no_prohibited_features check only checks feature names against the prohibited list. territory_risk_index is not listed, so it passes even though it indirectly reveals area. The detective approval_disparity_ratio and tpr_ratio checks catch the unequal outcomes, while subgroup_auc and subgroup_tpr also fail for rural drivers.
---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I added min_fpr_ratio = 0.80 to governance/policy.json and updated policy_version from 1.0 to 1.1.
**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 to require the lower group FPR to be at least 80% of the higher group FPR. A false positive approves a driver who files a claim, exposing Sierra Mutual to underpriced risk while giving that driver the standard rate. Unequal FPR means drivers who file claims receive different levels of leniency depending on their area, creating unfair treatment as well as financial risk.
**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

In tests/test_lab5_gate.py, test_gate_blocks_fpr_gap uses fake_metrics with otherwise passing values. It verifies that an FPR ratio of 0.70 is BLOCKED and a ratio exactly at 0.80 PASSES. Unlike one pipeline run, this test checks both rejection and the exact acceptance boundary independently of a trained model.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

Final model: logistic regression with 11 features and decision threshold 0.5, under policy v1.1.

overall_auc: 0.8198
approval_disparity_ratio: 0.8775
tpr_ratio: 0.9922
fpr_ratio: 0.9295
DECISION: PASS

All deployment checks passed in the final pipeline run.
**6.2** Which engineered features did you use, and which one mattered most? How do you know?

I used claims_per_month, months_since_last_claim, miles_volatility, max_hard_brakes_per_1k, and night_share_mean. Removing max_hard_brakes_per_1k while keeping the other settings unchanged reduced AUC from 0.8198 to 0.7397, a drop of 0.0801. This demonstrates a substantial contribution, although I did not remove every other feature individually to establish a complete ranking.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Adding territory_risk_index increased AUC from 0.8198 to 0.8421, but the model was BLOCKED: approval_disparity_ratio fell to 0.6460 and fpr_ratio to 0.5855, both below 0.80. Higher overall predictive performance does not guarantee acceptable fairness. I removed the index and retained the passing model.

---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?

This is a preventive approval control. The owner is the repository maintainer, pouyan1361. The trigger is a pull request from a fork requesting a workflow run. Evidence is the “1 workflow awaiting approval” status and the approval record in GitHub Actions once approved.
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
