# BANA 690A Midterm: Written Answers

**Name: Madison Metz**
**Last-name group (A to H, I to P, Q to Z):M**
**GitHub username:madisonmetz637**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
The four tests that failed were ZIP-like quasi-identifier (zip), Date-like quasi-identifier (date of birth), correlation test (adjuster_fraud_review), and policy completeness test. All of these control types are detective. 

**1.2** What did you add to `governance/policy.json`, and under which keys?
In governance/policy.json, I added the following:
pii_columnns: "zip", "date_of_birth"
leakage_columns: "adjuster_fraud_review"

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
It is not src/prepare.py because it already removes every column the policy gives. If we fix it in governance/policy.json, we will keep one source of truth. If we hardcode column names, prepare.py would create a second, unreviewed copy. Completing the policy is the durable fix since it turns this one-time catch into a permanent, versioned rule that Stage A won’t let anyone remove, and it leaves the detective controls at full strength for the next column nobody listed, whereas weakening the test or patching the code would just hide the alert.
---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Total at-fault claims filed in months 1–24 divided by 24. | Drivers who filed claims before are more likely to file again, so a higher rate means a lower chance of a claim-free year. |
| speeding_velocity | velocity | Speeding events per 1,000 miles in the last 6 months divided by speeding events per 1,000 miles over all 24 months (plus 0.1 so a zero baseline can't make it infinite). | A value above 1 means speeding is accelerating recently, a sign that risk is rising right before the policy starts. |
| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13–24 minus hard brakes per 1,000 miles in months 1–12. | A positive value means braking habits are getting worse over time, which points to more near-misses and a higher claim risk. |
| max_hard_brakes_per_1k | extremes | Hard brakes per 1,000 miles computed for each month, then the highest single month per driver. | One very bad month reveals dangerous episodes that a 24-month average would hide. |
| night_share_mean | ratio | The average share of each driver's monthly miles driven at night. | Night driving has lower visibility and more fatigue, so drivers who do more of it face a higher crash risk. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
If a feature had failed my model in production, it means the model would have learned from data that does not exist yet when a decision is made. In test, it can see in the future which is why it is more accurate. On the other hand, in production, that future data would be missing or different for each applicant.
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning 

| prior_claims_3y | allowed | 0.243 | at application | Counts at-fault claims from the 3 years before the history window, pulled from the industry claims database, so it is known when the underwriter decides. It is strongly related to the label, but strong is not the same as leakage. |
| renewal_offered | leakage | 0.549 | end of policy year | Sierra decides renewal at the end of the term, after it already knows whether the driver filed a claim. It is filled for 95.9% of claim-free drivers vs 50.0% of claimers, so it is close to a copy of the label. It passed the 0.60 correlation test only because a numeric test cannot see time. |
| annual_mileage_declared | allowed | 0.280 | at application | Declared by the applicant on the application form, before the decision. Fill rates are nearly identical for both classes (0.970 vs 0.966), so there is no sign it was filled based on the outcome. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

It was found that renewal_offered is leakage even though it did not trip the correlation test. A numeric test can miss this because its correlation with claim_free is .0549 and that is below the .60 limit. Therefore, the correlation test passes. A numeric test can only measure how strongly a column moves with the label. It can't tell when the column was recorded. Therefore, a leaky model that is only slightly correlated will slip through. A timeline test would catch this because it would compare each column's when_recorded in data/data_dictionary.csv.
---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
v1: DECISION line: PASS. This model may proceed to deployment review.
overall AUC: 0.7046
v2: DECISION line: BLOCKED. This model may NOT be deployed.
overall AUC: 0.7224

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

v2 adds overall blocked because it's extra accuracy comes from a proxy for area, not from better risk prediction. The exact line in data/generate_data.py that creates territory_risk_index is Line 136 territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)

Line 132 logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n) creates the label's rural penalty.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

A preventative list check cannot catch a proxy because it only checks the comparison between feature names in the config against the policy prohibited_features list. The detective check that did catch a proxy is approval_disparity_ratio which compares rural and urban approval rates.
---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

