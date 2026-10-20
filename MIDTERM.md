# BANA 690A Midterm: Written Answers

**Name:** Inna Chatoyan
**Last-name group (A to H, I to P, Q to Z):** A to H
**GitHub username:** chatoyaninna

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).

test_no_zip_like_column: detective. It found zip in the training data.
test_no_date_like_column: detective. It found date_of_birth.
test_no_suspiciously_predictive_column: detective. adjuster_fraud_review correlated 0.845 with the label, above the 0.60 limit.
test_policy_agrees_with_data_dictionary: detective. 

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added "zip" and "date_of_birth" to pii_columns, and "adjuster_fraud_review" to leakage_columns (it is recorded after the decision, during the policy year).
**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
The code already enforces whatever the policy says, so the bug was an incomplete policy, not the code. Keeping the rule in policy.json keeps one versioned source of truth that the code and tests both read, so they can’t drift apart.
---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | Sum of claim_filed over months 1 to 24, divided by 24. | Drivers who filed claims before are more likely to file again, so a higher value means less likely to be claim-free. |
| months_since_last_claim | recency | 25 minus the most recent month with a claim; drivers with no claim get 25. | A recent claim signals current risky behavior; a long gap or no claim at all suggests a safer driver. |
| max_hard_brakes_per_1k | extremes | Hard brakes divided by miles times 1,000 for each month, then the highest month per driver. | A month with lots of hard braking shows aggressive or distracted driving, which raises claim risk. |
| night_share_mean | ratio | Average of night_miles_share across months 1 to 24 per driver. | Night driving has lower visibility and more fatigue, so more night driving means higher risk. |
| miles_volatility | volatility | Standard deviation of monthly miles divided by mean monthly miles per driver. | Irregular driving patterns can signal less consistent habits or unfamiliar conditions, which may raise risk. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The fence test hands my feature functions extra months 25 to 30 with absurd values and checks that the output does not change. If nothing changes, every feature only uses data from before the decision (months 1 to 24). If a feature had failed it, it would be using information from the policy year, which does not exist yet when the underwriter makes the decision. The model would look very accurate in testing, but in production those future months would be missing, so the feature would be wrong or empty and the model’s real performance would collapse. That is leakage.

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | It counts claims from the 3 years before the application, so the underwriter has it at decision time. It is filled more often for drivers who later had a claim (0.146 vs 0.350), but that reflects real past risk, not information from the future. |
| renewal_offered | leakage | 0.549 | end of policy year | It is decided after the policy year ends, partly because of whether the driver filed a claim. It does not exist when the underwriter makes the decision, so the model would be learning from the outcome itself. |
| annual_mileage_declared | allowed | 0.280 | at application | The applicant declares it on the application form, so it is known at decision time. It is filled almost equally for both classes (0.970 vs 0.966), so nothing suspicious. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
renewal_offered is leakage even though its correlation (0.549) is under the 0.60 limit. A numeric test only measures how strongly a column moves with the label. It has no idea when the column was recorded. A leaky column can be only partly related to the outcome and still slip under the threshold, while a legitimate column like prior_claims_3y can look suspicious just because past risk predicts future risk. What catches it is a timeline test: checking the data dictionary for when each column was recorded relative to the decision. renewal_offered is recorded at the end of the policy year, after the decision, so the model would never have it in production. The numbers can raise a flag, but the timeline is what proves leakage.
---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
v1: overall AUC 0.7046. DECISION: PASS. This model may proceed to deployment review.
v2: overall AUC 0.7224. DECISION: BLOCKED. This model may NOT be deployed.
**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.
v2 is blocked because it treats rural drivers unfairly, even though it is more accurate overall. Rural approval dropped from 0.7749 (v1) to 0.5146, and rural TPR dropped from 0.8647 to 0.5588, which failed four fairness and subgroup checks.
The cause is in data/generate_data.py:
Line 136: territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1). The vendor index is mostly “+30 if rural” plus noise, so it is a proxy for the area column.
Line 132: logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n). The historical claim_free label carries a -1.10 penalty against rural drivers that their driving did not justify.
The penalty is in the historical label, and territory_risk_index gives the model a way to recognize rural drivers without seeing the area column. So v2 learned the rural penalty back through the proxy. Its higher AUC comes partly from reproducing old, unfair underwriting.


