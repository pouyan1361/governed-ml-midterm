# BANA 690A Midterm: Written Answers

**Name:** Denise Anciola
**Last-name group (A to H, I to P, Q to Z):** A to H
**GitHub username:** @denisecanciola99

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
The four tests that failed were test_no_zip_like_column, test_no_date_like_column, test_no_suspiciously_predictive_column, and test_policy_agrees_with_data_dictionary. All four are detective controls, because they check the data itself instead of a list. Together, they caught zip, date_of_birth, and adjuster_fraud_review (correlation 0.845, over the 0.60 limit), none of which the policy listed.

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added zip and date_of_birth to pii_columns, because together they can identify a person even without a name. I also added adjuster_fraud_review to leakage_columns, because it’s recorded after the policy year, so it wouldn’t exist when the underwriter makes the decision. After those changes, the Lab 1 tests showed 11 passed.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
src/prepare.py already drops whatever the policy tells it to, so the policy is the one source of truth that the committee owns and approves. If I hard-coded column names into the Python, I’d be creating a second copy of the rules that nobody reviews, and it would fall out of sync the next time the policy changes

---

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
The test adds fake months 25 to 30 with extreme values and checks that none of my features change, which proves they only use data from before the decision. If a feature had failed, the model would look great in testing but do bad in production because those future months don’t exist yet when the decision is made.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | | | | |
| renewal_offered | | | | |
| annual_mileage_declared | | | | |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
renewal_offered only has a 0.549 correlation, under the 0.60 limit, so a numeric test lets it through. The timeline test catches it, because the data dictionary shows it’s recorded at the end of the policy year, after the decision.

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
v1: DECISION: PASS, overall AUC 0.7046. v2: DECISION: BLOCKED, overall AUC 0.7224.

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.
Line 132 (logit = 1.35 + z - 1.10 * rural + ...) puts a rural penalty into the label, and line 136 (territory_risk_index = np.clip(42 + 30 * rural + ...)) makes the vendor index mostly a rural flag. v2 uses that index, so it learns the rural penalty through a proxy. Rural approval drops to 0.5146 vs 0.9196 for urban.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.
no_prohibited_features only checks feature names, and territory_risk_index isn’t on the list, so it can’t tell that the index is standing in for area. The detective checks on outcomes caught it: approval_disparity_ratio (0.5596) and tpr_ratio (0.5888), both under 0.80.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added "min_fpr_ratio": 0.80 to governance/policy.json.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
I chose 0.80 to match the four-fifths standard already used for the other fairness ratios. A false positive means Sierra approves a driver who then files a claim, so Sierra loses money and the driver gets a lower rate than their risk deserves. If FPR is unequal, one group’s risky drivers get the benefit of the doubt while the other group is held to a stricter standard, which is unfair, not just a profit problem.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
My test feeds the gate fake metrics with an fpr_ratio 0.10 below the threshold and checks that it’s BLOCKED, then sets it exactly at the threshold and checks that it PASSES. Running the pipeline only shows one model’s result, while the test proves the check actually fires on a known bad input.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.
==============================================================================
  DEPLOYMENT GATE   model v3   policy v1.1
==============================================================================
  check                                    value   threshold   result
------------------------------------------------------------------------------
  no_prohibited_features                    none        none   pass
  overall_auc                             0.8217        0.68   pass
  subgroup_auc[rural]                     0.8012        0.64   pass
  subgroup_tpr[rural]                     0.9059        0.70   pass
  subgroup_auc[urban]                     0.8333        0.64   pass
  subgroup_tpr[urban]                     0.9205        0.70   pass
  approval_disparity_ratio                0.8672        0.80   pass
  tpr_ratio                               0.9841        0.80   pass
  fpr_ratio                               0.9205        0.80   pass
==============================================================================
  DECISION: PASS. This model may proceed to deployment review.
==============================================================================

**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used claims_per_month, months_since_last_claim, max_hard_brakes_per_1k, speeding_velocity, and night_share_mean. max_hard_brakes_per_1k mattered most: when I removed it and reran, AUC dropped from 0.8217 to 0.7558.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
Adding territory_risk_index raised AUC to 0.8448, but the model was BLOCKED because the disparity ratio fell to 0.6654 and the FPR ratio to 0.6332. A more accurate model isn’t automatically deployable if it gets that accuracy by treating rural drivers unfairly.

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
Denise Curiel Anciola