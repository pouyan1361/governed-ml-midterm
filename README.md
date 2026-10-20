# BANA 690A Midterm: Governed ML Pipeline, Sierra Mutual Edition

A midterm you do with your hands. Same machinery as Week 5 (policy as code,
tests as controls, a deployment gate, a model card, an audit log, a CI
workflow, a pull request that waits for approval), a new business, a new
dataset, and this time **you are also the governance team**.

Instructor repo: `github.com/pouyan1361/governed-ml-midterm`
Open book. Individual. In class. Eight labs, the eighth is bonus.


## The business

Sierra Mutual sells one-year auto policies. At application time an underwriter
decides whether to offer the **standard rate** (approve) or route the applicant
to **manual review** at a higher rate (decline). The model predicts
`claim_free`: 1 if the driver filed no at-fault claim during the policy year.
Score at or above the threshold means approve.

Historical underwriting penalized rural drivers more than their driving
justified. That penalty is in the label. Your job is to build a model that is
useful and does not learn it back.

## Step 0: fork and open a Codespace (do this first)

1. On GitHub, open `pouyan1361/governed-ml-midterm` and click **Fork**. Keep
   the name. Create the fork under your own account.
2. On YOUR fork, click the green **Code** button, choose the **Codespaces**
   tab, click **Create codespace on main**.
3. **Wait for the line `Setup complete` in the terminal** (about two minutes).
   The Python packages install in the background after the editor opens.
   Do not type anything before that line appears.
4. In the Codespace terminal, run:

       python -m pytest -q tests/test_lab1_compliance.py

   You should see **4 failed, 7 passed**. That is the correct starting point.
5. **If instead you see `ModuleNotFoundError: No module named 'pandas'`**, the
   setup did not finish. Install the packages yourself, wait for it to end
   (about a minute), then run the test again:

       pip install -r requirements.txt
       python -m pytest -q tests/test_lab1_compliance.py

6. If a Codespace is stuck on "Opening Remote" for more than three minutes,
   delete it from the Codespaces tab on your fork and create a new one.

## The files

    governance/policy.json        the committee's rules (incomplete on purpose)
    data/policies_raw.csv         one row per applicant, with problems on purpose
    data/driving_history.csv      24 months of telematics BEFORE the decision
    data/history_after_decision.csv  months 25 to 30. Never read it. A test checks.
    data/data_dictionary.csv      what every column is and WHEN it was recorded
    data/generate_data.py         how the data and its traps were made (read it)
    src/prepare.py                policy-driven cleaning (you do not edit this)
    src/features.py               LAB 2: your engineered features
    src/leakage_checks.py         LAB 3 tool: the three leakage tests in Python
    src/gate.py                   LAB 5: add a check
    tests/test_lab1_compliance.py LAB 1 controls
    tests/test_lab2_features.py   LAB 2 controls (temporal fence)
    tests/test_lab3_leakage.py    LAB 3 control (rulings)
    tests/test_lab5_gate.py       LAB 5: write the last test
    tests/test_lab6_submission.py LAB 6 submission checks
    configs/v1.json, v2.json      the baseline and the tempting model
    model_config.json             LAB 6: your model
    MIDTERM.md                    LABS 1 to 8: your written answers
    ci/check_policy_integrity.py  Stage A: tighten yes, loosen no
    .github/workflows/            the automated gate

## The labs

| Lab | What you do | Done when |
|---|---|---|
| 1 | Complete the policy so the detective tests pass | `pytest -q tests/test_lab1_compliance.py` shows 11 passed |
| 2 | Implement `claims_per_month` (guided) and at least four more features from four families | `pytest -q tests/test_lab2_features.py` passes and `python src/features.py` lists your features |
| 3 | Rule on three suspect columns in the policy | `pytest -q tests/test_lab3_leakage.py` shows 3 passed |
| 4 | Run v1 and v2, read the evidence, explain the block in MIDTERM.md | Both runs complete; MIDTERM.md Lab 4 answered |
| 5 | Add an FPR-ratio check to the gate, a threshold to the policy, a test that proves it fires | `pytest -q tests/test_lab5_gate.py` shows 5 passed, 0 skipped |
| 6 | Edit `model_config.json`: highest overall AUC that PASSES, using at least two engineered features | `python run_pipeline.py` ends with DECISION: PASS; `pytest -q tests/test_lab6_submission.py` passes |
| 7 | Branch, commit, push, open a pull request to the instructor repo, fill the template | PR open; after approval the checks are green |
| 8 (bonus) | On a second branch, loosen a threshold and watch Stage A refuse it | Quote the refusal in MIDTERM.md |

## Commands you will use

    python -m pytest -q tests/test_lab1_compliance.py
    python -m pytest -q tests/                      # everything
    python src/features.py                          # which features are implemented
    python src/leakage_checks.py                    # the three leakage tests
    python run_pipeline.py --config configs/v1.json
    python run_pipeline.py --config configs/v2.json
    python run_pipeline.py                          # your model_config.json

## Rules of the road

- You may edit: `governance/policy.json`, `src/features.py`, `src/gate.py`,
  `tests/test_lab5_gate.py`, `model_config.json`, `MIDTERM.md`.
- You may not edit anything else. Stage A fails the pull request if you do.
- You may tighten a threshold or add a protection. You may not loosen one.
- Commit only your own files. Branch name: `student/firstname-lastname`.
- Everything is synthetic. Nothing here is a real person.
