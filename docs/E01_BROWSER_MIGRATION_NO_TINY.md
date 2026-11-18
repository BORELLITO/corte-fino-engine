# Browser migration for VERBO NO CHÃO — TinyFish to Playwright / ChatGPT Work

**Policy decision:** Stop relying on the TinyFish connector for project browsing. Do not remove or uninstall it from the user's other projects. Do not use it for this E01. No accounts, cookies, passwords, upload tokens or login form attempts are transferred.

## Public unattended research — GitHub Actions Playwright

- The new `agents/e01_public_browser_playwright.py` actually launches **Chromium** in GitHub Actions (standard runner, free for public repositories subject to GitHub fair use).
- Visits only 3 explicitly allowlisted **public pages** (IANA example.com canary, Playwright CI documentation, Agnes pricing documentation). Does not click, sign up, accept billing, generate a video, solve CAPTCHAs, use proxies, scrape aggressively or bypass a provider's terms.
- Saves a sanitized status report and an image of **example.com only**. All artifacts expire after 1 day. Report red when the canary/browser cannot navigate; a provider site refusing access is reported as BLOCKED, not falsely claimed accessible.
- This is NOT a persistent authenticated human-like browser. GitHub runners are short-lived, so sessions are deliberately not persisted.
- Workflow: `.github/workflows/verbo-no-chao-public-playwright-browser.yml`. No secrets required.
- Primary docs: https://playwright.dev/docs/ci ; https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job

## Sites requiring login — native ChatGPT Work Cloud Browser

- Supported on eligible paid ChatGPT plans via **Work mode**, not automatically activated from an ordinary chat.
- It holds its own separate authenticated sessions and pauses for secure login/2FA; login may require **one user action**. There is no lawful or reliable browser tool to bypass site authentication by promise.
- Official help: https://help.openai.com/pt-br/articles/20001280-using-cloud-browser-in-chatgpt
- For this project, prefer already-connected GitHub/Drive tools and authenticated API providers. Work Cloud Browser is for site-native steps where APIs/integrations cannot help.

## Video generation source

Agnes 2.5 Flash promotional free API is an alternative candidate (720P, 4–12s, 9:16, optional first frame). Endpoint `POST https://apihub.agnes-ai.com/v1/videos` requires user-owned `AGNES_API_KEY`. Offer is temporary and reported free queue can be congested. Current price must be verified before submission from the actual account (not only from a cached public page). Until a key and an account-level zero-cost entitlement are confirmed, no generation should occur; no blind retries or credential printing. Official catalog: https://github.com/AgnesAI-Labs/skills/blob/main/agnes-ai-models/references/model_catalog.md

**Status before CI:** files authored, browser test pending; no generated video and no spend.
