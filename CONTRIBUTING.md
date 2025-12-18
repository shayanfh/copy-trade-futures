# Contributing to Copy Trade Futures Bot

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and professional
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## How to Contribute

### 1. Report Bugs

If you find a bug, please open an issue with:

- **Title:** Clear, descriptive title
- **Description:** What happened and what you expected
- **Steps to Reproduce:** How to reproduce the issue
- **Environment:** Python version, OS, dependencies
- **Logs:** Relevant error messages or logs

Example:
```
Title: Bot crashes when receiving signal with missing targets

Description:
The bot crashes with a KeyError when receiving a signal that doesn't include targets.

Steps to Reproduce:
1. Send a signal without targets field
2. Bot crashes

Environment:
- Python 3.9
- Windows 10
- pyrogram 1.4.16

Error:
KeyError: 'Targets'
```

### 2. Suggest Features

For feature requests, open an issue with:

- **Title:** Feature description
- **Use Case:** Why this feature is needed
- **Proposed Solution:** How it should work
- **Alternatives:** Other approaches considered

Example:
```
Title: Add support for trailing stop loss

Use Case:
Users want to automatically adjust stop loss as price moves in their favor.

Proposed Solution:
Add a new signal parameter: trailing_stop_percent = 2%

Alternatives:
- Manual stop loss adjustment (current)
- Fixed stop loss (current)
```

### 3. Submit Code Changes

#### Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/copy-trade-futures.git
cd copy-trade-futures
```

#### Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

#### Make Changes

1. Follow the code style (see below)
2. Add comments for complex logic
3. Test your changes thoroughly
4. Update documentation if needed

#### Code Style Guidelines

**Python Style:**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

**Example:**
```python
# Good
def calculate_position_size(balance, leverage, risk_percent):
    """Calculate position size based on risk management rules."""
    risk_amount = balance * (risk_percent / 100)
    position_size = risk_amount * leverage
    return position_size

# Bad
def calc_pos(b, l, r):
    return b * (r / 100) * l
```

**Comments:**
```python
# Good - explains WHY
# Use 40% of balance to avoid liquidation in volatile markets
max_position = balance * 0.4

# Bad - explains WHAT (code already shows this)
# Multiply balance by 0.4
max_position = balance * 0.4
```

**Naming Conventions:**
- Functions: `snake_case` - `get_balance()`, `set_leverage()`
- Classes: `PascalCase` - `Binance`, `Signals`
- Constants: `UPPER_SNAKE_CASE` - `MAX_LEVERAGE`, `API_TIMEOUT`
- Private: `_leading_underscore` - `_internal_method()`

#### Commit Messages

Write clear, descriptive commit messages:

```bash
# Good
git commit -m "Add trailing stop loss support for long positions"
git commit -m "Fix: Handle missing targets in signal parsing"
git commit -m "Refactor: Extract API retry logic to separate function"

# Bad
git commit -m "fix bug"
git commit -m "update code"
git commit -m "changes"
```

Format:
```
[Type]: Brief description (50 chars max)

Detailed explanation if needed (wrap at 72 chars)
- Explain what changed
- Explain why it changed
- Reference issues if applicable

Fixes #123
```

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation
- `test:` - Tests
- `perf:` - Performance improvement

#### Testing

Before submitting, test your changes:

```bash
# Run the bot locally
python src/main.py

# Check for syntax errors
python -m py_compile src/*.py

# Test with sample data
python -c "from src.models import *; print('Database OK')"
```

#### Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
# - Describe what you changed
# - Reference related issues
# - Explain why this change is needed
```

### 4. Documentation

Help improve documentation:

- Fix typos
- Clarify confusing sections
- Add examples
- Update outdated information

## Project Structure

```
copy-trade-futures/
├── src/
│   ├── main.py           # Core bot logic
│   ├── binance_api.py    # Binance API wrapper
│   ├── models.py         # Database models
│   ├── panel.py          # Telegram UI
│   └── excel.py          # Excel utilities
├── config/
│   ├── bot.ini           # Configuration (not in repo)
│   └── bot.ini.example   # Configuration template
├── data/                 # Sample data
├── logs/                 # Application logs
├── tests/                # Unit tests (future)
├── README.md             # Project overview
├── SETUP.md              # Setup guide
├── CONTRIBUTING.md       # This file
└── requirements.txt      # Dependencies
```

## Key Components

### Signal Processing (`src/main.py`)

The `Halakui` class handles incoming signals:

```python
class Halakui:
    def do(self):
        # Parse signal format
        # Extract parameters
        # Open orders on all accounts
        # Store in database
```

To add a new signal format:
1. Add parsing logic in `do()` method
2. Extract symbol, leverage, entry, targets, stop loss
3. Call `open_order_all()` with parameters
4. Store in database

### API Wrapper (`src/binance_api.py`)

The `Binance` class wraps Binance Futures API:

```python
class Binance:
    def market_long(self, symbol, size, ClientOrderId=None):
        """Open a long market order."""
        # Implementation
```

To add a new API method:
1. Add method to `Binance` class
2. Use `self.client` to call Binance API
3. Handle errors appropriately
4. Return formatted response

### Database Models (`src/models.py`)

Uses Peewee ORM:

```python
class Signals(BaseModel):
    id_signal = TextField(unique=True)
    symbol = TextField()
    # ... other fields
```

To add a new model:
1. Create class inheriting from `BaseModel`
2. Define fields
3. Add to `create_db_tables()`

### Telegram UI (`src/panel.py`)

Handles user interactions:

```python
class MyButtonHandler:
    def run(self):
        # Handle button clicks
        # Execute trading actions
        # Send responses
```

## Performance Considerations

When contributing, keep these in mind:

1. **API Rate Limiting** - Binance has rate limits
2. **Database Queries** - Use indexes for frequently queried fields
3. **Memory Usage** - Avoid loading all data into memory
4. **Concurrency** - Use APScheduler for background tasks

## Security Considerations

- Never log sensitive data (API keys, secrets)
- Validate all user inputs
- Use HTTPS for external APIs
- Sanitize error messages
- Keep dependencies updated

## Testing

While the project doesn't have automated tests yet, please:

1. Test your changes locally
2. Test with multiple accounts if possible
3. Test error scenarios
4. Document test cases

## Documentation

Update documentation for:

- New features
- API changes
- Configuration options
- Troubleshooting steps

## Review Process

1. **Automated Checks** - Code style, syntax
2. **Code Review** - Functionality, security, performance
3. **Testing** - Manual testing on multiple environments
4. **Approval** - Merge when approved

## Questions?

- Check existing issues and discussions
- Review the README and SETUP guide
- Look at similar code in the project
- Ask in a new issue

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes

Thank you for contributing! 🎉

---

**Last Updated:** December 2024
