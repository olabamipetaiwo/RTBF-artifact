# DIDR: Data Injection–Deletion–Recall pipeline

Artifact for *"I Thought It Was Gone"* (IEEE S&P 2027 submission). DIDR injects a synthetic fact into an LLM agent, applies a deletion method, and checks 30 days later whether the fact can still be recalled. It drives each agent's web interface with Playwright.

> The flows in `flows/` reflect the agents' interfaces as of August–October 2026. The agents change their pages often, so expect to update a flow now and then; see "When something goes wrong" below. The offline stages and tests do not depend on the agents.

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

You need Python 3.11 or later (tested with 3.11.13) and Google Chrome. From the repository folder, run the setup script. It creates a virtual environment in `.venv`, installs the pinned dependencies from `requirements.txt`, and downloads the WordNet word list:

```
./setup.sh                       # on Windows: setup.bat
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
```

Activate the environment the same way in every new terminal before running the commands below. If you prefer to set it up yourself, the script runs `python -m venv .venv`, `pip install -r requirements.txt`, and `python -c "import nltk; nltk.download('wordnet')"`.

## Try it without any accounts

These commands run the tests and walk through the offline stages with the example files, so you can see how the pipeline works before touching a live agent:

```
python -m pytest tests/
python scripts/pipeline.py init --design examples/design.csv
python scripts/pipeline.py generate
python scripts/pipeline.py sample-requests --requests examples/example_requests.csv --target 10 --floor 2
python scripts/pipeline.py status
```

## Running it on live agents

Use only accounts that you own. A full run takes more than a month, because the pipeline waits 48 hours between injection and deletion and another 30 days before checking recall.

