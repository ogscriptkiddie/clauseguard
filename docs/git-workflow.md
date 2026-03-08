# ClauseGuard — Git Workflow Guide

This is your personal reference for pushing work to GitHub.
Read this once, then follow the commands every time you make changes.

---

## ONE-TIME SETUP (do this once ever)

### Step 1 — Create the repo on GitHub
1. Go to github.com and log in
2. Click the green "New" button (top left)
3. Repo name: `clauseguard`
4. Set it to PUBLIC (so employers/LinkedIn can see it)
5. Do NOT check "Add README" — we already have one
6. Click "Create repository"
7. GitHub will show you a page with setup commands. Copy your repo URL.
   It will look like: https://github.com/YOUR_USERNAME/clauseguard.git

### Step 2 — Connect your local folder to GitHub
Open your terminal, navigate to your clauseguard folder, then run:

```bash
git init
git add .
git commit -m "Phase 1: Backend engine — rule-based classifier, Flask API, risk scoring"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/clauseguard.git
git push -u origin main
```

That's it. Your code is now on GitHub.

---

## EVERY TIME YOU MAKE CHANGES (the daily workflow)

These are the only 3 commands you need to remember:

```bash
git add .
git commit -m "describe what you changed"
git push
```

### What each command does:
- `git add .`         → stages all your changed files (tells git "these are the changes I want to save")
- `git commit -m "…"` → creates a save point with a message explaining what you did
- `git push`          → sends that save point up to GitHub

---

## HOW TO WRITE GOOD COMMIT MESSAGES

This matters for LinkedIn and employers. Think of commit messages as a changelog that tells a story.

Good examples:
  "Phase 1: Add Flask API with /analyze endpoint"
  "Add negation detection to rule-based classifier"
  "Add annotation CSV with 50 labeled Google ToS clauses"
  "Phase 2: Chrome extension content script — extracts ToS text from active tab"
  "Evaluation: Rule-based F1=0.71, ML F1=0.84 — ML outperforms baseline"

Bad examples:
  "update"
  "fix"
  "changes"
  "asdfgh"

The rule: if someone reads only your commit messages, they should understand the entire arc of your project.

---

## BRANCH STRATEGY (use this when building new phases)

When you start a new phase, create a branch so main always has working code:

```bash
# Start a new phase
git checkout -b phase-2-extension

# ... do your work, make commits ...

# When the phase is done and working, merge it back
git checkout main
git merge phase-2-extension
git push
```

Branches for this project:
  main                  → always stable, working code
  phase-2-extension     → Chrome extension work
  phase-3-ml            → ML classifier work
  phase-4-evaluation    → Evaluation scripts

---

## CHECKING WHAT'S CHANGED

```bash
git status        # shows which files have changed
git diff          # shows exactly what lines changed
git log --oneline # shows your full commit history as a clean list
```

---

## IF SOMETHING BREAKS

```bash
# See your commit history
git log --oneline

# Go back to a previous working commit temporarily
git checkout COMMIT_HASH

# Come back to latest
git checkout main
```

---

## YOUR LINKEDIN POST (template)

Once Phase 1 is pushed, you can post this:

"Just shipped Phase 1 of ClauseGuard — a tool I'm building that automatically 
reads Terms of Service documents and classifies privacy/security risks using 
NLP and machine learning.

Phase 1: Backend rule-based classifier (Python + Flask + spaCy) with 
negation detection and a weighted 0–100 risk scoring system.

Next up: Chrome extension and ML classifier (scikit-learn).

Open source: github.com/YOUR_USERNAME/clauseguard

#Python #CyberSecurity #NLP #OpenSource #UFV"
