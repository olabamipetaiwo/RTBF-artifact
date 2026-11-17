# DIDR: Data Injection–Deletion–Recall pipeline

Artifact for *"I Thought It Was Gone"* (IEEE S&P 2027 submission). DIDR injects a synthetic fact into an LLM agent, applies a deletion method, and checks 30 days later whether the fact can still be recalled. It drives each agent's web interface with Playwright.

> The flows in `flows/` reflect the agents' interfaces as of August–October 2026 and may need updating. The offline stages and tests do not depend on the agents.

**Not included:** our accounts, sessions, transcripts, results, survey responses, or participant-written deletion requests. The survey questionnaire (questions only) is in `docs/survey_questions.md`.

## Components

| DIDR stage | Code | Command |
|---|---|---|
| Synthetic fact generation | `1_fact_generation/` | `generate` |
| Injection (prompt / UI action) | `2_injection/` | `inject` |
| Deletion-request sampling | `3_deletion/sample_requests.py` | `sample-requests` |
| Deletion (prompt / UI action), ≥48 h after injection | `3_deletion/delete.py` | `delete` |
| Recall (UI check, indirect, direct), ≥30 days after deletion | `4_recall/` | `recall` |
| Outcome classification | `5_classification/` | `classify` |
| Agent automation | `flows/` | |

Test cases are rows in one workbook, `data/DIDR Test Cases.xlsx` (see `docs/workbook.md`).

## Setup

You need Python 3.11 or later (tested with 3.11.13) and Google Chrome. From the `didr` folder, run the setup script. It creates a virtual environment in `.venv`, installs the pinned dependencies from `requirements.txt`, and downloads the WordNet word list:

```
./setup.sh                       # on Windows: setup.bat
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
```

Activate the environment the same way in every new terminal before running the commands below. If you prefer to set it up yourself, the script runs `python -m venv .venv`, `pip install -r requirements.txt`, and `python -c "import nltk; nltk.download('wordnet')"`.

## Try it without any accounts

These commands run the tests and walk through the offline stages with the example files, so you can see how the pipeline works before touching a live agent:

```
python -m pytest tests/
python pipeline.py init --design examples/design.csv
python pipeline.py generate
python pipeline.py sample-requests --requests examples/example_requests.csv --target 10 --floor 2
python pipeline.py status
```

## Running it on live agents

Use only accounts that you own. A full run takes more than a month, because the pipeline waits 48 hours between injection and deletion and another 30 days before checking recall.

ChatGPT, Claude, Copilot, and Perplexity show a bot check (such as Cloudflare's "Just a moment..." page) to any browser that Playwright controls, even when you are logged in. For these four agents the pipeline uses `playwright-stealth`, which hides those automation signals so it can run on your own logged-in account, as we did in the study. It is installed with the other dependencies; you do not need to do anything.

**1. Log in.** Most agents block logins made by an automated browser, so you log in with your everyday Chrome and copy that login over. `docs/sessions.md` walks you through it: you install the Cookie-Editor extension, export each agent's cookies into its empty file in `sessions/`, and run `python import_cookies.py <agent>`.

**2. Describe your test cases.** Make a copy of `examples/design.csv` and edit it. Each row is one test case: an ID of your choice, the agent, how the fact is injected, and how it is deleted (`docs/workbook.md` lists the allowed values). Then create the workbook and generate a synthetic fact for each test case:

```
python pipeline.py init --design my_design.csv
python pipeline.py generate
```

**3. Add deletion requests.** Skip this step if none of your test cases use a deletion-request prompt. Otherwise, write the requests in a CSV file with a single column named `request`, putting `{entity}` wherever the request should name the injected item (see `examples/example_requests.csv`). The pipeline groups the requests by what they ask to delete and draws a sample from each group. `--target` is how many requests to draw in total, and `--floor` is the minimum taken from each group:

```
python pipeline.py sample-requests --requests my_requests.csv --target 20 --floor 2
```

**4. Inject the facts.** `python pipeline.py inject <ID> ...` opens the agent and discloses each test case's fact. It prints when the test case becomes due for deletion.

**5. Delete them, at least 48 hours later.** `python pipeline.py delete <ID> ...` applies each test case's deletion method and prints when recall becomes due. Two methods have to be done by hand; see below.

**6. Check recall, at least 30 days later.** `python pipeline.py recall <ID> ...` asks the agent about the fact and checks its saved-memory page where one exists.

**7. Classify the outcomes.** Sometimes the pipeline cannot tell on its own whether a reply contains the fact, and marks it `REVIEW` or `PARTIAL` in the workbook. Read the saved transcript in `results/<agent>/<ID>/`, replace the mark with `TOKEN FOUND (reviewed)` or `NOT FOUND (reviewed)`, and then run `python pipeline.py classify`.

At any point, `python pipeline.py status` shows where each test case is. `delete` and `recall` refuse to run before a test case is due; adding `--force` skips the wait, which is useful only for trying the pipeline out.

### Deletions done by hand

Two deletion methods cannot be automated. Do them yourself in your everyday browser, logged in to the test case's account, and then tell the pipeline with `python pipeline.py delete <ID> --manual`.

| Agent | Method (paper) | Why it has to be done by hand | What to do |
|---|---|---|---|
| Copilot | Use a privacy dashboard (D6) | The dashboard asks for a passkey or security key | Open https://account.microsoft.com/privacy/copilot, choose **Delete all activity history**, and confirm |
| Gemini | Clear all conversation history (D3) | Google's activity page rejects automated browsers | Open https://myactivity.google.com/product/gemini, choose **Delete** → **All time**, and confirm |

Some deletion methods, including these two, erase everything on the account, not only the test case's fact. Give each such test case its own account, so it does not wipe out the facts of your other test cases; "Second account" in `docs/sessions.md` explains how.

## Claims supported

| Paper (Section 4) | Code | Test |
|---|---|---|
| Unique synthetic values, filtered word list | `1_fact_generation/generate_facts.py` | `test_generate_is_deterministic_and_unique` |
| Stratified sampling of deletion requests | `3_deletion/sample_requests.py` | `test_sample_requests_fills_prompt_cases` |
| 48 h / 30 day timeline | `didr/tracking.py` | `test_schedule_enforces_waits` |
| Recall check order; same-conversation check last, for deletion-request prompts | `4_recall/recall.py` | `test_recall_order_and_scoring` |
| Recall success / recall failed; D1 decided in the original conversation, D2–D6 in new conversations or the UI check | `5_classification/classify.py` | `test_classification_rules`, `test_prompt_deletion_decided_by_same_conversation_only`, `test_ui_action_ignores_same_conversation` |
| Reply scoring | `didr/recall_scoring.py` | `tests/test_recall_scoring.py` |

The paper's counts are not reproducible from this artifact: they come from live agents at a point in time.

## Documentation

- `docs/sessions.md`: logging in with Cookie-Editor
- `docs/survey_questions.md`: survey questionnaire (paper, Appendix B)
- `docs/request_codebook.md`: coding of deletion requests (seven wording dimensions)
- `docs/response_codebook.md`: coding of agent responses to deletion requests
- `docs/workbook.md`: test-case workbook columns

## Ethics

Facts are synthetic and non-sensitive. Use only accounts you own and respect each agent's terms of service. Sessions and results are git-ignored.

## License

MIT (`LICENSE`). EFF word list: CC BY 3.0 US.
