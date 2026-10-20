# BANA 690A Midterm: Written Answers

**Name:** Eric Davis
**Last-name group (A to H, I to P, Q to Z):** A to H (recency and extremes)
**GitHub username:** edavis71433

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).

All four failures were detective controls: test_no_zip_like_column (it found `zip`), test_no_date_like_column (it found `date_of_birth`), test_no_suspiciously_predictive_column (it found `adjuster_fraud_review` at 0.845), and test_policy_agrees_with_data_dictionary. The list controls all passed, because they only enforce what the policy already listed.

**1.2** What did you add to `governance/policy.json`, and under which keys?

I added "zip" and "date_of_birth" to pii_columns, because data/data_dictionary.csv classes them as quasi-identifiers. I added "adjuster_fraud_review" to leakage_columns, because the dictionary says it is recorded after the policy year, and its correlation with the label (0.845) is above the 0.60 limit.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

src/prepare.py already drops whatever the policy lists, so the code worked and the rule was missing. Fixing the policy keeps the rule versioned and reviewable, and every run enforces it the same way.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Sum of claim_filed over months 1 to 24, divided by 24. | Drivers who had at-fault claims before are more likely to have them again. |
| months_since_last_claim | recency | 25 minus the month of the latest claim, or 25 if there was no claim in the window. | A recent claim points to risky driving now; a long gap means the driver has been safe lately. |
| max_hard_brakes_per_1k | extremes | The highest monthly hard brakes per 1,000 miles across the 24 months. | Hard braking reflects aggressive or distracted driving, which causes at-fault claims. |
| speeding_velocity | velocity | Speeding per 1,000 miles in months 19 to 24, divided by the 24 month rate plus 0.1. | A driver speeding more than their own normal is getting riskier right before the policy starts. |
| miles_volatility | volatility | Standard deviation of monthly miles divided by mean monthly miles. | Erratic mileage can signal unstable habits, though it added little in this data. |
| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13 to 24 minus the same rate in months 1 to 12. | A rising rate means the driver is getting worse over time. |
| night_share_mean | ratio | Average night_miles_share over the 24 months. | Night driving has lower visibility and more fatigue, so drivers who do more of it have more claims. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The test adds fake months 25 to 30 with absurd values, like 500 hard brakes and a claim every month, and rebuilds the features. If any feature changes, it read data from after the decision. In production those months do not exist yet when the underwriter decides. A feature that used them would look strong in testing and then break or behave differently on real applicants. Those months also fall inside the policy year, so they partly encode the label itself.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | It is known when the decision is made and covers the 3 years before the history window. It is strong because it is a real risk signal, not because it leaks the outcome. |
| renewal_offered | leakage | 0.549 | end of policy year | It is decided after the policy year, partly because of whether the driver had a claim. It is filled for 95.9% of claim free drivers vs 50.0% of claim filers. |
| annual_mileage_declared | allowed | 0.280 | at application | The applicant declares it on the form before the decision, and more miles means more exposure to accidents. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

renewal_offered is leakage, but its correlation is 0.549, under the 0.60 limit, so the numeric test lets it through. A correlation test only measures how strong a column is, not when it was recorded. A timeline test catches it: the when_recorded column in data/data_dictionary.csv says "end of policy year", which is after the decision.

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

v1: overall AUC 0.7046, "DECISION: PASS. This model may proceed to deployment review."
v2: overall AUC 0.7224, "DECISION: BLOCKED. This model may NOT be deployed."

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

v2 failed four group checks: rural AUC 0.5937 (minimum 0.64), rural TPR 0.5588 (minimum 0.70), approval disparity ratio 0.5596 (minimum 0.80), and TPR ratio 0.5888 (minimum 0.80). Line 136 of data/generate_data.py builds `territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100)`, so the index is mostly the rural flag. Line 132 builds the label as `logit = 1.35 + z - 1.10 * rural + ...`, which is a rural penalty that driving does not justify. Using the index lets v2 learn that penalty back and decline safe rural drivers.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

no_prohibited_features only compares feature names to a list. territory_risk_index is not called area and is not on the list, but it carries the same information, so a list cannot see it. A preventive list only catches what someone already wrote down. The detective outcome checks caught it by measuring results by group: approval_disparity_ratio and tpr_ratio, along with the rural subgroup AUC and TPR checks.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I added min_fpr_ratio = 0.80 to governance/policy.json and bumped policy_version from 1.0 to 1.1. src/gate.py now checks metrics["fpr_ratio"] against it whenever the key is present.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

0.80 matches the four-fifths standard the policy already uses for approval disparity and TPR ratio, so the fairness rules stay consistent, and I chose it before looking at my own model's results. A false positive means Sierra gives the standard rate to a driver who then files an at-fault claim, so Sierra underprices that risk and pays the claim. The driver gets a cheaper rate than their risk justifies. When FPR differs by area, as in v2 (urban 0.8168 vs rural 0.4709), risky urban drivers get the benefit of the doubt and risky rural drivers do not. Drivers with the same risk get different treatment because of where they live, which repeats the historical rural penalty.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

test_gate_blocks_fpr_gap builds fake metrics with fpr_ratio 0.05 below the policy minimum. It asserts the gate returns BLOCKED and that an fpr_ratio check exists and failed. It then asserts PASS at exactly the minimum and 0.05 above it. This proves the check exists, fires, and uses the right boundary. Running the pipeline only shows one real model, which may pass anyway, so it never proves the check can block anything.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

| overall AUC | disparity ratio | TPR ratio | FPR ratio | DECISION |
|---|---|---|---|---|
| 0.8247 | 0.8599 | 0.9952 | 0.9729 | PASS |

Rural AUC 0.8080 and TPR 0.9176; urban AUC 0.8344 and TPR 0.9220.

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

The model is a logistic regression using five engineered features: claims_per_month, months_since_last_claim, speeding_velocity, max_hard_brakes_per_1k, and night_share_mean. It also uses three declared fields: annual_mileage_declared, prior_insurer_years, and prior_claims_3y. max_hard_brakes_per_1k mattered most. Removing it alone drops overall AUC from 0.8247 to 0.7577, the biggest drop of any feature, and night_share_mean is next (to 0.8076). I picked the set by removing one feature at a time and keeping a removal only if AUC went up and the gate still passed. Because I chose on the same test split the gate scores, the last few thousandths of AUC may not hold on new data.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

Yes. Adding territory_risk_index to my final model raised overall AUC to 0.8482, but the gate BLOCKED it: approval disparity ratio fell to 0.664 and FPR ratio fell to 0.616. The extra AUC comes from matching the historical label, rural penalty included. A better model by AUC is not the same as a deployable one, which also has to be accurate for the right reasons and fair across groups.

---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?

It is a preventive control, because a person must approve before the workflow runs. The owner is the instructor, acting as Model Risk Officer and repo owner (see .github/CODEOWNERS). The trigger is a pull request from a fork. The evidence is that GitHub Actions records who approved the run and when, next to the run logs and the uploaded governance-evidence artifacts.

**7.2** After approval, what did Stage A print about your governance change? Quote it.

---

## Lab 8 (bonus): Break it and watch it stop

**8.1** What did you change on your second branch, and what did `python run_pipeline.py --config configs/v2.json` print locally?

**8.2** What did Stage A print on GitHub? Quote the refusal line.

**8.3** Which control would NOT have stopped this change on its own, and why do we need both?

---

## Declaration

I completed this exam individually, using only the permitted materials.

**Signature (type your name):** Eric Davis
