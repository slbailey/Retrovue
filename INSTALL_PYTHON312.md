# Installing Python 3.12 on Ubuntu/WSL

Retrovue requires Python 3.12 or higher. If your system doesn't have it, follow these steps:

## Option 1: Using deadsnakes PPA (Recommended for Ubuntu/WSL)

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install software-properties-common

# Add deadsnakes PPA (provides newer Python versions)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.12 and required components
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify installation
python3.12 --version
```

## Option 2: Using pyenv (More flexible, works across distributions)

```bash
# Install dependencies
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to your shell profile (~/.bashrc or ~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc

# Install Python 3.12
pyenv install 3.12.0
pyenv global 3.12.0

# Verify installation
python --version
```

## After Installation

Once Python 3.12 is installed, create your venv:

```bash
# Remove old venv if it exists
rm -rf venv

# Create new venv with Python 3.12
python3.12 -m venv venv

# Activate it
source activate.sh

# Install the package
pip install -e .
```

## Verify Setup

```bash
# Check Python version in venv
python --version  # Should show 3.12.x

# Test retrovue command
retrovue --help
```

