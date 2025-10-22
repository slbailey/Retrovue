# 🤝 Contributing to Retrovue

Thank you for your interest in contributing to Retrovue! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## 📜 Code of Conduct

### Our Standards

- **Be respectful** and inclusive to all contributors
- **Be constructive** when providing feedback
- **Focus on what's best** for the community and project
- **Show empathy** towards other community members

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher installed
- FFmpeg installed and in your PATH
- Git for version control
- A GitHub account

### Fork and Clone

1. Fork the Retrovue repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Retrovue.git
   cd Retrovue
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/slbailey/Retrovue.git
   ```

### Development Setup

**Windows (PowerShell):**

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install flake8 mypy pytest pytest-cov black isort
```

**macOS/Linux (bash):**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install flake8 mypy pytest pytest-cov black isort
```

### Verify Installation

```bash
# Test the CLI
python -m cli.plex_sync --help

# Run tests
pytest tests/ -v
```

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, documented code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run linter
flake8 .

# Run type checker
mypy cli/ src/retrovue/ --ignore-missing-imports

# Run tests
pytest tests/ -v --cov
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: Add feature description"
```

#### Commit Message Format

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style/formatting
- `refactor:` Code refactoring
- `test:` Test updates
- `chore:` Build/config changes

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📝 Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use `black` for code formatting: `black .`
- Use `isort` for import sorting: `isort .`
- Maximum line length: 127 characters
- Use type hints where appropriate

### Code Quality

- **Write docstrings** for all public functions and classes
- **Keep functions focused** - one function, one responsibility
- **Use meaningful variable names** - avoid single-letter variables except in loops
- **Add comments** for complex logic or non-obvious code

## 🧪 Testing

### Writing Tests

- Place tests in the `tests/` directory
- Use pytest for test framework
- Aim for good test coverage (>80%)
- Test both success and failure cases

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_cli.py -v

# Run with coverage
pytest tests/ -v --cov=cli --cov=src/retrovue --cov-report=term-missing

# Run in offline mode (no network calls)
PLEX_OFFLINE=1 pytest tests/ -v
```

## 📤 Submitting Changes

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

### Pull Request Process

1. **Create a PR** with a clear title and description
2. **Link related issues** using "Fixes #123" or "Relates to #456"
3. **Fill out the PR template** completely
4. **Wait for CI checks** to pass
5. **Address review feedback** promptly
6. **Squash commits** if requested

## 📚 Documentation

### Documentation Updates

When making changes, update relevant documentation:

- **Code Comments**: Document complex logic
- **Docstrings**: Keep function/class documentation current
- **README**: Update if user-facing features change
- **Documentation Files**: Update guides in `documentation/` folder

## 🎯 What to Contribute

### High-Priority Areas

- **Bug Fixes**: Always welcome!
- **Test Coverage**: Help improve test coverage
- **Documentation**: Improve guides and examples
- **Performance**: Optimize slow operations

### Feature Development

Check the [Development Roadmap](documentation/development-roadmap.md) for planned features.

## 💬 Communication

### Where to Ask Questions

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code-specific discussions

## 📄 License

By contributing to Retrovue, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Retrovue!** 🎉📺

