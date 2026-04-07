# Cross-Platform Environment Guide for Claude Code

How to work correctly across macOS, Windows, WSL, and Linux. Covers package management, Python virtual environments, shell differences, path conventions, and platform-specific gotchas that cause Claude Code to make mistakes.

---

## Table of Contents

1. [Platform Detection](#1-platform-detection)
2. [Shell Differences](#2-shell-differences)
3. [Python Environment Management](#3-python-environment-management)
4. [Package Managers by Platform](#4-package-managers-by-platform)
5. [File System Differences](#5-file-system-differences)
6. [Node.js and JavaScript Tooling](#6-nodejs-and-javascript-tooling)
7. [Git Configuration Across Platforms](#7-git-configuration-across-platforms)
8. [Docker and Containers](#8-docker-and-containers)
9. [WSL-Specific Guide](#9-wsl-specific-guide)
10. [Common Mistakes Claude Code Makes](#10-common-mistakes-claude-code-makes)

---

## 1. Platform Detection

Before running platform-specific commands, detect the environment:

```bash
# In bash/zsh
case "$(uname -s)" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="macos";;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="windows";;
esac

# Check if WSL specifically
if grep -qi microsoft /proc/version 2>/dev/null; then
    PLATFORM="wsl"
fi

echo "Platform: $PLATFORM"
```

Claude Code exposes the platform in its environment context. Check `uname` output or `/etc/os-release` on Linux to determine the specific distribution.

### Quick Reference

| Check | macOS | Linux/WSL | Windows (Git Bash) |
|-------|-------|-----------|-------------------|
| Shell | zsh (default) | bash (default) | bash (Git Bash) |
| Package manager | brew | apt/dnf/pacman | choco/scoop/winget |
| Python | `python3` | `python3` | `python` or `py` |
| Open browser | `open` | `xdg-open` | `start` |
| Clipboard copy | `pbcopy` | `xclip -sel clip` | `clip` |
| Notifications | `osascript` | `notify-send` | PowerShell toast |
| File paths | `/Users/name` | `/home/name` | `C:\Users\name` |
| Line endings | LF | LF | CRLF (configure git!) |

---

## 2. Shell Differences

### macOS (zsh default since Catalina)
```bash
# Config file
~/.zshrc

# Array syntax differs from bash
my_array=(one two three)    # No 'declare -a' needed

# Extended glob is built-in
setopt extendedglob

# Homebrew paths
# Apple Silicon: /opt/homebrew/bin
# Intel: /usr/local/bin
eval "$(/opt/homebrew/bin/brew shellenv)"  # Apple Silicon
```

### Linux/WSL (bash default)
```bash
# Config file
~/.bashrc

# Source profile on login shells
~/.bash_profile  # or ~/.profile

# Extended glob needs enabling
shopt -s extglob
```

### Key Differences That Cause Bugs

| Feature | bash | zsh |
|---------|------|-----|
| Array indexing | 0-based | 1-based (by default) |
| `echo` flags | `echo -e` works | `echo -e` may not work, use `print -P` |
| Word splitting | On by default | Off for `$var` |
| Config file | `.bashrc` | `.zshrc` |
| Glob no match | Error | Error (use `setopt null_glob` to suppress) |

### Safe Cross-Platform Patterns
```bash
# Use printf instead of echo for portability
printf '%s\n' "Hello world"

# Use $() instead of backticks
result=$(command)  # Good
result=`command`   # Bad (nesting issues)

# Use [[ ]] instead of [ ] for conditionals
[[ -f "$file" ]]   # Good (handles spaces, no word splitting)
[ -f "$file" ]     # Works but more fragile
```

---

## 3. Python Environment Management

### CRITICAL RULE: NEVER Use --break-system-packages

On modern Ubuntu/Debian (23.04+), `pip install` outside a virtual environment fails with:

```
error: externally-managed-environment
```

**The WRONG fix** (that Claude often defaults to):
```bash
# NEVER DO THIS
pip install --break-system-packages somepackage
# Also NEVER do this
sudo pip install somepackage
```

This corrupts the system Python that apt/dpkg depend on. It can break system tools, package managers, and even the OS update process.

**The CORRECT fix** - always use a virtual environment:

### Option A: venv (built-in, recommended for most cases)
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate      # Linux/macOS/WSL
.venv\Scripts\activate         # Windows CMD
.venv\Scripts\Activate.ps1     # Windows PowerShell

# Now pip works normally
pip install somepackage

# Deactivate when done
deactivate
```

### Option B: uv (fast, modern, recommended for new projects)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with virtual environment
uv init myproject
cd myproject
uv venv

# Install packages (much faster than pip)
uv add requests flask pytest

# Run commands in the venv
uv run python script.py
uv run pytest
```

### Option C: conda/miniconda (data science, multiple Python versions)
```bash
# Install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Create environment
conda create -n myproject python=3.12
conda activate myproject

# Install packages
conda install numpy pandas scikit-learn
pip install other-package  # pip works inside conda envs
```

### Virtual Environment Best Practices

1. **One venv per project.** Store in project root as `.venv/` (gitignored).
2. **Activate before any pip command.** If you see `pip install` without activation, stop.
3. **Pin dependencies.** `pip freeze > requirements.txt` or use `pyproject.toml` with `uv`.
4. **gitignore the venv.** Add `.venv/` to `.gitignore`. Never commit it.
5. **Document activation.** Put the activation command in CLAUDE.md and README.

### Per-Platform Python Locations

| Platform | System Python | User Install | Recommended |
|----------|--------------|--------------|-------------|
| macOS | `/usr/bin/python3` (Apple) | `brew install python` | brew python + venv |
| Ubuntu/Debian | `/usr/bin/python3` | `apt install python3-venv` | system python3 + venv |
| Fedora/RHEL | `/usr/bin/python3` | `dnf install python3` | system python3 + venv |
| Arch | `/usr/bin/python` | `pacman -S python` | system python + venv |
| Windows | py launcher | python.org installer | py launcher + venv |
| WSL | Same as its Linux distro | Same as its Linux distro | venv or uv |

### Ensuring python3-venv is Available
```bash
# Ubuntu/Debian - venv may not be installed by default
sudo apt install python3-venv python3-pip

# Fedora
sudo dnf install python3-pip

# Arch
# Already included with python package

# macOS (with Homebrew Python)
# Already included
```

---

## 4. Package Managers by Platform

### macOS - Homebrew
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Common packages
brew install node python git gh jq ripgrep fd

# GUI apps
brew install --cask visual-studio-code docker

# Update
brew update && brew upgrade
```

### Ubuntu/Debian - apt
```bash
# Update package lists first (always)
sudo apt update

# Common packages
sudo apt install -y nodejs npm python3 python3-venv python3-pip git curl jq

# Node.js via NodeSource (for newer versions)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Don't install Python packages with apt for project use
# Use venv + pip instead
```

### Fedora/RHEL - dnf
```bash
sudo dnf install nodejs python3 python3-pip git curl jq
```

### Arch - pacman
```bash
sudo pacman -S nodejs npm python python-pip git curl jq
```

### Windows - Multiple Options
```powershell
# Winget (built into Windows 11)
winget install Git.Git Node.js Python.Python.3.12

# Chocolatey
choco install git nodejs python vscode

# Scoop (user-level, no admin)
scoop install git nodejs python
```

---

## 5. File System Differences

### Path Separators
```bash
# Unix (macOS, Linux, WSL)
/home/user/project/src/main.py

# Windows
C:\Users\user\project\src\main.py
# Or UNC paths
\\server\share\path

# In scripts, use forward slashes even on Windows when possible
# Most tools (Node, Python, Git) handle them correctly
```

### Case Sensitivity

| Platform | File System | Case Sensitive? |
|----------|------------|-----------------|
| macOS | APFS (default) | Case-insensitive, case-preserving |
| Linux | ext4/btrfs | Case-sensitive |
| Windows | NTFS | Case-insensitive, case-preserving |
| WSL | ext4 on Linux, NTFS via /mnt | ext4 is sensitive, /mnt/c is not |

**Gotcha:** `import MyModule` works on macOS but fails on Linux if the file is `mymodule.py`. Always match case exactly.

### Line Endings
```bash
# Configure git to handle this automatically
git config --global core.autocrlf input    # macOS/Linux: convert CRLF to LF on commit
git config --global core.autocrlf true     # Windows: convert LF to CRLF on checkout

# Or use .gitattributes (project-level, preferred)
echo "* text=auto" > .gitattributes
echo "*.sh text eol=lf" >> .gitattributes
echo "*.bat text eol=crlf" >> .gitattributes
```

### File Permissions
```bash
# Unix: executable bit matters
chmod +x script.sh

# Windows: no executable bit in NTFS
# Git tracks it: git update-index --chmod=+x script.sh

# WSL: Windows files mounted at /mnt/c have 777 by default
# Configure in /etc/wsl.conf:
[automount]
options = "metadata,umask=22,fmask=11"
```

### Max Path Length
- **Linux/macOS:** 4096 characters (PATH_MAX)
- **Windows:** 260 characters by default (can enable long paths via registry/group policy)
- **node_modules on Windows:** Frequently exceeds 260 chars. Enable long paths or use pnpm.

---

## 6. Node.js and JavaScript Tooling

### Node.js Version Management
```bash
# nvm (recommended for all platforms)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use a version
nvm install 20
nvm use 20
nvm alias default 20

# fnm (faster alternative)
curl -fsSL https://fnm.vercel.app/install | bash
fnm install 20
fnm use 20
```

### Package Managers
```bash
# npm (comes with Node)
npm install

# pnpm (faster, saves disk space, handles Windows paths better)
npm install -g pnpm
pnpm install

# Bun (fastest, macOS/Linux only)
curl -fsSL https://bun.sh/install | bash
bun install
```

### npx vs Global Install
```bash
# Prefer npx for one-off tools (no global pollution)
npx create-next-app@latest
npx prettier --write .

# Only install globally for tools you use constantly
npm install -g typescript tsx
```

---

## 7. Git Configuration Across Platforms

### Essential Cross-Platform Config
```bash
# Identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Line endings (see section 5)
git config --global core.autocrlf input  # macOS/Linux
git config --global core.autocrlf true   # Windows

# Default branch
git config --global init.defaultBranch main

# Editor
git config --global core.editor "code --wait"  # VS Code

# Credential storage
git config --global credential.helper store       # Linux (plaintext, use carefully)
git config --global credential.helper osxkeychain # macOS
git config --global credential.helper manager     # Windows (Git Credential Manager)
```

### SSH Key Setup
```bash
# Generate key (same on all platforms)
ssh-keygen -t ed25519 -C "you@example.com"

# Start agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub | pbcopy      # macOS
cat ~/.ssh/id_ed25519.pub | xclip -sel clip  # Linux
cat ~/.ssh/id_ed25519.pub | clip        # Windows Git Bash
```

---

## 8. Docker and Containers

### Installation by Platform

| Platform | Install Method |
|----------|---------------|
| macOS | Docker Desktop (`brew install --cask docker`) |
| Ubuntu | `sudo apt install docker.io` or Docker official repo |
| Fedora | `sudo dnf install docker` |
| Windows | Docker Desktop (requires WSL 2 backend) |
| WSL | Shares Docker Desktop from Windows host, OR install natively |

### WSL + Docker
Docker Desktop for Windows uses WSL 2 as its backend. Enable in Docker Desktop settings:
- Settings > General > "Use the WSL 2 based engine"
- Settings > Resources > WSL Integration > Enable for your distro

From inside WSL, `docker` commands work natively after this.

### Rootless Docker (Linux production)
```bash
# Install rootless Docker (no sudo needed)
dockerd-rootless-setuptool.sh install

# Set environment
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

---

## 9. WSL-Specific Guide

WSL (Windows Subsystem for Linux) is one of the most common Claude Code environments and has unique considerations.

### WSL Architecture
- WSL 2 runs a real Linux kernel in a lightweight VM
- File system: ext4 for Linux files, NTFS for Windows files via `/mnt/c/`
- Network: shares Windows host network (WSL 2 has its own IP)
- GUI: WSLg provides X11/Wayland display server

### Performance: Where You Store Files Matters

**CRITICAL:** Working on files in `/mnt/c/` (Windows filesystem) from WSL is 3-10x slower than working in the Linux filesystem (`~/`, `/home/`).

```bash
# SLOW - Windows filesystem accessed from WSL
cd /mnt/c/Users/name/projects/myapp
git status  # Takes seconds instead of milliseconds

# FAST - Native Linux filesystem
cd ~/projects/myapp
git status  # Near-instant
```

**Rule:** Clone repos and do all development work in the Linux filesystem (`~`). Only use `/mnt/c/` to move files to/from Windows.

### WSL Configuration (/etc/wsl.conf)
```ini
[boot]
systemd=true              # Enable systemd (WSL 2 only)

[automount]
enabled=true
options="metadata,umask=22,fmask=11"  # Proper file permissions on /mnt/c

[interop]
enabled=true              # Run Windows executables from WSL
appendWindowsPath=true    # Access Windows PATH

[network]
generateResolvConf=true   # Auto-configure DNS
```

Apply changes: `wsl --shutdown` from PowerShell, then reopen terminal.

### Common WSL Gotchas

**1. DNS Resolution Fails**
```bash
# If apt/curl/wget can't resolve hostnames:
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
sudo chattr +i /etc/resolv.conf  # Prevent auto-regeneration
```

**2. Memory Usage**
WSL 2 VM can consume all available RAM. Create `.wslconfig` in Windows user folder:
```ini
# C:\Users\YourName\.wslconfig
[wsl2]
memory=8GB
processors=4
swap=4GB
```

**3. VS Code Integration**
```bash
# Open current directory in VS Code from WSL
code .

# This launches VS Code on Windows with WSL remote extension
# Files stay in Linux filesystem, editor runs on Windows
```

**4. Clipboard**
```bash
# Copy from WSL to Windows clipboard
echo "text" | clip.exe

# Paste from Windows clipboard into WSL
powershell.exe Get-Clipboard
```

**5. Opening Browsers/Files**
```bash
# Open URL in Windows browser from WSL
wslview https://example.com
# or
explorer.exe https://example.com
```

### WSL Python Setup
```bash
# Install Python and venv support
sudo apt update
sudo apt install python3 python3-venv python3-pip

# Create project with venv (in Linux filesystem, not /mnt/c!)
mkdir -p ~/projects/myapp
cd ~/projects/myapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 10. Common Mistakes Claude Code Makes

These are platform-specific errors that Claude Code frequently makes. Include relevant ones in your project's CLAUDE.md to prevent them.

### Python
| Mistake | Correct Approach |
|---------|-----------------|
| `pip install --break-system-packages` | Use virtual environment: `python3 -m venv .venv && source .venv/bin/activate` |
| `sudo pip install` | Never sudo pip. Use venv. |
| `pip install` without venv active | Always activate venv first |
| Assuming `python` exists | Use `python3` on Linux/macOS. `python` may not exist or may be Python 2. |
| Using `pip` instead of `pip3` | Same issue. Use `pip3` or ensure venv is active (where `pip` is correct). |

### Shell
| Mistake | Correct Approach |
|---------|-----------------|
| bash syntax in zsh (macOS) | Check shell with `echo $SHELL`. Use `[[` not `[`. |
| Assuming `apt` on all Linux | Check distro first. Fedora uses `dnf`, Arch uses `pacman`. |
| Using `echo -e` for escape sequences | Use `printf '%s\n'` for portability |
| Hardcoding `/home/username` | Use `$HOME` or `~` |
| Missing `#!/usr/bin/env bash` shebang | Always include shebang in scripts |

### File System
| Mistake | Correct Approach |
|---------|-----------------|
| Case-insensitive imports that break on Linux | Always match exact case of filenames |
| Paths with spaces, unquoted | Always quote: `"$filepath"` |
| Assuming `/tmp` is persistent | It's cleared on reboot on most systems |
| Working in `/mnt/c/` on WSL | Work in `~/` for 3-10x better performance |
| Creating files with CRLF line endings | Configure `.gitattributes` with `* text=auto` |

### Node.js
| Mistake | Correct Approach |
|---------|-----------------|
| `npm install -g` for project deps | Use `npx` or local install |
| Assuming `node` version | Use `nvm` or `fnm` for version management |
| Long paths on Windows | Use pnpm or enable long paths in Windows |

### Docker
| Mistake | Correct Approach |
|---------|-----------------|
| `docker` requires sudo on Linux | Add user to docker group: `sudo usermod -aG docker $USER` |
| Docker not available in WSL | Enable WSL integration in Docker Desktop settings |

### CLAUDE.md Template for Environment Rules
Include the relevant subset of these rules in your project's CLAUDE.md:

```markdown
## Environment Rules
- NEVER use `pip install --break-system-packages` or `sudo pip install`
- Always activate virtual environment before pip: `source .venv/bin/activate`
- Use `python3` not `python` (Linux/macOS)
- Check platform before using platform-specific commands
- Quote all file paths: "$filepath"
- Use printf instead of echo -e for portability
```
