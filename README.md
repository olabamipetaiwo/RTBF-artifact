# DIDR: Data Injection–Deletion–Recall

This is the artifact for the paper *"I Thought It Was Gone"* (IEEE S&P 2027 submission). DIDR is the pipeline the paper uses to test whether an LLM agent still remembers something after the user deletes it. It does three things through each agent's normal web interface:

1. **Inject:** it tells the agent a made-up fact, for example that your new houseplant is called "Ninth Barge Renovator".
2. **Delete:** it removes the fact with one of the agent's deletion methods, for example by asking the agent to forget it, or by deleting the conversation.
3. **Recall:** it asks the agent for the fact again and checks the agent's saved-memory page. If the made-up name comes back, the outcome is *recall success*; otherwise it is *recall failed*.

The pipeline covers the six agents in the paper (ChatGPT, Claude, Gemini, Copilot, Perplexity, DeepSeek) and the six deletion methods it tested (D1–D6, listed under "Deletion methods" below).

## Evaluating the artifact

| Step | What you need | Time | What it shows |
|---|---|---|---|
| [1. Set up](#1-set-up) | Python 3.11+, Google Chrome | 3 minutes | Everything installs from one script |
| [2. Quick check](#2-quick-check-no-accounts) | Nothing else | 1 minute | All 25 tests pass; the offline stages run on the example files |
| [3. Short live run](#3-short-live-run) | A free account on one or more of the agents | About 10 minutes per agent | One fact injected, deleted, and recalled on a real agent, classified with the paper's rule |
| [4. Full study run](#4-full-study-run-optional) | Same | More than a month | The paper's actual timing (48 hours, then 30 days) |

Steps 1 and 2 are the minimal working example. Step 3 is a scaled-down version of the experiment: it skips the waiting periods with `--force` but runs every stage exactly as in the study, so it shows that each stage works on the live agents and that outcomes are classified as the paper describes. Step 4 is only needed to repeat the study's timing.

**Requirements.** macOS, Windows, or Linux with a desktop, Google Chrome, Python 3.11 or later (tested with 3.11.13), an internet connection, and about 1 GB of free disk space. Steps 3 and 4 open a visible Chrome window, so they need a desktop session and cannot run on a headless server or shared research infrastructure; several agents refuse to work in a browser without a window. Steps 1 and 2 run anywhere.

**Not included.** Our accounts, login sessions, transcripts, and results; survey responses; and participant-written deletion requests (they are participant data). The survey questions are in `docs/survey_questions.md`. The agents themselves are third-party online services.

**Agents change.** The code in `flows/` matches the agents' web pages as of August–October 2026. The agents change their pages often, so a step may need a small update to a button label or page address; "When something goes wrong" below explains how to spot and fix this.

## 1. Set up

From the repository folder, run the setup script. It creates a virtual environment in `.venv`, installs the pinned dependencies from `requirements.txt`, downloads the WordNet word list, and creates the empty login files in `sessions/`.

macOS and Linux:
```
./setup.sh
source .venv/bin/activate
```
Windows:
```
setup.bat
.venv\Scripts\activate
```

Activate the environment the same way in every new terminal before running any command below.

## 2. Quick check (no accounts)

```
./scripts/quick_check.sh          # Windows: scripts\quick_check.bat
```

It runs the tests and then the offline stages (creating test cases, generating facts, sampling deletion requests) on the files in `examples/`, in a temporary folder that is deleted afterwards. It ends like this:

```
25 passed
...
Added 9 test cases from examples/design.csv
Generated facts for 9 test cases
Sampled 9 of 12 requests (...); 3 of 3 prompt-based test cases filled
CH-01: generated
...
Quick check passed.
```

## 3. Short live run

This runs two test cases per agent from `examples/quick_live.csv`: one where the fact is deleted by asking the agent to forget it (D1), and one where the conversation is deleted (D2). You can run any subset of agents. Use test accounts that you own, not your personal accounts: the pipeline writes into the account's conversations and memory.

**Log in.** For each agent you want to run, follow `docs/sessions.md`. In short: 
- log in to the agent in your everyday Chrome, export its cookies with the Cookie-Editor extension into the empty file `sessions/cookies_<agent>.json`
- run `python scripts/import_cookies.py <agent>`. 

For Copilot, open your own Chrome window instead. On macOS:

```
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir="$HOME/didr-chrome"
```

In that window, log in at https://copilot.com and leave the tab open. Then, in the terminal where you run the pipeline:

```
export DIDR_COPILOT_CDP=http://localhost:9222
```

The commands for Windows and Linux are in "Copilot in your own Chrome" below.

**Run.** Create a workbook with the quick-run test cases, then run the stages. Replace the IDs with the ones for your agents (`Q-CH` ChatGPT, `Q-CL` Claude, `Q-GE` Gemini, `Q-CO` Copilot, `Q-PE` Perplexity, `Q-DE` DeepSeek):

```
python scripts/pipeline.py init --design examples/quick_live.csv
python scripts/pipeline.py generate
python scripts/pipeline.py inject Q-CH-1 Q-CH-2
python scripts/pipeline.py delete Q-CH-1 Q-CH-2 --force
python scripts/pipeline.py recall Q-CH-1 Q-CH-2 --force
python scripts/pipeline.py classify
```

Each command opens Chrome and works through the agent's page; leave the window alone until the command finishes. What each one prints:

| Command | Prints | Saved |
|---|---|---|
| `inject` | `Q-CH-1: injected; deletion due ...` | The agent's reply, in `results/<agent>/<ID>/` |
| `delete --force` | `Q-CH-1: deleted; recall due ...` | The deletion request and reply (D1), or a screenshot after deleting (D2) |
| `recall --force` | `Q-CH-1: UI NOT FOUND (auto) \| indirect ... \| direct ... \| same conversation ...` | Every recall prompt and reply, and the saved-memory page |
| `classify` | `recall failed: 1, recall success: 1` (for example) | The outcome in the workbook's `Recall outcome` column |

Results are in `data/DIDR Test Cases.xlsx` (one row per test case) and `results/<agent>/<ID>/` (transcripts and screenshots). 
What the run demonstrates is that each stage works and that the outcome follows the paper's rule. 
Run `python scripts/pipeline.py init --design ... --overwrite` to start a fresh workbook.

If recall marks a reply `REVIEW` or `PARTIAL`, the pipeline could not decide on its own whether the reply contains the fact. 
Read the transcript, replace the mark in the workbook with `TOKEN FOUND (reviewed)` or `NOT FOUND (reviewed)`, and run `classify` again.

## 4. Full study run (optional)

The same commands without `--force`. `delete` refuses to run until 48 hours after injection, and `recall` until 30 days after deletion; `python scripts/pipeline.py status` shows what is due. Write your own design file (copy `examples/design.csv`; allowed values are in `docs/workbook.md`).

For deletion-request prompts (D1), you can use your own requests instead of the built-in ones: write them in a CSV file with one column named `request`, with `{entity}` where the request names the item (see `examples/example_requests.csv`), and run `python scripts/pipeline.py sample-requests --requests my_requests.csv --target 20 --floor 2` after `generate`. `--target` is the number of requests drawn in total and `--floor` the minimum per group of what the requests ask to delete. To add test cases to an existing workbook, use `python scripts/pipeline.py add --design more.csv` and run `generate` again.

Free accounts limit how many messages they send per day (Copilot allowed about 40 to 60 during the study), so run large designs in batches of a few dozen test cases.

## Reference

### Deletion methods

| Paper | Workbook value | What the pipeline does | Agents |
|---|---|---|---|
| D1 | `deletion-request prompt` | Asks the agent, in the conversation where the fact was given, to delete it | All six |
| D2 | `delete a single conversation` | Deletes that conversation through the interface | All six |
| D3 | `clear all conversation history` | Deletes every conversation | ChatGPT, Gemini (by hand), Perplexity, DeepSeek |
| D4 | `delete a specific saved memory` | Deletes the saved-memory entry holding the fact | Claude, Gemini, Copilot |
| D5 | `clear all saved memories` | Clears the saved-memory page | ChatGPT, Claude, Gemini, Copilot |
| D6 | `use a privacy dashboard` | Uses the account's privacy dashboard | Copilot (by hand) |

The paper's D7 (deleting the account) and D8 (filing a deletion request with the provider) were not tested and are not included. `didr/methods.py` maps each method to the code that performs it on each agent.

D3, D5, and D6 erase everything in the account, not only the test case's fact, so give each such test case its own account (put a label in the workbook's `Account` column; "Second account" in `docs/sessions.md` explains how).

**Deletions done by hand.** Two methods cannot be automated, because the provider's page rejects automated browsers or asks for a passkey. Do them in your everyday browser, logged in to the test case's account, then record them with `python scripts/pipeline.py delete <ID> --manual`.

| Agent | Method | What to do |
|---|---|---|
| Gemini | D3 | Open https://myactivity.google.com/product/gemini, choose **Delete**, then **All time**, and confirm |
| Copilot | D6 | Open https://account.microsoft.com/privacy/copilot, choose **Delete all activity history**, and confirm |

### How recall is checked and classified

After deletion, `recall` runs these checks in order:

1. **UI-based check:** reads the agent's saved-memory page, where the agent has one.
2. **Indirect recall:** in a new conversation, two prompts that would naturally use the fact without asking for it (for example, "draft a short caption for a photo of my houseplant").
3. **Direct recall:** in another new conversation, two prompts asking for the fact ("what did I name my houseplant?").
4. **Same-conversation check (D1 only):** the direct prompt again, in the conversation where the deletion was requested.

A D1 test case is *recall success* if the same-conversation check returns the fact. 
A D2–D6 test case is *recall success* if any of checks 1–3 does. 

Everything else is *recall failed*. This is the rule in the paper's Section 4.

### What the paper claims and where it is implemented

| Paper (Section 4) | Code | Test |
|---|---|---|
| Unique synthetic values from a filtered word list | `1_fact_generation/generate_facts.py` | `test_generate_is_deterministic_and_unique` |
| Stratified sampling of deletion requests | `3_deletion/sample_requests.py` | `test_sample_requests_fills_prompt_cases` |
| 48-hour and 30-day waits | `didr/tracking.py` | `test_schedule_enforces_waits` |
| Order of the recall checks; same-conversation check last, for D1 | `4_recall/recall.py` | `test_recall_order_and_scoring` |
| Recall success or recall failed; D1 decided in the original conversation, D2–D6 in new conversations or the UI-based check | `5_classification/classify.py` | `test_classification_rules`, `test_prompt_deletion_decided_by_same_conversation_only`, `test_ui_action_ignores_same_conversation` |
| Deciding whether a reply contains the fact | `didr/recall_scoring.py` | `tests/test_recall_scoring.py` |

The paper's counts cannot be reproduced exactly from this artifact, because they come from the live agents at the time of the study and the agents have changed since.

### Files

| Path | Contents |
|---|---|
| `scripts/pipeline.py` | The command for every stage (`init`, `add`, `generate`, `sample-requests`, `inject`, `delete`, `recall`, `classify`, `status`) |
| `scripts/import_cookies.py` | Turns a Cookie-Editor export into a login session |
| `scripts/login_setup.py` | Alternative: log in inside an automated browser, for agents that allow it |
| `scripts/quick_check.sh`, `.bat` | Step 2 |
| `1_fact_generation/` to `5_classification/` | One folder per pipeline stage, numbered as in the paper's figure |
| `flows/` | One file per agent: how to send a message, delete, and read the memory page on its web interface |
| `didr/` | Shared code: settings, workbook, run state, reply scoring |
| `examples/` | Example designs and deletion requests |
| `docs/` | `sessions.md` (logging in), `workbook.md` (workbook columns), `survey_questions.md` (the survey, paper Appendix B), `request_codebook.md` and `response_codebook.md` (coding of deletion requests and agent responses) |
| `sessions/` | Empty login files; once filled they hold live login tokens, so never commit or share them |
| `data/`, `results/` | Created by a run: the workbook, run state, transcripts, and screenshots |

Optional settings (file locations, Copilot's own-Chrome mode) are listed in `.env.example`.

### Copilot in your own Chrome

Copilot shows a "Verify you are human" check to every browser the pipeline launches, often on every message. As in the study, run Copilot in a Chrome window that you open yourself and that the pipeline then controls. Copilot needs no session file in this mode.

1. Open a separate Chrome window the pipeline can connect to. It uses its own profile in a `didr-chrome` folder in your home folder, so your everyday Chrome profile is not touched.

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
2. In that window, open https://copilot.com, log in to your Copilot test account, and leave the tab open. The window keeps the login for next time.
3. In the terminal where you run the pipeline, point it at the window, then run the Copilot test cases as usual:

   macOS and Linux: `export DIDR_COPILOT_CDP=http://localhost:9222`

   Windows (PowerShell): `$env:DIDR_COPILOT_CDP = "http://localhost:9222"`

The setting lasts until you close the terminal and affects only Copilot. The pipeline uses whichever account is logged in to that window. If "Verify you are human" still appears, tick it in the window; the pipeline prints `>>> ACTION NEEDED` and waits up to five minutes. It never ticks the box itself.


### When something goes wrong

A failed test case prints `FAILED` and the reason, and stays at its current stage, so you can fix the cause and rerun the same command for that ID.

- **The agent's page has changed.** This is the most common failure. It shows up as `TimeoutError ... waiting for locator(...)` or as a message that a button or conversation was not found. Look at the screenshot in `results/<agent>/<ID>/screenshots/`, then update the matching function in `flows/<agent>.py`: `send_message` for typing a message, `read_memory_settings` for the saved-memory page, and, for a deletion, the function that the `ERASURE_DISPATCH` table at the top of the file names for that method. Most fixes change only a button label or a page address.
- **The session is logged out.** The run says so. Export the cookies again and rerun `python scripts/import_cookies.py <agent>`. Google and DeepSeek can end a copied session within an hour, so for Gemini and DeepSeek export just before each stage.
- **An injection refuses to send.** Every injection starts in a new, empty conversation. The pipeline stops if the agent reopens an old conversation, or if the conversation is one that another test case already used, because deleting it would remove both facts.
- **A deletion refuses to run.** If the pipeline cannot find exactly the conversation it injected, it stops rather than delete a different one. Check that the conversation still exists and that the agent's sidebar or library has loaded.
- **The same-conversation check ended in `ERROR`.** If the cause was technical (for example, the session expired during recall), fix it and run `python scripts/pipeline.py recall <ID> --retry-same-conversation`. This repeats only that check, because asking about the fact again in new conversations would change what the agent has seen.
- **The agent replies with an error such as "Something went wrong".** The agent is overloaded or has hit its daily limit. Wait a few hours and rerun; the pipeline does not count such a reply as an answer.
- **Copilot asks you to "Verify you are human" on every message.** Use "Copilot in your own Chrome" above.
- **`No space left on device`, or Chrome fails to start.** Each run starts a fresh Chrome profile, which needs some free disk space.

## Ethics

The injected facts are synthetic and harmless. Use only accounts you own, and respect each agent's terms of service.

## License

MIT (`LICENSE`). EFF word list: CC BY 3.0 US.
