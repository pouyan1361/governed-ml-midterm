# BANA 690A Midterm: Written Answers

**Name:** Lori Balian
**Last-name group (A to H, I to P, Q to Z):** A to H
**GitHub username:** LoriBalian

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
- test_no_zip_like_column
- test_no_date_like_column
- test_no_suspiciously_predictive_column
- test_policy_agrees_with_data_dictionary
All four of these are detective controls.

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added "zip" and "date_of_birth" under pii_columns.
I added "adjuster_fraud_review" under leackage_columns.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
The code was already working correctly, but the policy was missing columns. I fixed the policy becaause the code follows its rules. 

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Total prior claims divided by 24 months | More past claims may mean more future claims. |
| months_since_last_claim | recency | 25 minus the month of the most recent claim; 25 if no claims | A recent claim may mean a driver is more likely to file another claim. |
| max_hard_brakes_per_1k | extremes | Highest monthly hard-braking rate per 1,000 miles | Hard braking may be a sign of unsafe driving. |
| night_share_mean | ratio | Average share of miles driven at night over 24 months | Driving more at night may increase the chance of an accident. |
| miles_volatility | volatility | Standard deviation of monthly miles divided by average monthly miles | Big changes in driving habits may affect the chance of a claim. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The temporal fence makes sure the model only uses data from before the insurance decision (months 1-24). If it used future data from month 25-30, the model could look more accurate during testing but wouldn't work as well in real life because that information wouldn't be available yet.
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | the info was available before the decision |
| renewal_offered | leakage | 0.549 | end of policy | the info was only available after the decision |
| annual_mileage_declared | allowed | 0.280 | at application | the info was available when the driver applied |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

A numeric test can miss leakage because future information might not have a high correlation. A timeline test catches it by checking if the information was available before or after the decision.

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
v1: DECISION: PASS
Overall AUC: 0.7046

v2: DECISION: BLOCKED
Overall AUC: 0.7224

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.
It was blocked because it failed four governance checks.
Code for territory_risk_index: line 136 in data/generate_data
Code for label's rural penalty: line 132 in data/generate_data

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.
The preventive check passed because the model didn't use any banned columns. However, it used a column that indirectly showed where drivers live. The detective checks caught this by showing that rural and urban drivers had different approval rates and results.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added min_fpr_ratio with a value of 0.80 and updated the policy version to 1.1.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
I chose 0.80 because rural and urban drivers should be treated fairly. If the model approves too many drivers who end up filing claims, Sierra Mutual could lose money. If one group has a much lower false positive rate, that group is being treated more strictly.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
The test proves that the new rule blocks a model when its FPR ratio is below 0.80 and passes it when the ratio meets 0.80. Running the pipeline only showed that one model passed, but the test checks both situations.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

check                                    value   threshold   result
------------------------------------------------------------------------------
  no_prohibited_features                    none        none   pass
  overall_auc                             0.8198        0.68   pass
  subgroup_auc[rural]                     0.7936        0.64   pass
  subgroup_tpr[rural]                     0.9118        0.70   pass
  subgroup_auc[urban]                     0.8349        0.64   pass
  subgroup_tpr[urban]                     0.9190        0.70   pass
  approval_disparity_ratio                0.8775        0.80   pass
  tpr_ratio                               0.9922        0.80   pass
  fpr_ratio                               0.9295        0.80   pass
==============================================================================
  DECISION: PASS. This model may proceed to deployment review.
==============================================================================

**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used five engineered features: claims_per_month, months_since_last_claim, max_hard_brakes_per_1k, night_share_mean, and miles_volatility.
The one that helped the most was max_hard_brakes_per_1k. I know because I removed each one and tested the model again. Without hard braking, the AUC dropped from 0.8198 to 0.7397.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
Adding `territory_risk_index` increased the model's AUC from 0.8198 to 0.8421, but the model was blocked because it failed two fairness checks. This shows that a model can make better predictions overall but still treat groups unfairly.

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

**Signature (type your name):** Lori Balian
