# BANA 690A Midterm: Written Answers

**Name:** Bear Zelaya
**Last-name group (A to H, I to P, Q to Z):** Group Z
**GitHub username:** BearZelaya87

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
# The four tests that failed were test_no_zip_like_column, test_no_date_like_column, test_no_suspiciously_predictive_column, and test_policy_agrees_with_data_dictionary. All four are detective controls because they caught problems in the data that were missing from the policy.

**1.2** What did you add to `governance/policy.json`, and under which keys?
# In governance/policy.json, I added zip and date_of_birth under pii_columns because they could identify applicants. I also added adjuster_fraud_review under leakage_columns because it was recorded after the policy year and had a 0.845 correlation with the label.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
# I fixed the policy instead of src/prepare.py because the code was already doing its job by removing whatever columns were listed in the policy. The problem was that the policy was missing some columns, so updating it fixed the issue without changing the code.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| claims_per_month | frequency | I took the total claims each driver had over 24 months and divided by 24. | Drivers who had more claims in the past might have a higher chance of filing another one. |
| miles_volatility | volatility | I calculated how much each driver's monthly mileage changed compared to their average mileage. | If someone's driving changes a lot every month, it could mean their driving habits are less consistent. |
| night_share_mean | ratio | I calculated the average percentage of miles each driver drove at night over 24 months. | Driving more at night could increase the risk of accidents because of lower visibility. |
| max_hard_brakes_per_1k | extremes | I calculated hard brakes per 1,000 miles for each month and used the highest monthly value. | A month with a lot of hard braking could show risky driving behavior. |
| speeding_velocity | velocity | I compared speeding events per 1,000 miles in the last six months with the driver's overall 24 month rate. | If a driver has been speeding more recently, they might have a higher risk of getting into an accident. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The temporal fence test checks that my features only use data from months 1 through 24. It adds fake data from months 25 to 30 to see if any results change. If they change, that means my model is using information from the future that would not be available when making the actual decision. This could make the model seem more accurate during testing but unreliable when used in real life.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | This shows claims the driver had in the past. Since the information is already available when they apply, the model can use it. |
| renewal_offered | leakage | 0.549 | end of policy year | This information comes after the policy year is over, so the model should not use it. It could give away the outcome because 95.9% of claim-free drivers had this filled in compared to only 50% of drivers who filed claims. |
| annual_mileage_declared | allowed | 0.280 | at application | The driver provides their estimated mileage when applying for insurance, so the information is available before the decision. The fill rates are also almost the same for both groups. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
renewal_offered is considered leakage even though its correlation is only 0.549, which is below the 0.60 limit. Just because a number is below the limit does not mean the information is safe to use. The timeline test helps us catch this because renewal_offered was recorded after the policy year ended. The model should only use information that was available when the original decision was made. 

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

v1: Overall AUC 0.7046. DECISION: PASS. This model may proceed to deployment review.
v2: Overall AUC 0.7224. DECISION: BLOCKED. This model may NOT be deployed.

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

Even though v2 had a higher overall AUC, it was blocked because it treated rural drivers differently from urban drivers. The rural approval rate was only 0.5146 compared to 0.9196 for urban drivers. The disparity ratio was 0.5596, which is below the required 0.80. Four governance checks failed: subgroup_auc[rural], subgroup_tpr[rural], approval_disparity_ratio, and tpr_ratio.

Line 132 in data/generate_data.py:
logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)
This line reduces the claim-free outcome for rural drivers by subtracting 1.10, even when their driving behavior does not justify it.

Line 136 in data/generate_data.py:
territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)
This line gives rural drivers a higher territory risk score because it adds 30 when the driver is rural.

Since v2 uses territory_risk_index, it can learn the unfair pattern from the historical data without directly using the area column.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

The no_prohibited_features check is a preventive control. It only compares the names of the features in the config to a list of banned columns like area, gender, and zip. Since territory_risk_index is not on that list, v2 passed this check, even though the index carries almost the same information as area. A list check can only catch what it knows by name, so it cannot see a proxy.
The detective checks caught the problem because they measure the model’s actual outcomes for each group. subgroup_auc[rural], subgroup_tpr[rural], approval_disparity_ratio, and tpr_ratio all failed in artifacts/gate_report.json, which shows v2 was treating rural drivers worse regardless of what the feature was called.


Line 132 in data/generate_data.py:
logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)
This line reduces the claim-free outcome for rural drivers by subtracting 1.10, even when their driving behavior does not justify it.

Line 136 in data/generate_data.py:
territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)
This line gives rural drivers a higher territory risk score because it adds 30 when the driver is rural.

Since v2 uses territory_risk_index, it can learn the unfair pattern from the historical data without directly using the area column.

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?

I  added min_fpr_ratio to the governance policy and set it to 0.80. This means the false positive rates for rural and urban drivers need to be reasonably close, with a minimum ratio of 0.80.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

I chose 0.80 because I think both rural and urban drivers should have similar error rates. A false positive means the model approves a driver for the standard rate because it predicts they will be claim-free, but they actually file an at-fault claim, which can cost Sierra Mutual money and gives the driver a standard-rate offer based on an incorrect prediction. It becomes a fairness problem when one group is more likely to receive that mistaken approval just because of where they live.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

I tested whether the gate blocks a model when its FPR ratio is below 0.80 and passes the FPR check when the ratio meets the requirement. All five Lab 5 tests passed, and the pipeline showed that v1 passed with an FPR ratio of 0.9427 while v2 failed with 0.5765. This proves the new governance check works for different values, instead of only relying on the results of one model run.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

My final model had an overall AUC of 0.8222, an approval disparity ratio of 0.8754, a TPR ratio of 0.9809, and an FPR ratio of 0.8712.

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

I used four engineered features: claims_per_month, speeding_velocity, max_hard_brakes_per_1k, and night_share_mean. The one that made the biggest difference was max_hard_brakes_per_1k. I know this because when I removed it and ran the model again, the AUC dropped from 0.8216 to 0.7551. Removing the other features barely changed the AUC. I also noticed that removing miles_volatility slightly improved the results, so I decided not to include it in my final model.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

When I added territory_risk_index, my overall AUC increased to 0.8449, which was my highest result. However, the rural approval rate dropped to 0.5702 compared to 0.8601 for urban drivers. The model was blocked because the approval disparity ratio was 0.6629 and the FPR ratio was 0.6376, both below the required 0.80.

This showed me that having a higher AUC does not automatically make a model better or safe to use. The territory risk score was bringing back the unfair rural penalty from the historical data. I learned that a model needs to meet both performance and fairness requirements before it can be approved for deployment.

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

**Signature (type your name):** Bear Zelaya
