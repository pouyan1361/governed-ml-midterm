# BANA 690A Midterm: Written Answers

**Name:Kelly Altamira**
**Last-name group (A to H, I to P, Q to Z): A**
**GitHub username:kellyaltamira892**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
test_no_zip_like_column -list; test_no_date_like_column-list; test_no_suspiciously_predictive_column-detecitve; test_policy_agrees_with_data_dictionary-detective 


**1.2** What did you add to `governance/policy.json`, and under which keys?
under pii columns, the variable zip and date of birth were added
under data leakage the var adjuster fraud review was added.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
It is under policy becasue we must restrict this information from being used as it violates governance guidlines. The vars zip, date of birth and adjuster fraud review all feature sensitive infromation that cannot be utilized in our model.
---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

claims per month : frequency=> Total previous claims per month. Drivers with higher claims from the past may be likely to file claims in the future.

months since last claim: recency=>month minus most recent claim from 25, Drivers with more recency have a hgher risk of future claims.

speeding velocity: velocity=> ratio of recent six month speeding rate by the overall speeding plus0.1. Increasing speeding behavior may indicate higher accident risk.

miles volatility: volatility=>Divide the standard deviation of monthly miles by the average monthly miles. nconsistent driving patterns may indicate changes in risk exposure.

max hard brakes per 1k: extremes=> Calculate hard brakes per 1,000 miles each month and take the highest value. Frequently hard braking may indicate risky driving.

hard brake trend: trend=>Subtract the first 12-month hard-braking rate from the last 12-month rate. ncreasing hard braking may indicate worsening driving behavior.

night share mean: ratio=> average monthyl shares of miles driven at night. more nightime driving may increase the exposure to higher risk conditions for driving.

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
For Lab 2, I implemented seven features from different families to help predict whether a driver will remain claim-free. Claims per month measures the frequency of past claims, while months since last claim measures how recently a claim occurred. Speeding velocity tracks changes in speeding behavior, and miles volatility measures how much monthly driving distance varies. Maximum hard brakes per 1,000 miles identifies extreme braking behavior, while hard brake trend shows whether braking habits are improving or worsening. Lastly, night share mean measures the average percentage of driving done at night. Temporal Fence Test: The temporal fence test ensures that the model only uses driving information from months 1 through 24, before the insurance decision is made. If a feature failed this test, the model would be using future information that would not be available in production.
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

prior_claims_3y is allowed because it contains previous claim information recorded at application time. renewal_offered is classified as leakage because it is recorded at the end of the policy year, after the insurance decision has already been made. Although its correlation with the label is approximately 0.549, it still contains future information. Lastly, annual_mileage_declared is allowed because it is provided by the applicant at application time. All three columns have correlations below the 0.60 threshold, but only renewal_offered violates the timeline rule.

**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it? A numeric correlation test can miss leakage because a feature does not need to have a strong correlation with the target variable to contain future information. 

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.
V1: DECISION: PASS. This model may proceed to deployment review. overall AUC 0.7046
V2 : DECISION: BLOCKED. This model may NOT be deployed.
    - subgroup_auc[rural]: Model must be useful for every group, not just the largest.
    - subgroup_tpr[rural]: Claim-free drivers in every group must mostly be offered the standard rate.
    - approval_disparity_ratio: Approval rates across groups must not diverge beyond the four-fifths screen.
    - tpr_ratio: Equally safe drivers must have similar chances across groups. overall AUC 0.7224

**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

Model v2 achieved a higher AUC of 0.7224 compared to v1's 0.7046, but it failed the governance gate because its predictions were less fair to rural drivers. The territory_risk_index increases risk scores for rural drivers, while the rural penalty in the logit calculation lowers their likelihood of being labeled claim-free.
line 136=>`territory_risk_index`: risk score based on drivers depending where the live.
line 131=> rural penalty: The code creates a score called logit that helps determine whether a driver is classified as claim-free.

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.
The preventive list check passed because territory_risk_index was not explicitly listed as a prohibited feature, even though it acted as a proxy for rural status. The detective checks identified unequal approval rates, low rural AUC, and low rural TPR, which caused v2 to be blocked despite its higher overall accuracy.
---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added the new policy key min_fpr_ratio and selected a threshold of 0.70.

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?
 I chose 0.70 because it helps reduce unfair differences between rural and urban drivers while allowing some flexibility. A false positive means the model approves a driver who later files a claim, potentially causing financial losses for Sierra Mutual, while the driver receives the standard rate despite being classified as higher risk by the outcome.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?
I added a test that checks whether the governance gate blocks a model when its FPR ratio falls below 0.70 and allows it to pass when the ratio meets the threshold.
---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.
overall AUC 0.8215   accuracy 0.7892
  rural  n=342   AUC 0.7993  approval 0.7251  TPR 0.9059  FPR 0.5465
  urban  n=858   AUC 0.8347  approval 0.8228  TPR 0.9220  FPR 0.4764
  disparity ratio 0.8813   TPR ratio 0.9825   FPR ratio 0.8717

[stage 5] Deployment gate
==============================================================================
  DEPLOYMENT GATE   model v3   policy v1.1
==============================================================================
  check                                    value   threshold   result
------------------------------------------------------------------------------
  no_prohibited_features                    none        none   pass
  overall_auc                             0.8215        0.68   pass
  subgroup_auc[rural]                     0.7993        0.64   pass
  subgroup_tpr[rural]                     0.9059        0.70   pass
  subgroup_auc[urban]                     0.8347        0.64   pass
  subgroup_tpr[urban]                     0.9220        0.70   pass
  approval_disparity_ratio                0.8813        0.80   pass
  tpr_ratio                               0.9825        0.80   pass
  fpr_ratio                               0.8717        0.70   pass
==============================================================================
  DECISION: PASS. This model may proceed to deployment review.
**6.2** Which engineered features did you use, and which one mattered most? How do you know?
I used engineered features including claims_per_month, months_since_last_claim, speeding_velocity, miles_volatility, max_hard_brakes_per_1k, and night_share_mean. These features help the model evaluate previous claims and driving behavior to predict whether a driver will remain claim-free. I believe claims_per_month is an important feature because previous claims can indicate future risk.
**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?
 I compared the results of v1 and v2, which included territory_risk_index. Model v2 achieved a higher AUC of 0.7224 compared to v1's 0.7046, but it failed the governance gate because of unfair outcomes for rural drivers. This shows that a model can have better predictive performance but still be unsuitable for deployment if it fails fairness requirements.
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

**Signature (type your name): Kelly Altamira**
