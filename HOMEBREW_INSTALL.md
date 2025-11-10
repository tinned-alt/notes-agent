# Homebrew Installation Guide

This guide explains how to make `obsidian-notes-agent` installable via Homebrew, with options for both private (personal use) and public distribution.

## Table of Contents

- [Security Overview](#security-overview)
- [Option 1: Private Homebrew Tap (Recommended for Personal Use)](#option-1-private-homebrew-tap)
- [Option 2: Public Homebrew Tap](#option-2-public-homebrew-tap)
- [Option 3: Submit to Homebrew Core](#option-3-submit-to-homebrew-core)
- [Testing Locally](#testing-locally)
- [User Installation Instructions](#user-installation-instructions)

## Security Overview

✅ **This project is secure for Homebrew distribution:**

- **No hardcoded API keys**: All sensitive credentials are loaded from user configuration
- **User-provided configuration**: API keys and vault paths are set by users after installation
- **Config file permissions**: Configuration files are created with `0600` permissions (user-only access)
- **Gitignored secrets**: `.env` files are properly excluded from version control
- **Interactive setup**: The `notes config` command guides users through secure configuration

## Option 1: Private Homebrew Tap

A private tap is perfect for personal use or sharing within your organization without making the code public.

### Step 1: Create a GitHub Repository for Your Tap

Create a **private** repository named `homebrew-tools` (or any name following `homebrew-*` pattern):

```bash
# On GitHub, create a private repo: yourusername/homebrew-tools
```

### Step 2: Prepare Your Project for Release

```bash
cd /path/to/notes-agent

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Add your GitHub remote
git remote add origin https://github.com/yourusername/obsidian-notes-agent.git

# Create and push a release
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

### Step 3: Create a GitHub Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select tag `v0.1.0`
4. Add release notes
5. Publish the release

### Step 4: Calculate SHA256 for the Formula

```bash
# Download your release tarball
curl -L https://github.com/yourusername/obsidian-notes-agent/archive/refs/tags/v0.1.0.tar.gz -o release.tar.gz

# Calculate SHA256
sha256sum release.tar.gz  # Linux
# or
shasum -a 256 release.tar.gz  # macOS
```

### Step 5: Create the Formula in Your Tap

```bash
# Clone your tap repository
git clone https://github.com/yourusername/homebrew-tools.git
cd homebrew-tools

# Create Formula directory
mkdir -p Formula

# Copy the formula
cp /path/to/notes-agent/homebrew/obsidian-notes-agent-simple.rb Formula/obsidian-notes-agent.rb

# Edit the formula to add the SHA256
nano Formula/obsidian-notes-agent.rb
# Update:
# - url to point to your actual release
# - sha256 with the calculated hash
# - homepage URL

# Commit and push
git add Formula/obsidian-notes-agent.rb
git commit -m "Add obsidian-notes-agent formula"
git push origin main
```

### Step 6: Install from Your Private Tap

```bash
# Add your tap (you'll need GitHub authentication for private repos)
brew tap yourusername/tools https://github.com/yourusername/homebrew-tools

# Install
brew install obsidian-notes-agent

# Configure
notes config
```

### Updating Your Formula

When you release a new version:

```bash
# Tag new version
git tag v0.2.0
git push origin v0.2.0

# Update formula with new URL and SHA256
cd homebrew-tools
nano Formula/obsidian-notes-agent.rb
# Update version, url, and sha256

git commit -am "Update obsidian-notes-agent to v0.2.0"
git push origin main

# Users can update with:
brew update
brew upgrade obsidian-notes-agent
```

## Option 2: Public Homebrew Tap

Make your formula publicly available while keeping your API keys secure.

### Security Checklist Before Going Public

```bash
# 1. Verify .env is gitignored
cat .gitignore | grep ".env"

# 2. Check for any committed secrets
git log --all --full-history -- .env

# 3. Search for hardcoded API keys (should find none in source code)
grep -r "sk-ant-api" --exclude-dir=.venv --exclude-dir=.git --exclude=".env"

# 4. Review all files that will be public
git ls-files
```

If any API keys are found in git history:

```bash
# Remove sensitive data from git history (use with caution!)
# Consider using git-filter-repo or BFG Repo-Cleaner
# Better option: Create a fresh repository
```

### Create Public Tap

Same as private tap, but make the `homebrew-tools` repository **public** on GitHub.

```bash
# Users can install with:
brew tap yourusername/tools
brew install obsidian-notes-agent
```

## Option 3: Submit to Homebrew Core

For maximum visibility, submit to the official Homebrew repository. This requires:

1. **Stable release**: At least version 1.0.0
2. **Public repository**: Must be publicly accessible
3. **Maintained project**: Active development and issue responses
4. **Notable adoption**: Some user base or community interest
5. **Clean formula**: Follows Homebrew style guidelines

```bash
# Test formula against Homebrew style guidelines
brew audit --strict --online obsidian-notes-agent

# Create a pull request to homebrew/homebrew-core
# See: https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request
```

## Testing Locally

Test your formula before publishing:

```bash
# Build a source distribution
cd /path/to/notes-agent
python -m build --sdist

# Create a local formula for testing
brew create file://$(pwd)/dist/obsidian_notes_agent-0.1.0.tar.gz

# Or test directly
brew install --build-from-source ./homebrew/obsidian-notes-agent-simple.rb

# Verify installation
notes --help
notes config

# Uninstall
brew uninstall obsidian-notes-agent
```

## User Installation Instructions

### From Your Private/Public Tap

```bash
# One-time setup: Add the tap
brew tap yourusername/tools [REPO_URL_IF_PRIVATE]

# Install
brew install obsidian-notes-agent

# Configure (first time)
notes config
# Enter your Anthropic API key
# Enter your Obsidian vault path

# Start using
notes chat
```

### Configuration

After installation, users must configure:

1. **Anthropic API Key**: Get from https://console.anthropic.com/
2. **Obsidian Vault Path**: Full path to their Obsidian vault

Configuration is stored at `~/.config/obsidian-notes-agent/config.env` with `0600` permissions.

### Updating

```bash
# Update Homebrew and upgrade
brew update
brew upgrade obsidian-notes-agent

# Configuration persists across updates
```

### Uninstalling

```bash
# Uninstall the package
brew uninstall obsidian-notes-agent

# Optionally remove configuration
rm -rf ~/.config/obsidian-notes-agent

# Remove tap
brew untap yourusername/tools
```

## Environment Variables

Users can also configure via environment variables instead of the config file:

```bash
export ANTHROPIC_API_KEY="your-key"
export OBSIDIAN_VAULT_PATH="/path/to/vault"
notes chat
```

## Security Best Practices

✅ **What's Safe to Commit**:
- Source code
- `.env.example` with placeholder values
- Documentation
- Tests
- Formula files

❌ **Never Commit**:
- `.env` files with real credentials
- API keys
- Personal vault paths
- User data

✅ **Formula Security**:
- API keys are never in the formula
- Users provide credentials post-installation
- Config files have restrictive permissions (0600)
- No network calls during formula installation (unless fetching dependencies)

## Troubleshooting

### Private Tap Authentication

If installing from a private tap fails with authentication errors:

```bash
# Create a GitHub Personal Access Token with 'repo' scope
# Then authenticate Homebrew:
export HOMEBREW_GITHUB_API_TOKEN="your-token"

# Or use SSH URLs in your tap
```

### Formula Issues

```bash
# Check formula for issues
brew audit obsidian-notes-agent

# View formula
brew cat obsidian-notes-agent

# Reinstall from source
brew reinstall --build-from-source obsidian-notes-agent
```

### Python Version Issues

The formula requires Python 3.12. If users have multiple Python versions:

```bash
# Check Python version used by Homebrew
brew info python@3.12

# Formula automatically uses Homebrew's Python
```

## Next Steps

1. **Choose your distribution method**: Private tap, public tap, or Homebrew Core
2. **Test thoroughly**: Install on a clean system to verify everything works
3. **Document**: Update your README with Homebrew installation instructions
4. **Maintain**: Keep the formula updated with new releases
5. **Security**: Regularly audit for any accidentally committed secrets

## Example: Complete Private Tap Setup

```bash
# 1. Prepare your project
cd ~/notes-agent
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:yourusername/obsidian-notes-agent.git
git push -u origin main
git tag v0.1.0
git push origin v0.1.0

# 2. Create GitHub release and get SHA256
curl -L https://github.com/yourusername/obsidian-notes-agent/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256

# 3. Create tap repository
mkdir homebrew-tools
cd homebrew-tools
git init
mkdir Formula
cp ~/notes-agent/homebrew/obsidian-notes-agent-simple.rb Formula/obsidian-notes-agent.rb
# Edit formula with correct URL and SHA256
git add Formula/
git commit -m "Add obsidian-notes-agent formula"
git remote add origin git@github.com:yourusername/homebrew-tools.git
git push -u origin main

# 4. Test installation
brew tap yourusername/tools
brew install obsidian-notes-agent
notes config
notes chat

# Success! 🎉
```

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guidance](https://docs.brew.sh/Python-for-Formula-Authors)
- [Creating Taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae)
