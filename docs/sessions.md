# Logging in: sessions from Cookie-Editor

The pipeline drives each agent while logged in to your account. Most agents block logins performed by an automated browser (Google sign-in rejection, Cloudflare checks), so log in in your everyday Chrome and copy that login into the pipeline with the Cookie-Editor extension.

`sessions/` holds an empty file for each export below. Once filled, these files hold live login tokens: never commit, share, or paste them anywhere else.

## 1. Install Cookie-Editor

1. In Chrome, open the Chrome Web Store and search for **Cookie-Editor**.
2. Click **Add to Chrome**, then **Add extension**.
3. Pin it: click the puzzle-piece icon in the toolbar, then the pin next to Cookie-Editor.

## 2. Export the cookies for each agent

Repeat for every agent you will test.

1. In your everyday Chrome, open the agent and log in to the account you will use for the experiments.

   | Agent | Open |
   |---|---|
   | ChatGPT | https://chatgpt.com |
   | Claude | https://claude.ai |
   | Gemini | https://gemini.google.com |
   | Copilot | https://copilot.com |
   | Perplexity | https://www.perplexity.ai |
   | DeepSeek | https://chat.deepseek.com |

2. With the agent's tab active, click the Cookie-Editor icon.
3. Click **Export**, then **JSON**. The cookies are copied to the clipboard.
4. Open the agent's empty file in `sessions/`, paste the clipboard into it, and save:

   | Agent | Paste into |
   |---|---|
   | ChatGPT | `sessions/cookies_chatgpt.json` |
   | Claude | `sessions/cookies_claude.json` |
   | Gemini | `sessions/cookies_gemini.json` |
   | Copilot | `sessions/cookies_copilot.json` |
   | Perplexity | `sessions/cookies_perplexity.json` |
   | DeepSeek | `sessions/cookies_deepseek.json` |

> **Copilot:** we recommend running Copilot in your own Chrome window instead of a cookie session, because Copilot asks a pipeline-launched browser to verify you are human on every message. See "Copilot: use your own Chrome" in the README. The cookie steps below still work if you prefer them.

## 3. Copilot and DeepSeek: also copy localStorage

These two keep part of the login in the page's localStorage, which cookies do not cover.

1. On the agent's tab, open the developer console: **View → Developer → JavaScript Console** (or Cmd+Option+J / Ctrl+Shift+J).
2. Type the line below and press Enter. If Chrome asks you to type `allow pasting` first, do so.
   ```
   copy(JSON.stringify(localStorage))
   ```
3. Open the agent's empty file, paste the clipboard into it, and save:
   - Copilot: `sessions/localstorage_copilot.json`
   - DeepSeek: `sessions/localstorage_deepseek.json`

## 4. Convert to a session

With the virtual environment active (`source .venv/bin/activate`, see the README), run this for each agent:
```
python import_cookies.py <agent>
```
This writes `sessions/<agent>.json`, the session the pipeline loads. A warning that no login token was found means the export was taken while logged out; log in and export again.

## Further cases

- **Second account** (for account-wide deletion methods, which need a dedicated account): log in to that account, paste its export into `sessions/cookies_<agent>__<label>.json` (and `localstorage_<agent>__<label>.json` for Copilot or DeepSeek), run `python import_cookies.py <agent> --account <label>`, and put `<label>` in the workbook's Account column.
- **Second domain** (Gemini's activity page, Copilot's privacy page): log in on https://myactivity.google.com or https://account.microsoft.com/privacy, export from that tab into `sessions/cookies_<agent>_<domain>.json`, then run `python import_cookies.py <agent> --merge <domain>`.
- **Expired session**: when a run reports a sign-in page or a logged-out session, export the cookies again and rerun step 4.

`login_setup.py` (log in inside the automated browser) remains as an alternative for agents that allow it.
