# BANA 690A Midterm: Written Answers

**Name: Anahit Grigoryan**
**Last-name group (A to H, I to P, Q to Z): A to H**
**GitHub username: anahitgrigoryan257**

This file is half of your exam. The code and the pipeline grade the other half.
Write in full sentences. Cite evidence from THIS repository: a file name, a line,
a number from `artifacts/gate_report.json` or `artifacts/model_card.md`.
Open book. Individual. Keep each answer short and specific.

---

## Lab 1: Make the data compliant

**1.1** Which four tests failed when you first ran `python -m pytest -q tests/test_lab1_compliance.py`? For each, name the control type (list or detective). 

The initial run had four failures, as described in `README.md`: `test_no_zip_like_column` (detective), `test_no_date_like_column` (detective), `test_no_suspiciously_predictive_column` (detective), and `test_policy_agrees_with_data_dictionary` (detective). These controls inspect the processed data for unsafe patterns or compare policy coverage with the data dictionary.

**1.2** What did you add to `governance/policy.json`, and under which keys?

Add the missing quasi-identifiers to pii_columns and the missing post-year column to leakage_columns. `zip` and `date_of_birth` to `pii_columns` so the quasi-identifiers are dropped, and added `adjuster_fraud_review` and `renewal_offered` to `leakage_columns` because they are post-decision outcomes.

**1.3** Why is the fix in the policy and not in `src/prepare.py`? One or two sentences.

It removes the columns listed by the policy rather than hard-coding specific fields. Updating the policy fixes the missing protections while keeping the control reviewable and avoiding a change to protected pipeline code.
---

## Lab 2: Build features from driving history

Record every feature you implemented. Four minimum, four families minimum, including both families assigned to your last-name group.

| Feature name | Family | Formula in one sentence | Why it should predict claim_free |
| claims_per_month | frequency | Sum `claim_filed` over months 1–24 and divide by 24. | A higher prior claim frequency may indicate a higher chance of another claim. |
| months_since_last_claim | recency | Subtract the latest claim month from decision month 24; use 25 when there was no claim. | A recent claim may indicate higher near-term risk than a more distant claim. |

**2.1** Explain the temporal fence test in your own words. What would have happened to your model in production if a feature had failed it?
The test appends fake, extreme values for months 25–30 and checks that every engineered feature stays unchanged. 
---

## Lab 3: Hunt the leakage

Three suspect columns. For each, give your ruling and the evidence.

| Column | Ruling (leakage or allowed) | Correlation with label | When recorded | Reasoning |
| prior_claims_3y | allowed | 0.243 | at application | This is prior claims information available when the application is assessed; it is listed as an allowed suspect. |
| renewal_offered | leakage | 0.549 | end of policy year | It is recorded after the decision, so it is unavailable at application time even though its correlation is below the 0.60 limit. |
| annual_mileage_declared | allowed | 0.280 | at application | The applicant declares mileage at application, so it is available before the decision; its correlation is below the policy limit. |


**3.1** One of these columns is leakage even though it did not trip the correlation test. Why can a numeric test miss it, and what kind of test catches it?

renewal_offered is leakage despite its 0.549 absolute correlation being below the 0.60 threshold. 

## Lab 4: Run v1 and v2, explain the block

**4.1**
- v1: overall AUC `0.7046`; `DECISION: PASS. This model may proceed to deployment review.`
- v2: overall AUC `0.7224`; `DECISION: BLOCKED. This model may NOT be deployed.`



**4.2**
- [data/generate_data.py](data/generate_data.py#L136): territory_risk_index = np.clip(42 + 30 * rural + rng.normal(0, 8, n), 0, 100).round(1)` generates the index; the data dictionary names its source as a third-party vendor, and rural applicants receive higher values on average.
- [data/generate_data.py](data/generate_data.py#L132): logit = 1.35 + z - 1.10 * rural + rng.normal(0, 1.05, n)` applies an explicit negative rural term to the score used to create the historical label.

**4.3** no_prohibited_features compares feature names against a fixed list, and territory_risk_index is not itself named as a prohibited feature even though it acts as a rural proxy. The outcome-based detective checks caught the resulting disparity: v2 failed subgroup_auc[rural] (`0.5937` < `0.64`), subgroup_tpr[rural]` (`0.5588` < `0.70`), `approval_disparity_ratio` (`0.5596` < `0.80`), and `tpr_ratio` (`0.5888` < `0.80`).

---

## Lab 5: Change the governance

**5.1** What new policy key did you add, and what value did you choose?
I added the policy key min_fpr_ratio with a threshold of in governance/policy.json


**5.2** Defend the value in two or three sentences. What does a false positive mean for Sierra Mutual, and for the driver? Why is unequal FPR across urban and rural drivers a fairness problem, not only a profit problem?


An FPR is the share of drivers who later filed a claim but were approved as if they were claim-free; for Sierra Mutual this can mean unpriced claim costs, while for the driver it means receiving standard-rate approval rather than being routed to manual review. A large urban/rural FPR gap means claim-filing applicants in one group are let through at a different rate, raising a fairness concern as well as a financial one.


**5.3** Describe the test you wrote in `tests/test_lab5_gate.py`. What does it prove that running the pipeline alone does not?

test_gate_blocks_fpr_gap checks that an fpr_ratio 0.10 below the policy threshold returns 'BLOCKED', and that a ratio exactly at the threshold returns 'PASS'. This tests both sides of the gate’s boundary with controlled metrics; an ordinary pipeline run only reports the result for the one model and dataset used in that run.


---

## Lab 6: Beat the gate

**6.1** Paste your final gate table (from the terminal or `artifacts/gate_report.json`): overall AUC, disparity ratio, TPR ratio, FPR ratio, DECISION.

Forgot to copy

**6.2** Which engineered features did you use, and which one mattered most? How do you know?

claims_per_month and months_since_last_claim. 


**6.3** Did you try `territory_risk_index`? What happened, and what does that tell you about the difference between a better model and a deployable model?

The v2 configuration used `territory_risk_index` and achieved higher overall AUC (0.7224 versus v1’s 0.7046), but was BLOCKED after rural subgroup AUC, rural TPR, approval disparity, and TPR-ratio checks failed.
---

## Lab 7: Request deployment

Fill in the pull request template on GitHub. Then answer here:

**7.1** The workflow paused with "awaiting approval" before it ran. Which control is that, in the language of owner, trigger and evidence?


forgot to copy

**7.2** After approval, what did Stage A print about your governance change? Quote it.
Governance change is a tightening or an addition. Allowed, pending owner review. Integrity check passed
---

## Lab 8 (bonus): Break it and watch it stop

**8.1** What did you change on your second branch, and what did `python run_pipeline.py --config configs/v2.json` print locally?

**8.2** What did Stage A print on GitHub? Quote the refusal line.

**8.3** Which control would NOT have stopped this change on its own, and why do we need both?

---

## Declaration

I completed this exam individually, using only the permitted materials.

**Signature (type your name):* Anahit Grigoryan*
