# 🛡️ Aparty Git Workflow & Branch Protection Guide

This document defines the rules and steps for protecting the `main` branch, enforcing Pull Request workflows, and ensuring that **this PR's total diff contains at most 200 lines of code**.

---

## 📌 Core Rules

1. **Direct Pushes to `main` are Strictly Prohibited:**
   - All code must be introduced via a Pull Request (PR).
   - No developer or maintainer may push commits directly to `main`.

2. **Merge Only When Green (CI Passes):**
   - A PR can only be merged after all GitHub Actions automated tests pass.
   - If any test or validation fails, merging is blocked.

3. **PR Diff Size Limit (Max 200 Lines Total):**
   - This PR's total diff must touch **200 lines or fewer** (sum of additions and deletions, excluding lockfiles and assets).
   - Because squash merging is used, keeping the whole PR diff under 200 lines ensures the resulting commit landing on `main` is clean, concise, easy to review, and simple to revert if needed.
   - Large features must be broken down into multiple smaller, reviewable PRs.

---

## ⚙️ How to Configure Branch Protection in GitHub

Follow these steps in your GitHub repository:

### Step 1: Open Branch Protection Settings
1. Go to your repository on GitHub: `https://github.com/<owner>/Aparty`.
2. Click **Settings** (tab at the top).
3. In the left sidebar, under **Code and automation**, click **Branches**.
4. Click **Add branch ruleset** (or **Add branch protection rule**).

### Step 2: Set Branch Name Pattern
- Set **Branch name pattern** to: `main`
- (Or if using Rulesets, target: `Default branch`).

### Step 3: Enable Protection Policies
Check the following settings:

- [x] **Require a pull request before merging**
  - **Required approvals:** `1`
  - **Dismiss stale pull request approvals when new commits are pushed:** Checked
  - **Require review from Code Owners:** (Optional, if CODEOWNERS file is used)

- [x] **Require status checks to pass before merging**
  - **Require branches to be up to date before merging:** Checked
  - Add the following status checks (type their names in the search box after the first CI run):
    - `Check PR Diff Size (<= 200 lines)`
    - `Backend Tests (Pytest + PostgreSQL + Redis)`
    - `Frontend Client (Vite Build & Lint)`
    - `Microservices Syntax & Compile Check`
    - `Docker Compose Validation`

- [x] **Do not allow bypassing the above settings**
  - Applies these rules to everyone, including repository administrators.

- [x] **Restrict who can push to matching branches**
  - Leave list empty or specify only automated deployment bots to prevent direct pushes.

5. Click **Save changes** (or **Create**).

---

## 👨‍💻 Developer Workflow

### 1. Branching Strategy
Always create a branch from latest `main`:
```bash
git checkout main
git pull origin main
git checkout -b feat/your-feature-name
```

### 2. Keep PR Total Diff Under 200 Lines
Write code and keep the overall scope focused:
```bash
# Check how many lines changed against main
git diff --shortstat origin/main...HEAD -- . ':!package-lock.json' ':!yarn.lock' ':!*.png' ':!*.jpg' ':!*.svg'
```

### 3. Check PR Diff Size Locally
You can test your branch at any time before pushing or opening a PR:
```bash
./scripts/check_commit_size.sh origin/main
```

Or install the automatic pre-push hook:
```bash
./scripts/setup_git_hooks.sh
```

### 4. How to Split a PR That Exceeds 200 Lines
If your total diff exceeds 200 lines, split it into smaller PRs:
1. Identify independent layers:
   - PR 1: Database models and schemas (`models.py`, `schemas.py`).
   - PR 2: Business logic and endpoints (`routers/`, `services/`).
   - PR 3: Frontend UI / integration.
2. Create separate branches and open smaller, focused PRs:
   ```bash
   # Branch 1 for models & schemas
   git checkout -b feat/feature-models
   git commit -m "feat(api): add schemas and models"
   git push -u origin feat/feature-models
   ```

### 5. Open Pull Request & Merge When Green
1. Push your branch:
   ```bash
   git push -u origin feat/your-feature-name
   ```
2. Open a PR against `main`. Fill in the PR template checklist.
3. Wait for GitHub Actions to turn green (✅).
4. Request review from a teammate.
5. Once approved and green, squash-merge into `main`!
