# BANA 690A Midterm: Written Answers

**Name:Sabrina**
**Last-name group (A to H, I to P, Q to Z):Q**
**GitHub username:sab-quevedo**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).

FAILED tests/test_lab1_compliance.py::test_no_zip_like_column - AssertionErro...
FAILED tests/test_lab1_compliance.py::test_no_date_like_column - AssertionErr...
FAILED tests/test_lab1_compliance.py::test_no_suspiciously_predictive_column
FAILED tests/test_lab1_compliance.py::test_policy_agrees_with_data_dictionary


**1.2** What did you add to `governance/policy.json`, and under which keys?

For "pii_columns":"zip", "date_of_birth" were added. 
For "leakage_columns": "adjuster_fraud_review" was added.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

The fix is in the policy since this is the control, and the code only excutes the objective.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
You need 5 implemented features, at least 4 families, and 4 passed
| claims_per_month | frequency | | |
| | | | |
| | | | |
| | | | |
| | | | |
families: ['frequency']
                   count   mean    std  min  25%  50%  75%    max
claims_per_month  4000.0  0.007  0.018  0.0  0.0  0.0  0.0  0.125


**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The temporal fence test adds fake future data and checks that the features don’t change. If a feature changed, it would be using information from after the decision date. Overall, the model would look great in training but do badly in production.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | | | | |
| renewal_offered | | | | |
| annual_mileage_declared | | | | |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

---
Renewal_offered isn’t in the leakage_columns.

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

v1: overall_auc                             0.7046        0.68   pass
    DECISION: PASS. This model may proceed to deployment review.
v2: overall_auc                             0.7224        0.68   pass
    DECISION: BLOCKED. This model may NOT be deployed.

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

Line 136.

Line 132.


**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

The preventive check only compares feature names to a banned list. “area” is banned, but “territory_risk_index” isn’t, so it passed.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I added min_fpr_ratio to policy.json with a value of 0.80.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 because it matches the four-fifths rule already used for the approval and TPR ratios. A false positive means Sierra approves a driver who will file a claim and loses money on them. Unequal FPR is unfair if one group’s risky drivers get approved more often than the other’s, the second group is being held to a stricter standard.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

The test feeds the gate fake metrics, one with an FPR ratio below the threshold that must be BLOCKED and one exactly at the threshold that must PASS. 

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.
policy_version": "1.1", "stage_reached": "gate", "decision": "PASS", "overall_auc": 0.8198, "approval_disparity_ratio": 0.8813, "fpr_ratio": 0.9101

**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used claims_per_month, months_since_last_claim, miles_volatility, max_hard_brakes_per_1k, and night_share_mean. max_hard_brakes_per_1k mattered most.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Yes, adding territory_risk_index raised the AUC, but the model was BLOCKED because rural drivers were treated unfairly

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
