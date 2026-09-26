# Aparty Git Workflow & Branch Protection Guide

This document defines how the `main` branch is protected and how changes reach it.

## Core Rules

1. **No direct pushes to `main`.** All code goes through a Pull Request.
2. **Merge only when green.** A PR can be merged only after all GitHub Actions checks pass.
3. **Keep PRs focused and reviewable.** There is no hard line limit, but prefer a logical set of commits, each with a clear message (English, describing the change).

## How to Configure Branch Protection in GitHub

1. Open the repository on GitHub, then **Settings → Branches → Add branch ruleset** (or **Add branch protection rule**).
2. Set the **branch name pattern** to `main` (or target the default branch).
3. Enable:
   - **Require a pull request before merging** (1 approval; dismiss stale approvals on new commits).
   - **Require status checks to pass before merging** and **Require branches to be up to date**. Add these checks (type their names in the search box after the first CI run):
     - `Tests: iam-service`
     - `Tests: catalog-service`
     - `Tests: order-service`
     - `Tests: notification-service`
     - `Tests: telegram bot`
     - `Frontend Client (Vite Build & Lint)`
     - `Microservices Syntax & Compile Check`
     - `Docker Compose Validation`
   - **Do not allow bypassing the above settings**, and restrict who can push to `main`.
4. Save.

## Developer Workflow

1. Create a branch from the latest `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```
2. Commit in logical steps, run the tests of what you changed, and push:
   ```bash
   git push -u origin feat/your-feature-name
   ```
3. Open a PR against `main` and fill in the template checklist.
4. Wait for the checks to turn green, get a review, then squash-merge.