**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.
no_prohibited_features is a preventive check that only looks at feature names. It blocks area, zip, gender and date_of_birth if they appear in the config. territory_risk_index has a different name and is not on the list, so it passed, even though it carries almost the same information as area. A list check cannot see what a column actually encodes, so it cannot catch a proxy.
The detective checks on outcomes caught it, mainly approval_disparity_ratio (0.5596 vs the 0.80 minimum) and tpr_ratio (0.5888 vs 0.80), along with subgroup_tpr[rural] (0.5588 vs 0.70) and subgroup_auc[rural] (0.5937 vs 0.64). These look at what the model actually does to each group, so they caught the unfair result no matter which column caused it.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added "min_fpr_ratio": 0.80 to governance/policy.json, next to the other min_ keys, and changed policy_version from “1.0” to “1.1”. I also added the matching check in src/gate.py so the gate enforces it.
**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
I chose 0.80 before running any model with it, to match the four-fifths rule the policy already uses for approval_disparity_ratio and tpr_ratio, so all group-parity checks follow the same standard. A false positive means the model approved a driver at the standard rate who then filed a claim. For Sierra Mutual that is a loss, because risk was underpriced. For the driver it is a benefit, because they got a cheaper rate than their risk justified. Unequal FPR is a fairness problem because it means risky drivers in one area get the benefit of the doubt and risky drivers in the other do not. In v2, urban FPR was 0.8168 and rural only 0.4709, so rural drivers were held to a stricter standard just because of where they live, not only because the company lost money.
**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
In test_gate_blocks_fpr_gap I removed the skip and wrote two asserts using made-up metrics. An fpr_ratio 0.10 below my threshold must return BLOCKED, and an fpr_ratio exactly at the threshold must return PASS. Running the pipeline only shows the check’s result for one real model, so it can’t tell me whether the check itself is correct. The test proves the check fires when it should, uses the right comparison (>= at the boundary), and reads its value from the policy. It also runs every time the code changes, so if someone breaks or deletes the check later, the test fails.
---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.
model v3 (logistic_regression, 6 declared fields + 5 engineered features), policy v1.1
overall AUC 0.8198
approval_disparity_ratio 0.8775 (min 0.80) pass
tpr_ratio 0.9922 (min 0.80) pass
fpr_ratio 0.9295 (min 0.80) pass
subgroup_auc rural 0.7936 / urban 0.8349 (min 0.64) pass
subgroup_tpr rural 0.9118 / urban 0.9190 (min 0.70) pass
DECISION: PASS. This model may proceed to deployment review.
**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used five engineered features: claims_per_month (frequency), months_since_last_claim (recency), max_hard_brakes_per_1k (extremes), night_share_mean (ratio) and miles_volatility (volatility). Together they raised AUC from 0.7046 (v1, declared fields only) to 0.8198 (v3), with the same model type.
max_hard_brakes_per_1k mattered most. I know because I removed one feature at a time and reran the pipeline. Removing max_hard_brakes_per_1k dropped AUC from 0.8198 to 0.7397. Removing claims_per_month barely changed it (0.8197), probably because months_since_last_claim already carries most of the same claim-history information. The worst month of hard braking captures aggressive driving that the declared application fields cannot see. The audit log records every one of these runs.


**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
Yes. Adding territory_risk_index raised overall AUC from 0.8198 to 0.8421, but the model was BLOCKED. approval_disparity_ratio fell to 0.6460 and fpr_ratio fell to 0.5855, both below 0.80. Rural approval dropped from 0.7251 to 0.5556. The index is a proxy for area (line 136 of generate_data.py), so the model used it to learn back the historical rural penalty in the label. A better model by AUC is not the same as a deployable model: some of that extra accuracy comes from reproducing unfair past decisions. A deployable model has to be accurate enough and also meet every fairness and governance check. I did not lower min_fpr_ratio to let it through, because changing the threshold to fit the model would defeat the control.
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
