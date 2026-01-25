# Contributing to ARUN Trading Bot

First off, thank you for considering contributing to ARUN Trading Bot! It's people like you that make this project better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Collaborative**: Work together towards common goals
- **Be Professional**: Keep discussions focused and constructive
- **Be Inclusive**: Welcome diverse perspectives and experiences

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git for version control
- A GitHub account
- Basic understanding of algorithmic trading concepts

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TradingBot_Arun-Jay_Pilot.git
   cd TradingBot_Arun-Jay_Pilot
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot.git
   ```

4. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

6. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/issues) to avoid duplicates.

When creating a bug report, include:

- **Clear title**: Summarize the issue in the title
- **Description**: Detailed description of the issue
- **Steps to reproduce**: List exact steps to reproduce the bug
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots
- **Environment**:
  - OS: [e.g., Windows 11, macOS 13.0, Ubuntu 22.04]
  - Python version: [e.g., 3.11.5]
  - Bot version: [e.g., 3.0]
- **Additional context**: Any other relevant information

**Example**:
```markdown
## Bug: Dashboard crashes when clicking "Start Engine" with empty symbol list

**Steps to Reproduce**:
1. Open dashboard
2. Go to Settings and clear all symbols from config_table.csv
3. Click "Start Engine"

**Expected**: Bot should show error message "No symbols configured"

**Actual**: Dashboard crashes with "IndexError: list index out of range"

**Environment**:
- OS: Windows 11
- Python: 3.11.5
- Bot Version: 3.0

**Screenshots**: [Attach crash screenshot]
```

---

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title**: Use a descriptive title
- **Problem statement**: Describe the problem you're trying to solve
- **Proposed solution**: Describe your proposed solution
- **Alternatives**: Describe alternative solutions you've considered
- **Benefits**: Explain why this would be useful
- **Additional context**: Add mockups, examples, or references

**Example**:
```markdown
## Feature Request: Add support for multiple timeframes per symbol

**Problem**: Currently each symbol can only have one RSI timeframe, limiting strategy flexibility.

**Proposed Solution**: Allow users to configure multiple timeframes per symbol (e.g., 15T and 30T) and generate signals when both align.

**Benefits**:
- More robust signals with multi-timeframe confirmation
- Reduces false signals
- Common professional trading practice

**Mockup**: [Attach UI mockup if applicable]
```

---

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue`: Simple issues perfect for beginners
- `help wanted`: Issues where we need community help
- `documentation`: Improvements to documentation

---

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features (e.g., `feature/zerodha-adapter`)
- `bugfix/*`: Bug fixes (e.g., `bugfix/order-placement-error`)
- `hotfix/*`: Urgent production fixes

### Creating a Feature Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create and switch to feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Make your changes** in the feature branch
2. **Add tests** for your changes
3. **Run tests** to ensure nothing broke
4. **Update documentation** if needed
5. **Commit your changes** with clear messages

### Keeping Your Branch Updated

```bash
# Fetch latest changes from upstream
git fetch upstream

# Rebase your branch on upstream/main
git rebase upstream/main

# Force push to your fork (only if you haven't pushed yet)
git push -f origin feature/your-feature-name
```

---

## Code Style Guidelines

### Python Style (PEP 8)

