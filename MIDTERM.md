# BANA 690A Midterm: Written Answers

**Name:** Carlos
**Last-name group (A to H, I to P, Q to Z):** Herrera
**GitHub username:** carlosherrera206

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective).
test_no_zip_like_column Detective control
test_no_date_like_column detective control
test_no_suspiciously_predictive_column detective control
test_policy_agrees_with_data_dictionary detective control

**1.2** What did you add to `governance/policy.json`, and under which keys?
added zip and date of birth to pii columns and i added adjuster froud review to leakage column

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.
 its in polict because the code already enforces what the policy says. the fauilre happed because the policy was incomplete so chaning the policy enforces it better rather than hard coding specific columns onto the code

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

claims_per_month | frequency | total prior claims /24 months | drivers with more prior claims will probably be less likely to remain claim free

months_since_last_claim | recency | 25 = the most recent month with a claim with 25 meaning no claim occurred | a more recent claim may indicate higher future risks claims

miles_volatility | volatility | S.D of monthly miles / by average month;y miles | inconsistant driving volume may capture unstable driving patters

night_share_mean | ratio | average shaare of miles driven at night | more night driving may associated with differenct claim risk.


**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?

The temporal fence means every freature must use only informaiton availible by the decision date, which on here is 1-24 months. if a failure used months 25-30, it would use future info that would not exist when the real decision is made, creating leakage and making the model seem better in training than it would in real life. 

---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
|---|---|---|---|---|
| prior_claims_3y | | | | |
| renewal_offered | | | | |
| annual_mileage_declared | | | | |

prior_claims_3y | allowed| recorded at applivation| existed when the underwritting deicison was made so its not in future info

renewal_offered|leakage| correlation about 0.549 |recorded at end of policy year | it did not exist at decision time so using it would leak future info

annual_milage_declared | allowed | recorded at application | it was availible when the decision was made

prior_claims_3y 0.243     0.146     0.350  at application 
annual_mileage_declared 0.280     0.970     0.966 at application 


**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

a numeric test can miss leakage becasue a future variable does not have to have really high correlation with the lable to still be unavailble at the decision time. a timeline test catches this by checking wehn the variable was recorded and whether it existed at the moment the model would actually make its decision

---

## Lab 4: Run v1 and v2, explain the block

**4.1** Paste the DECISION line and overall AUC for v1 and for v2.

DECISION: PASS. This model may proceed to deployment review.  overall AUC 0.7046   accuracy 0.7350

DECISION: BLOCKED. This model may NOT be deployed.  overall AUC 0.7224   accuracy 0.7117


**4.2** v2 has the higher AUC. Why is it blocked? Point to the exact line in `data/generate_data.py` that creates `territory_risk_index`, and the line that creates the label's rural penalty.

territory_risk_index is largely built from rural indicator so it acts as a proxy for area. the label generation formula also subtracts from rural applicants meaning the historical outcome contains a ruaral penalty that the model can learn 

**4.3** v2 passed `no_prohibited_features`. Explain why a preventive list check cannot catch a proxy, and name the detective check that did.

the preventative check only compares feature names against the prohibited feature list so it can miss a proxy whose neame is not forbidden. the detective outcome checks measure model results by group so they can detect the unfair effect even when the protected attribute is not directly used itself 

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
min_fpr_ratio with threshold of 0.75 and policy version 1.1

**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?

A flase possitive means sierra approves driver who later files a claim which can create financial loss for sierra. Unequal FPR across groupsis also a fairness problem because the group with the lower fpr is held to stricter standard while risky drivers in other group recieve more benefit of the doubt.

**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

running the pipeline only shows that the fpr check works for one models actual results. the unit rest proves the control itself works by showing what bad fpr ratio is blocked and a value exactly at the threshold passes

---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

Final model: overall AUC 0.8198, approval disparity ratio 0.8775, TPR ratio 0.9922, FPR ratio 0.9295, Decision: PASS
**6.2** Which engineered features did you use, and which one mattered most? How do you know?

the engineered driving history features improved performance over the baseline while still passing all govt checks. i know they mattered because the final model using them achived a higher AUC than v1 while remaining within the fairness thresholds.

**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

adding territory_risk_index increased overall AUC to 0.8421, but approval disparity dropped to 0.6460 and fpr ratio to 0.5855, causing the model to be blocked. this shows that a feature can improve predictive accuracy while acting as a procy that worsens fiarness outsomes so it should not be kept just becuase it improves AUC
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
