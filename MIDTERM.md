# BANA 690A Midterm: Written Answers

**Name:Julie Loyez**
**Last-name group (A to H, I to P, Q to Z):I to P**
**GitHub username:julixlyz08**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
test_no_zip_like_column (detective control)
test_no_date_like_column (detective control)
test_no_suspiciously_predictive_column (detective control)
test_policy_agrees_with_data_dictionary (detective control)

**1.2** What did you add to `governance/policy.json`, and under which keys?
I added "zip" and "date_of_birth" to the pii_columns because the data dictionary classes both as quasi-identifiers. 
I added "adjuster_fraud_review" to the leakage_column because the data dictionary classes it as an outcome recorded after the policy year (a fraud referral only happens during a claim).

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
The fix is in the policy and not in the prepare.py file because the file already drops whatever the policy lists. The python file ran like it was supposed to do, it was the policy that was incomplete.

---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|
| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
|---|---|---|---|

| claims_per_month | frequency | Sum of claim_filed over months 1 to 24, divided by 24. | Drivers who filed at-fault claims before tend to file again, so a higher rate should mean a lower chance of a claim-free year (correlation with claim_free about -0.11). |

| speeding_velocity | velocity | Speeding events per 1,000 miles in the last 6 months (19 to 24), divided by speeding events per 1,000 miles over all 24 months plus 0.1. | A value above 1 means the driver is speeding more lately than their usual habit, and that recent risky behavior is the closest signal to how they will drive during the policy year (correlation about -0.14). |

| hard_brake_trend | trend | Hard brakes per 1,000 miles in months 13 to 24 minus hard brakes per 1,000 miles in months 1 to 12. | Hard braking is a sign of following too closely or reacting late, and a positive trend means that habit is getting worse, which should raise claim risk (correlation about -0.13). |

| night_share_mean | ratio | Average of night_miles_share across months 1 to 24. | Night driving has lower visibility, more fatigue and more impaired drivers on the road, so a higher share of night miles should mean more crash exposure (correlation about -0.12). |

| miles_volatility | volatility | Standard deviation of monthly miles divided by mean monthly miles over months 1 to 24 (coefficient of variation). | Erratic mileage can signal irregular use such as long unfamiliar trips, so it should add some risk; in this data it turned out to be a weak signal (correlation about +0.02). |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The temporal fence test adds fake months 25 to 30 with absurd values and checks that no feature changes. If one changes, it used data from after the underwriting decision. If a feature had failed it, the model would have looked accurate in testing by partly seeing the outcome, then performed much worse in production, where those months don’t exist yet at application time.

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | allowed | 0.243 | at application | Comes from the industry claims database and counts claims in the 3 years before the history window, so it is fully known when the underwriter decides. Its fill rate differs by class (0.146 vs 0.350) because past claims genuinely predict future claims, not because it reveals the outcome. |

| renewal_offered | leakage | 0.549 | end of policy year | Sierra decides renewal after seeing how the policy year went, so the column is a consequence of the label. It is filled for 95.9% of claim-free drivers and only 50.0% of claim filers. It does not exist at application time, so it was added to leakage_columns. |

| annual_mileage_declared | allowed | 0.280 | at application | Declared by the applicant on the application form before the decision. Its fill rate is nearly equal across classes (0.970 vs 0.966), and more miles means more exposure, which is a legitimate risk signal. |

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?
"renewal_offered" had a correlation below the 0.60 limit (0.549), so it passed the test. A correlation threshold only measures how much a variable predicts a label, not the date when it was recorded. On the data dictionary, it says it was recorded at the end of the year, which is after the decision, therefore it shouldn't be allowed in the test. 

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
V1:
Decision line: DECISION: PASS. This model may proceed to deployment review.
overall AUC: 0.7046

V2:
Decision line: DECISION: BLOCKED. This model may NOT be deployed.
    - subgroup_auc[rural]: Model must be useful for every group, not just the largest.
    - subgroup_tpr[rural]: Claim-free drivers in every group must mostly be offered the standard rate.
    - approval_disparity_ratio: Approval rates across groups must not diverge beyond the four-fifthsscreen.
    - tpr_ratio: Equally safe drivers must have similar chances across groups.
overall AUC: 0.7224

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.
v2 adds "territory_risk_index" at line 136: territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)
and the label is created line 132: logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)
The - 1.10 * rural term penalizes rural drivers regardless of how they drive.

Using the proxy, v2 learns that penalty back. Rural approval drops to 0.51 against 0.92 for urban, so the fairness checks fail.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.
A preventive list check cannot catch a proxy because it only compares the features names in the config with the prohibited list. "territory_risk_index" is not on the list, so it passed, even if it has the same information as "area". The detective outcome check caught it because it measures results per group regardless of which column produced them. 

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added: "min_fpr_ratio": 0.80
And modified "policy_version": "1.1"

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
I chose 0.80 for the FPR rate. A false positive means approving a driver who then files a claim. Sierra loses money, and the driver gets a cheaper rate than their risk justified. If FPR is much lower for rural drivers, risky urban drivers get the benefit of the doubt and rural drivers don’t. It is not just about profit but also about being fair. 

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
My test calls "run_gate" with fake metrics where the right answer is already known. An fpr_ratio of 0.70, which is 0.10 below the threshold, must return BLOCKED, and an fpr_ratio exactly at 0.80 must return PASS. That proves the boundary is >=. Running the pipeline only shows the check on one real model’s numbers. The test proves the check fires on a known bad input and clears a known good one, independent of any model, and it keeps proving that every time the tests run.

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.
Final gate (model_config.json, gradient boosting, policy v1.1):
overall AUC 0.7630 · approval disparity ratio 0.9318 · TPR ratio 0.9761 · FPR ratio 0.9005 · rural AUC 0.7262 / TPR 0.9000 · urban AUC 0.7756 / TPR 0.9220
DECISION: PASS. This model may proceed to deployment review.

**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used five engineered features: claims_per_month, speeding_velocity, hard_brake_trend, night_share_mean and miles_volatility. To see which mattered, I removed one at a time and reran. Removing hard_brake_trend dropped AUC the most, from 0.7630 to 0.7455, with night_share_mean a close second (0.7461) and speeding_velocity next (0.7499). Removing miles_volatility barely changed anything (0.7633), so it adds little.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
Yes. Adding territory_risk_index raised AUC from 0.7630 to 0.7949, but the gate BLOCKED the model. Approval disparity fell to 0.6248, the TPR ratio to 0.7775 and the FPR ratio to 0.5322, all below 0.80. The index is mostly a rural signal, so the extra AUC came from relearning the historical rural penalty in the label, not from better risk prediction. A better model by AUC isn’t necessarily deployable. The gate checks that the model is fair across groups, not just accurate on average.

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
