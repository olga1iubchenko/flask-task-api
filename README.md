# Claude Code in CI/CD — Team Setup Guide

> How to wire Claude Code into your GitHub repository for automated PR reviews and interactive `@claude` assistance.

---

## What You Get

Once configured, your repo will have two automated workflows:

| Workflow | Trigger | What Claude Does |
|---|---|---|
| **Auto PR Review** | Every pull request opened or updated | Reviews the diff, flags bugs and violations, posts a comment |
| **@claude trigger** | Any comment containing `@claude` | Reads context, answers questions, or pushes fixes |

---

## Prerequisites

- A GitHub repository (public or private)
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)
- Admin access to the repository

---

## Step 1 — Add the API Key to GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret** (not environment secret)
4. Set:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Secret:** your Anthropic API key
5. Click **Add secret**

> ⚠️ Make sure you select **repository secret**, not environment secret. Environment secrets require extra workflow configuration to access.

---

## Step 2 — Install the Claude GitHub App

1. Go to [github.com/apps/claude](https://github.com/apps/claude)
2. Click **Install**
3. Select your repository (or all repositories)
4. Confirm installation

> ⚠️ This step is easy to miss but required. Without the app installed, you will get an OIDC authentication error and the workflows will fail immediately.

Alternatively, if you have Claude Code installed locally, run this in your terminal:
```bash
/install-github-app
```
This walks you through both the app installation and secret setup automatically.

---

## Step 3 — Add the Workflow Files

Create the following two files in your repository. **Commit and push both to your default branch** before opening any pull requests — the OIDC authentication requires the workflow files to exist on the default branch.

### `.github/workflows/claude.yml` — Interactive @claude trigger

```yaml
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest

    permissions:
      contents: write        # so Claude can push commits
      pull-requests: write   # so Claude can post PR comments
      issues: read
      id-token: write        # required for OIDC authentication — do not remove

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0     # full history so Claude understands context

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: --model claude-sonnet-4-6
```

### `.github/workflows/pr-review.yml` — Automated PR review

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest

    permissions:
      pull-requests: write   # to post review comments
      contents: read         # read-only — Claude won't modify code here
      id-token: write        # required for OIDC authentication — do not remove

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            PR NUMBER: ${{ github.event.pull_request.number }}
            REPO: ${{ github.repository }}

            Review the changes in this PR. Check for:
            1. Bugs and missing error handling
            2. Input validation on all POST and PUT routes
            3. Proper HTTP status codes (400 for bad input, 404 for not found)
            4. Code style violations defined in CLAUDE.md

            Be concise. Use bullet points. Flag HIGH PRIORITY issues clearly.
            Do NOT say checks passed if any issues are present.

            After completing your review, post your findings as a comment using:
            gh pr comment ${{ github.event.pull_request.number }} --body "your review here"
          claude_args: --model claude-sonnet-4-6 --allowedTools Read,Grep,Glob,Bash
```

> 💡 **Customise the prompt** to match your team's standards. The more specific it is, the better the review quality. Generic prompts lead to false positives where Claude says everything is fine.

---

## Step 4 — Add a CLAUDE.md to Your Repo

`CLAUDE.md` is read by Claude at the start of every session — including CI runs. Define your team's coding standards here once and they'll be enforced automatically on every PR review.

Create a `CLAUDE.md` in your repo root:

```markdown
# Project Name

## Tech Stack
- Python 3.11, Flask, SQLAlchemy

## Code Standards
- Follow PEP8, max line length 88
- Type hints required on all functions
- Use logger.error() / logger.info() — never print()

## Review Checklist
When reviewing PRs, always check:
1. Input validation on all POST/PUT routes — return HTTP 400 for missing/empty required fields
2. Proper HTTP status codes throughout
3. No raw SQL — use ORM only
4. Tests added for new routes

## Do NOT modify
- migrations/ folder
- config/production.py
```

---

## Step 5 — Verify It Works

1. Create a feature branch and make a change
2. Open a pull request (make sure it's **not a draft**)
3. Go to the **Actions tab** — you should see `Claude PR Review` running
4. After it completes, check the PR for a comment from `claude[bot]`
5. Add a comment on the PR with `@claude explain what this PR does`
6. Go to Actions again — you should see `Claude Code` running
7. After it completes, check the PR for Claude's response

---

## How to Use @claude

Once set up, mention `@claude` in any PR or issue comment:

```
@claude what does this function do?
@claude can you add error handling to this route?
@claude please fix the validation issue and make the tests pass
@claude review this PR for security issues
```

Claude will read the full PR context including all comments, CLAUDE.md, and the codebase before responding.

---

## Customising the Review Prompt

The `prompt` field in `pr-review.yml` controls what Claude checks. Tailor it to your project:

**For security-focused reviews:**
```yaml
prompt: |
  Review this PR for security issues only.
  Check for: SQL injection, XSS, missing auth checks, exposed secrets.
  Post findings via: gh pr comment ${{ github.event.pull_request.number }} --body "..."
```

**For specific file types:**
```yaml
on:
  pull_request:
    paths:
      - 'src/**/*.py'   # only run when Python files change
```

**To skip certain PRs:**
```yaml
jobs:
  review:
    if: |
      github.event.pull_request.draft == false &&
      !contains(github.event.pull_request.labels.*.name, 'skip-claude')
```

---

## Cost Control

| Workflow type | Recommended token budget | Model |
|---|---|---|
| PR review | ~20K tokens | claude-sonnet-4-6 |
| Interactive fix (@claude) | ~60K tokens | claude-sonnet-4-6 |
| Scheduled audit | ~100K tokens | claude-sonnet-4-6 |

Always use `claude-sonnet-4-6` in `claude_args` for CI — it's roughly 5x cheaper than Opus with no meaningful quality difference for routine review tasks.

To raise your token limit: **console.anthropic.com → Settings → Workspaces → your workspace → adjust rate limit**.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Could not fetch an OIDC token` | App not installed OR workflow not on default branch | Install app at github.com/apps/claude; push workflows to default branch |
| `429 Too Many Requests` | Workspace rate limit too low | Raise limit in Anthropic Console or wait 60s |
| `Undefined parameter: model` | Deprecated input used | Use `claude_args: --model claude-sonnet-4-6` not `model:` |
| Review runs but no PR comment | Missing `gh pr comment` in prompt | Add the posting instruction to the end of your prompt |
| Review says "all checks passed" incorrectly | Prompt too generic | Add specific "You MUST flag" instructions to your prompt |
| `@claude` not triggering | App not installed or comment syntax wrong | Verify app install; `@claude` must be a complete word |

---

## Reference

- Official action: [github.com/anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)
- Claude Code docs: [docs.anthropic.com/en/docs/claude-code/github-actions](https://docs.anthropic.com/en/docs/claude-code/github-actions)
- Anthropic Console: [console.anthropic.com](https://console.anthropic.com)