# BANA 690A Midterm: Written Answers

**Name:** Vanessa 
**Last-name group (A to H, I to P, Q to Z):** Ojeda-Coogan
**GitHub username:** Vanessaojeda-coogan

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
1. `test_no_zip_like_column` detected the `zip` column. This was a detective control because it examined the actual data values.
2. `test_no_date_like_column` detected the `date_of_birth` column. This was a detective control because it examined the actual data values.
3. `test_no_suspiciously_predictive_column` detected `adjuster_fraud_review`, which had a correlation of 0.845 with the label. This was a detective control because it analyzed the data and label relationship.
4. `test_policy_agrees_with_data_dictionary` found missing identifier/quasi-identifier and outcome protections. This was a detective control because it compared the policy against the data dictionary.

All four initially failing tests were detective controls. The list controls passed because they checked protections that were already listed in the policy.

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added `zip` and `date_of_birth` to the `pii_columns` list in `governance/policy.json`. I added `adjuster_fraud_review` to the `leakage_columns` list because it was recorded after the policy decision and had an unusually high correlation with the label.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
The fix belongs in the policy because `src/prepare.py` enforces the governance rules but should not contain individual decisions about which fields are sensitive or leaky. Keeping the fix in the policy makes the rule explicit, reviewable, and reusable by the pipeline and its tests.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Total claims filed during the 24 months divided by DECISION_MONTH. | A history of more claims suggests higher future claim risk, so it should be negatively related to claim_free. |
| speeding_velocity | velocity | Recent speeding events per 1,000 miles divided by whole-history speeding events per 1,000 miles, with 0.1 added to the denominator. | Increasing speeding behavior may indicate worsening driving risk and a lower chance of being claim-free. |
| miles_volatility | volatility | The standard deviation of monthly miles divided by the average monthly miles. | Large changes in monthly driving exposure may indicate less stable driving patterns and different levels of claim exposure. |
| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13–24 minus hard brakes per 1,000 miles in months 1–12. | An increase in hard braking may indicate worsening driving behavior and greater claim risk. |
| night_share_mean | ratio | The average share of miles driven at night across the 24 months. | More night driving may involve lower visibility and greater driving risk, which could reduce the likelihood of being claim-free. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The temporal fence test checks that every feature uses only driving-history records available before the underwriting decision. The test adds months 25–30 with extreme values and confirms that the feature results do not change. If a feature failed this test, the model would be using information from after the decision, creating data leakage. In production, the model would not have access to those future values when making a real application decision, so the model’s testing performance would appear better than its real-world performance. The model could therefore make incorrect approval decisions.
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | It was available before the decision, and its correlation was below the 0.60 limit. |
| renewal_offered | leakage | 0.549 | end of policy year | It was recorded after the original underwriting decision, so it uses future information even though its correlation was below 0.60. |
| annual_mileage_declared | allowed | 0.280 | at application | It was available when the application decision was made, and its correlation was below the 0.60 limit. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
A numeric correlation test can miss leakage when a post-decision field does not have a correlation above the chosen threshold. `renewal_offered` had a correlation of only 0.549, below the 0.60 limit, so the correlation test did not identify it as suspicious. The timeline test caught it because the data dictionary showed that it was recorded at the end of the policy year, after the underwriting decision.

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
v1
overall AUC 0.7046 
DECISION: PASS

v2
overall AUC 0.7224
DECISION: BLOCKED

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

V2 has the higher overall AUC, but it is blocked because its fairness results are much worse for rural drivers. It fails the rural subgroup AUC, rural subgroup TPR, approval disparity ratio, and TPR ratio checks.


The line that creates the "territory_risk_index" is:
territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1) 

The line that creates the rural penatly is:
logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

V2 passed `no_prohibited_features` because the preventive check only looks for feature names that are explicitly prohibited. The configuration did not include the protected feature `area`, so the name-based check allowed `territory_risk_index`. However, `territory_risk_index` acts as a proxy because it is higher for rural drivers. 

The detective outcome checks caught the problem. V2 failed the rural subgroup AUC, rural subgroup TPR, approval disparity ratio, and TPR ratio checks. These checks examined the model’s actual outcomes and showed that rural drivers were treated much worse, even though the feature name itself did not look prohibited.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added the policy key `"min_fpr_ratio"` and set its value to `0.75`.


**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
I chose 0.75 because it requires the lower group FPR to be at least 75% of the higher group FPR. A false positive occurs when a driver who eventually files a claim is incorrectly approved, which can cause Sierra Mutual to experience unexpected claim losses. Unequal FPR is also a fairness problem because one group’s risky drivers may be approved more often while another group’s risky drivers are more likely to be declined or sent to manual review.


**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
I wrote a test that creates fake metrics with an FPR ratio below the threshold and confirms that the gate returns `BLOCKED`. The test also sets the FPR ratio exactly equal to the threshold and confirms that the gate returns `PASS`. This proves that the new check works at both sides of the boundary and uses the intended `>=` rule. Running the pipeline once only shows what happened for one model and one set of metrics; the test proves that the gate reacts correctly to known good and bad inputs.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

| Check | Value | Threshold | Result |
|---|---:|---:|---|
| Overall AUC | 0.7588 | 0.68 | Pass |
| Approval disparity ratio | 0.8687 | 0.80 | Pass |
| TPR ratio | 0.9540 | 0.80 | Pass |
| FPR ratio | 0.9444 | 0.75 | Pass |
| Decision | PASS | — | The model may proceed to deployment review |

**6.2** Which engineered features did you use, and which one mattered most? How do you know?
My final model used four engineered features: `claims_per_month`, `speeding_velocity`, `hard_brake_trend`, and `night_share_mean`. I determined which features mattered by removing one feature at a time and rerunning the pipeline. Removing `night_share_mean` caused the largest AUC decrease, from 0.7579 to 0.7368, a decrease of 0.0211, so it mattered most. Removing `miles_volatility` slightly improved the AUC from 0.7579 to 0.7588, so I left it out of the final model.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
I tried adding `territory_risk_index`. The overall AUC increased from 0.7579 to 0.7811, but the model became blocked. The approval disparity ratio fell to 0.6352, the TPR ratio fell to 0.7786, and the FPR ratio fell to 0.5476. This shows that a model can have better overall predictive performance but still be unsuitable for deployment if it creates unacceptable fairness disparities.

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
