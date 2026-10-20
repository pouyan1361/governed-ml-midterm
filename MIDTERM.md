# BANA 690A Midterm: Written Answers

**Name:*Aastha Malhotra*
**Last-name group (A to H, I to P, Q to Z):*M*
**GitHub username:*am-malhotra*

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
test_no_zip_like_column – 
Error: ZIP-like quasi-identifier columns reached training: ['zip']- detective
test_no_date_like_column – 
Error: Date-like quasi-identifier columns reached training: ['date_of_birth'] - detective
test_no_suspiciously_predictive_column – 
Error: Columns correlated with the label above 0.6: {'adjuster_fraud_review': 0.845} - detective
test_policy_agrees_with_data_dictionary – 
Error: Policy is incomplete. Add to pii_columns: ['zip', 'date_of_birth']. Add to leakage_columns: ['adjuster_fraud_review]- detective


**1.2** What did you add to `governance/policy.json`, and under which keys?
Additions made: 
  "pii_columns":  "zip","date_of_birth"],
  "leakage_columns": ["adjuster_fraud_review"],

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

---we want the code to read from the policy and not hardcode it in the code in the source file 

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | | |
| | | | |
| | | | |
| | | | |
| | | | |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

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

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

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