Follow [PEP 8](https://pep8.org/) guidelines:

```python
# Good
def calculate_rsi(candles: List[Dict], period: int = 14) -> float:
    """
    Calculate RSI indicator for given candles.

    Args:
        candles: List of candle dictionaries with OHLCV data
        period: RSI calculation period (default: 14)

    Returns:
        RSI value between 0 and 100
    """
    if len(candles) < period:
        raise ValueError(f"Insufficient data: {len(candles)} < {period}")

    # Calculate gains and losses
    gains = []
    losses = []

    for i in range(1, len(candles)):
        change = candles[i]['close'] - candles[i-1]['close']
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)
```

### Key Principles

1. **Type Hints**: Always use type hints for function parameters and return values
   ```python
   def place_order(symbol: str, qty: int, price: float) -> OrderResult:
   ```

2. **Docstrings**: Add docstrings to all public functions and classes
   ```python
   def function_name(param: type) -> return_type:
       """
       Brief description of what the function does.

       Args:
           param: Description of parameter

       Returns:
           Description of return value

       Raises:
           ExceptionType: When this exception is raised
       """
   ```

3. **Function Length**: Keep functions under 50 lines. If longer, consider refactoring.

4. **Variable Names**: Use descriptive names
   ```python
   # Good
   average_entry_price = sum(prices) / len(prices)

   # Bad
   aep = sum(p) / len(p)
   ```

5. **Exception Handling**: NEVER use bare `except:` statements
   ```python
   # Good
   try:
       result = api.get_positions()
   except requests.exceptions.Timeout:
       logger.error("API timeout")
       raise
   except requests.exceptions.ConnectionError as e:
       logger.error(f"Connection failed: {e}")
       raise

   # Bad
   try:
       result = api.get_positions()
   except:
       pass
   ```

6. **Logging**: Use proper logging instead of print statements
   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.info("Starting trading cycle")
   logger.warning("Insufficient capital for trade")
   logger.error(f"API call failed: {error}")
   ```

---

## Testing Guidelines

### Writing Tests

All new code should include tests. Use `pytest` for testing.

```python
# tests/test_rsi_calculation.py
import pytest
from trading_engine import calculate_rsi

def test_rsi_oversold():
    """Test RSI calculation for oversold condition"""
    candles = [
        {'close': 100},
        {'close': 95},
        {'close': 90},
        # ... more candles
    ]

    rsi = calculate_rsi(candles, period=14)
    assert 0 <= rsi <= 100
    assert rsi < 30  # Oversold

def test_rsi_insufficient_data():
    """Test RSI raises error with insufficient data"""
    candles = [{'close': 100}, {'close': 95}]

    with pytest.raises(ValueError, match="Insufficient data"):
        calculate_rsi(candles, period=14)

def test_rsi_all_gains():
    """Test RSI returns 100 when all gains (no losses)"""
    candles = [
        {'close': 100 + i} for i in range(20)  # All increasing
    ]

    rsi = calculate_rsi(candles, period=14)
    assert rsi == 100
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rsi_calculation.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

### Test Coverage

- Aim for at least **70% coverage** for new code
- Critical sections (order placement, risk management) should have **90%+ coverage**

---

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change or bug fix)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

### Examples

```
feat(trading): add support for multiple RSI timeframes

- Allow configuring multiple timeframes per symbol
- Generate signals when all timeframes align
- Add multi-timeframe display in dashboard

Closes #123
```

```
fix(database): add thread safety to prevent data corruption

- Add threading.Lock() for all database writes
- Fixes BUG-003 from audit report
- Prevents race conditions in concurrent write scenarios

See: Documentation/comprehensive_audit_report.md
```

```
docs(readme): update installation instructions

- Add virtualenv setup steps
- Clarify Python version requirements
- Add troubleshooting section
```

---

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest main
2. **Run all tests** and ensure they pass
3. **Run linters** (flake8, mypy)
4. **Update documentation** if needed
5. **Add entry to CHANGELOG.md**

### Submitting PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub with:
   - Clear title following commit message format
   - Detailed description of changes
   - Reference to related issues (e.g., "Closes #123")
   - Screenshots (if UI changes)
   - Checklist of completed items

### PR Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Closes #123
Fixes #456

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] All existing tests pass
- [ ] Added tests for new functionality
- [ ] Manually tested with live broker API
- [ ] Tested in paper trading mode

## Screenshots (if applicable)
[Attach screenshots]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code sections
- [ ] Updated documentation
- [ ] No new warnings or errors
- [ ] Added tests with sufficient coverage
- [ ] All tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD runs tests automatically
2. **Code Review**: Maintainers review your code
3. **Address Feedback**: Make requested changes
4. **Approval**: Once approved, PR will be merged

### After Merge

1. **Delete your feature branch**:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your main branch**:
   ```bash
   git checkout main
   git pull upstream main
   ```

---

## Additional Notes

### Security Issues

**DO NOT** create public issues for security vulnerabilities. Instead, email security@arunbot.com (or project maintainer) privately.

### Questions?

- Check [Documentation](Documentation/)
- Search [existing issues](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/issues)
- Ask in [Discussions](https://github.com/ORIGINAL_OWNER/TradingBot_Arun-Jay_Pilot/discussions)

---

**Thank you for contributing to ARUN Trading Bot!** 🚀
