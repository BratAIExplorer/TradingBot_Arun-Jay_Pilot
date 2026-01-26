# Git Workflow for AI Agents (Claude & Google AI)

## 📋 Commit Message Standards

### Format
```
<type>: <short description>

<detailed description>

Changes:
- File1: Description
- File2: Description

Fixes: #issue_number (if applicable)
```

### Commit Types
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `docs:` Documentation only
- `style:` UI/UX improvements
- `perf:` Performance improvements
- `test:` Adding tests
- `chore:` Maintenance tasks

### Examples
```
fix: resolve stock validation failures and add smart exchange detection

Enhanced symbol validator with retry logic, timeout handling, and smart
NSE/BSE auto-detection. Fixed duplicate CSV entries and improved error
messaging for better user experience.

Changes:
- symbol_validator.py: Added retry logic and smart exchange fallback
- settings_gui.py: Enhanced validation error display with detailed messages
- dashboard_v2.py: Removed duplicate button code causing visibility issues
- config_table.csv: Fixed MARSON exchange and removed duplicate entry
- BUG_TRACKER.md: Updated with all resolved issues

Fixes: #005, #006, #007, #008, #009
```

---

## 🌿 Branching Strategy

### Branch Naming Convention
```
<agent>/<feature-name>
```

**Examples:**
- `claude/fix-validation-errors`
- `google/enhance-settings-gui`
- `main` - Production-ready code

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b claude/feature-name
   ```

2. **Work on Changes**
   - Make focused commits
   - One logical change per commit
   - Test before committing

3. **Before Committing**
   ```bash
   git status          # Review changes
   git diff            # Check modifications
   git add -A          # Stage all changes
   ```

4. **Commit with Good Message**
   ```bash
   git commit -m "type: short description" -m "Detailed explanation..."
   ```

5. **Push to Remote**
   ```bash
   git push origin claude/feature-name
   ```

6. **Merge to Main** (after testing)
   ```bash
   git checkout main
   git merge claude/feature-name
   git push origin main
   ```

---

## ✅ Pre-Commit Checklist

Before committing, verify:
- [ ] Code runs without errors
- [ ] All modified files are staged (`git add`)
- [ ] Commit message follows format
- [ ] Related issues referenced in commit message
- [ ] No sensitive data (passwords, API keys) in commit
- [ ] Documentation updated if needed

---

## 🚫 What NOT to Commit

Never commit:
- `*.pyc` (Python bytecode)
- `__pycache__/` directories
- `.env` files with secrets
- `node_modules/`
- Personal API keys or credentials
- Temporary/test files
- Large binary files (unless necessary)

---

## 📝 Documentation Standards

### Update These Files After Changes

1. **BUG_TRACKER.md**
   - Move fixed bugs to Resolved section
   - Document fix description
   - Add verification status

2. **CHANGELOG.md** (if exists)
   - List all changes by category
   - Include version number
   - Link to commit hashes

3. **README.md** (if feature affects usage)
   - Update installation steps
   - Add new feature documentation
   - Update screenshots if UI changed

---

## 🔄 Common Git Commands

### Status & Inspection
```bash
git status                    # Check current state
git log --oneline -10        # View recent commits
git diff                     # See unstaged changes
git diff --staged            # See staged changes
```

### Staging Changes
```bash
git add -A                   # Stage all changes
git add file.py              # Stage specific file
git add Documentation/       # Stage directory
```

### Committing
```bash
git commit -m "message"                          # Simple commit
git commit -m "title" -m "description"           # Multi-line
git commit --amend                               # Fix last commit
```

### Branching
```bash
git branch                              # List branches
git checkout -b new-branch             # Create & switch
git checkout main                      # Switch to main
git branch -d feature-branch           # Delete branch
```

### Syncing
```bash
git pull origin main            # Get latest from main
git push origin branch-name     # Push your branch
git fetch --all                 # Fetch all remotes
```

### Undoing Changes
```bash
git restore file.py            # Discard unstaged changes
git restore --staged file.py   # Unstage file
git reset --soft HEAD~1        # Undo last commit (keep changes)
git reset --hard HEAD~1        # Undo last commit (discard changes)
```

---

## 🤝 Collaboration Between AI Agents

### Claude & Google AI Working Together

**Rule 1: Branch Isolation**
- Claude works on `claude/*` branches
- Google works on `google/*` branches
- Never work directly on `main` simultaneously

**Rule 2: Communication**
- Update `Documentation/AI_AGENT_HANDOVER.md` after completing work
- Document what you changed and why
- List any pending issues or blockers

**Rule 3: Merge Protocol**
```bash
# Before merging to main:
1. Ensure your branch is up to date
   git checkout your-branch
   git pull origin main        # Merge main into your branch
   git push origin your-branch

2. Test thoroughly

3. Merge to main
   git checkout main
   git merge your-branch
   git push origin main
```

---

## 📊 Commit Frequency

**Good Practice:**
- Commit after completing each logical unit of work
- Typical: 3-10 commits per feature
- Better many small commits than one giant commit

**Commit Granularity:**
- ✅ "fix: add retry logic to validator"
- ✅ "fix: update UI to display error messages"
- ❌ "fix: everything" (too vague)
- ❌ "wip" (work in progress - avoid)

---

## 🎯 Summary

**Remember:**
1. **Descriptive commits** - Future you will thank you
2. **Test before committing** - Don't break main
3. **Sync frequently** - Pull before you push
4. **Document changes** - Update BUG_TRACKER.md
5. **Clear branch names** - `agent/what-you-did`

**When in doubt:**
- Check `git status` first
- Read commit message before confirming
- Ask user before force-pushing or resetting `main`
