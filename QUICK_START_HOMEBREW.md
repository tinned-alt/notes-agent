# Quick Start: Homebrew Installation

## For Users Installing the Package

```bash
# 1. Add the tap (if using a custom tap)
brew tap yourusername/tools

# 2. Install
brew install obsidian-notes-agent

# 3. Configure
notes config
# Enter your Anthropic API key (from https://console.anthropic.com/)
# Enter your Obsidian vault path

# 4. Start using!
notes chat
```

That's it! Your API key and vault path are stored securely in `~/.config/obsidian-notes-agent/config.env`.

---

## For Developers: Making This Project Homebrew-Installable

### Quick Setup (Private Tap - Recommended)

**1. Create a Release**

```bash
# Build and get SHA256
./scripts/create-release.sh 0.1.0

# Push to GitHub
git push origin main
git push origin v0.1.0

# Create release on GitHub
# Go to: https://github.com/yourusername/obsidian-notes-agent/releases/new
```

**2. Create Your Homebrew Tap**

```bash
# Create a new GitHub repo: yourusername/homebrew-tools (can be private!)
mkdir homebrew-tools
cd homebrew-tools
mkdir Formula

# Copy and edit formula
cp /path/to/notes-agent/homebrew/obsidian-notes-agent-simple.rb Formula/obsidian-notes-agent.rb

# Edit Formula/obsidian-notes-agent.rb:
# - Update 'url' to your GitHub release URL
# - Update 'sha256' with the hash from step 1
# - Update 'homepage' with your repo URL
```

**3. Push and Test**

```bash
# Push tap
git init
git add Formula/
git commit -m "Add obsidian-notes-agent formula"
git remote add origin git@github.com:yourusername/homebrew-tools.git
git push -u origin main

# Test installation
brew tap yourusername/tools
brew install obsidian-notes-agent
notes config
notes chat
```

### Security Checklist ✅

Before making anything public:

```bash
# Verify no API keys in code
grep -r "sk-ant-api" --exclude-dir=.venv --exclude-dir=.git --exclude=".env"

# Verify .env is gitignored
cat .gitignore | grep "^\.env$"

# Check git history for secrets
git log --all --full-history -- .env
```

**You're safe to distribute because:**
- ✅ API keys are user-provided post-installation
- ✅ Config stored in user's home directory
- ✅ No secrets in source code
- ✅ .env files properly gitignored

### Distribution Options

| Method | Public/Private | Difficulty | Best For |
|--------|---------------|-----------|----------|
| **Private Tap** | Private | Easy | Personal use, testing |
| **Public Tap** | Public | Easy | Sharing with others |
| **Homebrew Core** | Public | Hard | Wide distribution |

### Common Commands

```bash
# Update your tap with new version
cd homebrew-tools
nano Formula/obsidian-notes-agent.rb  # Update version, url, sha256
git commit -am "Update to v0.2.0"
git push

# Users update with:
brew update
brew upgrade obsidian-notes-agent
```

### Troubleshooting

**"Cannot install from private repo"**
```bash
# Create GitHub token with 'repo' access
export HOMEBREW_GITHUB_API_TOKEN="your-token"
```

**"Python version not found"**
```bash
# Install Python 3.12
brew install python@3.12
```

**"Formula errors"**
```bash
# Audit formula
brew audit --strict Formula/obsidian-notes-agent.rb

# Test installation
brew install --build-from-source ./Formula/obsidian-notes-agent.rb
```

### Full Documentation

See [HOMEBREW_INSTALL.md](HOMEBREW_INSTALL.md) for complete details.