ChatGPT, Claude, Copilot, and Perplexity show a bot check (such as Cloudflare's "Just a moment..." page) to any browser that Playwright controls, even when you are logged in. 

**1. Log in.** Most agents block logins made by an automated browser, so you log in with your everyday Chrome and copy that login over. `docs/sessions.md` walks you through it: you install the Cookie-Editor extension, export each agent's cookies into its empty file in `sessions/`, and run `python scripts/import_cookies.py <agent>`. For Copilot, use your own Chrome window instead (see "Copilot: use your own Chrome" below).

**2. Describe your test cases.** Make a copy of `examples/design.csv` and edit it. Each row is one test case: an ID of your choice, the agent, how the fact is injected, and how it is deleted (`docs/workbook.md` lists the allowed values). Then create the workbook and generate a synthetic fact for each test case:

```
python scripts/pipeline.py init --design my_design.csv
python scripts/pipeline.py generate
```

To add more test cases later without touching the existing ones, put them in another CSV file and run `python scripts/pipeline.py add --design more.csv`, then `python scripts/pipeline.py generate` again; it fills only the new rows.

**3. Add deletion requests.** Skip this step if none of your test cases use a deletion-request prompt. Otherwise, write the requests in a CSV file with a single column named `request`, putting `{entity}` wherever the request should name the injected item (see `examples/example_requests.csv`). The pipeline groups the requests by what they ask to delete and draws a sample from each group. `--target` is how many requests to draw in total, and `--floor` is the minimum taken from each group:

```
python scripts/pipeline.py sample-requests --requests my_requests.csv --target 20 --floor 2
```

**4. Inject the facts.** `python scripts/pipeline.py inject <ID> ...` opens the agent and discloses each test case's fact. It prints when the test case becomes due for deletion.

**5. Delete them, at least 48 hours later.** `python scripts/pipeline.py delete <ID> ...` applies each test case's deletion method and prints when recall becomes due. Two methods have to be done by hand; see below.

**6. Check recall, at least 30 days later.** `python scripts/pipeline.py recall <ID> ...` asks the agent about the fact and checks its saved-memory page where one exists.

**7. Classify the outcomes.** Sometimes the pipeline cannot tell on its own whether a reply contains the fact, and marks it `REVIEW` or `PARTIAL` in the workbook. Read the saved transcript in `results/<agent>/<ID>/`, replace the mark with `TOKEN FOUND (reviewed)` or `NOT FOUND (reviewed)`, and then run `python scripts/pipeline.py classify`.

Each command opens a Chrome window and drives it. Leave the window alone until the command finishes; clicking in it or closing it makes the step fail. Transcripts and screenshots of every step are saved in `results/<agent>/<ID>/`.

Agents limit how many messages a free account can send in a day (Copilot allowed about 40 to 60 during the study). Inject and recall in batches of a few dozen test cases, with a pause between batches.

At any point, `python scripts/pipeline.py status` shows where each test case is. `delete` and `recall` refuse to run before a test case is due; adding `--force` skips the wait, which is useful only for trying the pipeline out.

### Deletions done by hand

For deletion methods cannot be automated. Do them yourself in your everyday browser, logged in to the test case's account, and then tell the pipeline with `python scripts/pipeline.py delete <ID> --manual`.


### Copilot: use your own Chrome

Copilot shows a "Verify you are human" check to every browser the pipeline launches, often on every message. As in the study, run Copilot in a Chrome window that you open yourself, which the pipeline then controls. Copilot does not need a session file in this mode.

**1. Open a Chrome window the pipeline can connect to.** Copy the whole line for your system into a terminal. It starts a separate Chrome with its own profile in a `didr-chrome` folder in your home folder, so your everyday Chrome profile is not touched (Chrome allows remote control only of a separate profile).

macOS:
```
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$HOME/didr-chrome"
```
Windows (PowerShell):
```
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:USERPROFILE\didr-chrome"
```
Linux:
```
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/didr-chrome"
```

**2. Log in.** In that new window, open https://copilot.com, log in to the account for your Copilot test cases, and leave the tab open. The window keeps the login, so next time you only reopen it with the same command.

**3. Point the pipeline at it** in the terminal where you run the pipeline, then run the stages as usual:

macOS and Linux:
```
export DIDR_COPILOT_CDP=http://localhost:9222
python scripts/pipeline.py inject <Copilot IDs>
```
Windows (PowerShell):
```
$env:DIDR_COPILOT_CDP = "http://localhost:9222"
python scripts/pipeline.py inject <Copilot IDs>
```

The setting stays on until you close that terminal, and it only affects Copilot. The pipeline uses whichever account is logged in in that window and ignores the workbook's Account column for Copilot, so for a test case on a second account, log that account in before running it. If "Verify you are human" still appears, tick it in the window; the pipeline waits up to five minutes.

### When something goes wrong

A failed test case prints `FAILED` and the reason, and is left at its current stage, so you can fix the cause and rerun the same command for that ID.

- **The agent's page has changed.** This is the most common failure. It shows up as `TimeoutError ... waiting for locator(...)` or as a message that a button or conversation was not found. Look at the step's screenshot in `results/<agent>/<ID>/screenshots/`, then update the matching function in `flows/<agent>.py`: `send_message` for typing a message, `read_memory_settings` for the saved-memory page, and, for a deletion, the function that the `ERASURE_DISPATCH` table at the top of the file names for that deletion method. Most fixes only change a button label or a page address. During our own test run in November 2026, ChatGPT, Claude, and Perplexity had each changed at least one of these since the study.
- **An injection refuses to send.** The pipeline starts every injection in a new, empty conversation and stops if the agent reopens an old one, or if the conversation turns out to be one that another test case already used. Two facts in one conversation would make both test cases invalid, because deleting that conversation removes both.
- **A deletion refuses to run.** When the pipeline cannot find exactly the conversation it injected, it stops instead of deleting the nearest one, so it never deletes another test case's data. Check that the conversation still exists and that the agent's sidebar or library has loaded.
- **A same-conversation check ended in `ERROR`.** If the cause was technical (for example, the session expired during recall), fix it and run `python scripts/pipeline.py recall <ID> --retry-same-conversation`. This repeats only that check, because asking about the fact again in new conversations would change what the agent has seen.
- **The run reports that the session is logged out.** The session has expired. Export the cookies again and rerun `python scripts/import_cookies.py <agent>` (see `docs/sessions.md`). DeepSeek can log a copied session out within an hour, so export its cookies and localStorage just before each stage.
- **Copilot asks you to "Verify you are human" on every message.** Run Copilot in your own Chrome window ("Copilot: use your own Chrome" above). When the box appears, the pipeline prints `>>> ACTION NEEDED` and waits up to five minutes for you to tick it; it never ticks the box itself.
- **Any other bot check ("Just a moment...") appears.** Export fresh cookies from your everyday Chrome and rerun.
- **The agent replies with an error such as "Something went wrong".** The agent is overloaded or has hit its daily limit. Wait a few hours and rerun; the pipeline does not count such a reply as an answer.
- **`No space left on device`, or Chrome fails to start.** Each run starts a fresh Chrome profile, which needs some free disk space. Free a few gigabytes and rerun.

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
