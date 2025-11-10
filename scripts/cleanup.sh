#!/bin/bash
# Cleanup script - Remove unnecessary files for Homebrew distribution

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╭────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│  Project Cleanup for Homebrew Distribution        │${NC}"
echo -e "${BLUE}╰────────────────────────────────────────────────────╯${NC}"
echo

# Safety check
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

echo -e "${YELLOW}This will delete unnecessary files and folders.${NC}"
echo -e "${YELLOW}See CLEANUP_PLAN.md for details.${NC}"
echo
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo

# Delete duplicate source directory
if [ -d "src" ]; then
    echo -e "${BLUE}→ Removing duplicate src/ directory...${NC}"
    rm -rf src
    echo -e "${GREEN}  ✓ Deleted src/${NC}"
fi

# Delete old scripts
for file in main.py create_distribution.sh install_alias.sh; do
    if [ -f "$file" ]; then
        echo -e "${BLUE}→ Removing $file...${NC}"
        rm "$file"
        echo -e "${GREEN}  ✓ Deleted $file${NC}"
    fi
done

# Delete test files
if [ -f "test_persistence.py" ]; then
    echo -e "${BLUE}→ Removing test_persistence.py...${NC}"
    rm test_persistence.py
    echo -e "${GREEN}  ✓ Deleted test_persistence.py${NC}"
fi

# Delete IDE settings
if [ -d ".vscode" ]; then
    echo -e "${BLUE}→ Removing .vscode/ directory...${NC}"
    rm -rf .vscode
    echo -e "${GREEN}  ✓ Deleted .vscode/${NC}"
fi

# Delete data directory (will be regenerated)
if [ -d "data" ]; then
    echo -e "${BLUE}→ Removing data/ directory...${NC}"
    rm -rf data
    echo -e "${GREEN}  ✓ Deleted data/${NC}"
fi

# Delete redundant documentation
DOCS_TO_DELETE=(
    "DISTRIBUTION.md"
    "INSTALL.md"
    "SETUP.md"
    "CONTENT_INGESTION.md"
    "CLI_REFERENCE.md"
    "PERSISTENCE.md"
    "HOMEBREW_README_SNIPPET.md"
    "CLEANUP_PLAN.md"
)

for doc in "${DOCS_TO_DELETE[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${BLUE}→ Removing $doc...${NC}"
        rm "$doc"
        echo -e "${GREEN}  ✓ Deleted $doc${NC}"
    fi
done

# Delete local .env (keep .env.example)
if [ -f ".env" ]; then
    echo -e "${BLUE}→ Removing local .env file...${NC}"
    echo -e "${YELLOW}  (Your API key should be in ~/.config/obsidian-notes-agent/config.env)${NC}"
    rm .env
    echo -e "${GREEN}  ✓ Deleted .env${NC}"
fi

# Update .gitignore to include IDE settings
echo -e "${BLUE}→ Updating .gitignore...${NC}"
if ! grep -q ".vscode/" .gitignore; then
    echo "" >> .gitignore
    echo "# IDE - Additional" >> .gitignore
    echo ".vscode/" >> .gitignore
    echo ".idea/" >> .gitignore
fi

if ! grep -q ".DS_Store" .gitignore; then
    echo "" >> .gitignore
    echo "# OS - Additional" >> .gitignore
    echo ".DS_Store" >> .gitignore
fi

echo -e "${GREEN}  ✓ Updated .gitignore${NC}"

echo
echo -e "${GREEN}╭────────────────────────────────────────────────────╮${NC}"
echo -e "${GREEN}│  ✓ Cleanup complete!                              │${NC}"
echo -e "${GREEN}╰────────────────────────────────────────────────────╯${NC}"
echo
echo -e "${BLUE}Files kept:${NC}"
echo "  • obsidian_notes_agent/ - Main package"
echo "  • homebrew/ - Homebrew formulas"
echo "  • scripts/ - Release scripts"
echo "  • README.md, LICENSE - Documentation"
echo "  • HOMEBREW_*.md - Homebrew guides"
echo "  • pyproject.toml, requirements.txt - Package config"
echo "  • .env.example - Example configuration"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review changes: git status"
echo "  2. Update README.md if needed"
echo "  3. Test installation: pip install -e ."
echo "  4. Commit: git add -A && git commit -m 'Clean up project structure'"
echo