Added the policy key min_fpr_ration to governance/policy.json with the value 0.80. Additionally, I added the matching fpr_ratio check in src/gate.py and changed policy_version from 1.0 to 1.1, since the policy gained a new threshold. With this check in place, v1 passes (FPR ratio 0.9427) and v2 gets one more FAIL (FPR ratio 0.5765).

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 before running my model. It matches the four fifths screen the policy already uses for approval disparity and TPR ratio, so both sides of error rate fairness are held to the same standard, and it’s not a number picked to make a model pass. A false positive means approving a driver at the standard rate who then files an at-fault claim. For Sierra Mutual, that’s underpriced risk: it pays claims without having charged the higher premium. For the driver, it’s an approval they got on the benefit of the doubt. Unequal FPR is a fairness problem because it means one area’s risky drivers get that benefit of the doubt while comparable drivers in the other area are held to a stricter standard and sent to manual review at a higher rate. In v2, rural FPR is 0.4709 vs urban 0.8168 (ratio 0.5765), so similar drivers are treated differently based on where they live, not how they drive.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

In tests/test_lab5_gate.py, I replaced the skip in test_gate_blocks_fpr_gap with two asserts that run the gate on fake metrics. The first sets fpr_ratio to 0.70, which is 0.10 below my 0.80 threshold, and asserts the decision is BLOCKED.The second sets it exactly at the threshold (0.80) and asserts PASS. Together they prove the new check actually fires and the boundary is right where  a value at the threshold passes, and a value below it blocks.

Running the pipeline can’t prove that. A pipeline run only shows how the gate treated one real model. If that model happened to pass, you couldn’t tell whether the check works or is missing, misspelled, or never triggered. The test checks the gate’s logic directly, with controlled inputs, independent of any particular model. It’s a control over the control, and it reruns automatically on every pull request, so if someone later breaks or removes the FPR check, the test fails right away.
---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

[stage 5] Deployment gate
==============================================================================
  DEPLOYMENT GATE   model v3   policy v1.1
==============================================================================
  check                                    value   threshold   result
------------------------------------------------------------------------------
  no_prohibited_features                    none        none   pass
  overall_auc                             0.8224        0.68   pass
  subgroup_auc[rural]                     0.8001        0.64   pass
  subgroup_tpr[rural]                     0.9059        0.70   pass
  subgroup_auc[urban]                     0.8345        0.64   pass
  subgroup_tpr[urban]                     0.9220        0.70   pass
  approval_disparity_ratio                0.8729        0.80   pass
  tpr_ratio                               0.9825        0.80   pass
  fpr_ratio                               0.9005        0.80   pass
==============================================================================
  DECISION: PASS. This model may proceed to deployment review.
==============================================================================

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

I used the following:
max_hard_brakes_per_1k
night_share_mean
speeding_velocity
claims_per_month
max_hard_brakes_per_1k mattered most because each feature was removed one at a time. Then, I compared the overall AUC each time with the full model's 0.8224

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Yes. I added `territory_risk_index` to my final logistic regression model and reran the pipeline. Overall AUC rose from 0.8224 to **0.8451**, but the gate **BLOCKED** it. The approval_disparity_ratio fell to **0.6620** and fpr_ratio to **0.6332**, both below the 0.80 thresholds. My own min_fpr_ratio was one of the checks that stopped it. The extra AUC didn't come from better information about how people drive. The vendor index is mostly a rural flag (generate_data.py line 136), so the model used it as a proxy to relearn the rural penalty in the historical label (line 132), and urban and rural drivers ended up treated very differently.

That's the difference between a better model and a deployable one. "Better" by AUC only means it predicts the historical labels more closely, including their bias. "Deployable" means it meets every threshold the AI Risk Committee set in advance, for every group. A higher score bought with a proxy for a protected attribute fails that test, and lowering min_fpr_ratio to let it through would turn the control into an alibi. So my final model leaves the index out and accepts the lower AUC of 0.8224.

If you ran the territory experiment yourself, check that your numbers match these (0.8451, 0.6620, 0.6332). If any differ, use yours.

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
