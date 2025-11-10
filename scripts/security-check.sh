#!/bin/bash
# Security verification script before public release

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╭────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│  Security Check - Pre-Release Verification        │${NC}"
echo -e "${BLUE}╰────────────────────────────────────────────────────╯${NC}"
echo

ISSUES=0

# Check 1: Verify .env is gitignored
echo -e "${BLUE}[1/6] Checking .gitignore for .env...${NC}"
if grep -q "^\.env$" .gitignore; then
    echo -e "${GREEN}✓ .env is gitignored${NC}"
else
    echo -e "${RED}✗ .env is NOT in .gitignore${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check 2: Search for API keys in source code
echo -e "${BLUE}[2/6] Scanning for hardcoded API keys...${NC}"
API_KEY_MATCHES=$(grep -r "sk-ant-api" --include="*.py" --include="*.json" --include="*.toml" --include="*.yaml" --include="*.yml" --exclude-dir=.venv --exclude-dir=.git --exclude-dir=data --exclude-dir=dist --exclude-dir=build --exclude-dir=__pycache__ . || true)

if [ -z "$API_KEY_MATCHES" ]; then
    echo -e "${GREEN}✓ No hardcoded API keys found in source code${NC}"
else
    echo -e "${RED}✗ Found potential API keys:${NC}"
    echo "$API_KEY_MATCHES"
    ISSUES=$((ISSUES + 1))
fi

# Check 3: Check if .env is tracked by git
echo -e "${BLUE}[3/6] Checking if .env is tracked by git...${NC}"
if [ -d ".git" ]; then
    if git ls-files --error-unmatch .env >/dev/null 2>&1; then
        echo -e "${RED}✗ .env is tracked by git!${NC}"
        echo -e "${YELLOW}  Run: git rm --cached .env${NC}"
        ISSUES=$((ISSUES + 1))
    else
        echo -e "${GREEN}✓ .env is not tracked by git${NC}"
    fi
else
    echo -e "${YELLOW}! Not a git repository - skipping${NC}"
fi

# Check 4: Check git history for .env
echo -e "${BLUE}[4/6] Checking git history for .env file...${NC}"
if [ -d ".git" ]; then
    if git log --all --full-history --source --pretty=format: --name-only --diff-filter=A | grep -q "^\.env$"; then
        echo -e "${RED}✗ .env was committed in the past!${NC}"
        echo -e "${YELLOW}  Consider using git-filter-repo to remove it${NC}"
        ISSUES=$((ISSUES + 1))
    else
        echo -e "${GREEN}✓ No .env files in git history${NC}"
    fi
else
    echo -e "${YELLOW}! Not a git repository - skipping${NC}"
fi

# Check 5: Verify .env.example has placeholders
echo -e "${BLUE}[5/6] Checking .env.example has placeholders...${NC}"
if [ -f ".env.example" ]; then
    if grep -q "your.*key.*here\|YOUR_.*HERE\|placeholder\|example" .env.example; then
        echo -e "${GREEN}✓ .env.example contains placeholders${NC}"
    else
        echo -e "${YELLOW}! .env.example might contain real values${NC}"
        echo -e "${YELLOW}  Please verify manually${NC}"
    fi
else
    echo -e "${YELLOW}! .env.example not found${NC}"
fi

# Check 6: Search for common secret patterns
echo -e "${BLUE}[6/6] Scanning for other secret patterns...${NC}"
PATTERNS=(
    "password\s*=\s*['\"][^'\"]{3,}['\"]"
    "api_key\s*=\s*['\"][^'\"]{10,}['\"]"
    "secret\s*=\s*['\"][^'\"]{3,}['\"]"
    "token\s*=\s*['\"][^'\"]{10,}['\"]"
)

FOUND_SECRETS=false
for pattern in "${PATTERNS[@]}"; do
    MATCHES=$(grep -rE "$pattern" --exclude-dir=.venv --exclude-dir=.git --exclude-dir=data --exclude-dir=dist --exclude-dir=build --exclude=".env" --include="*.py" . || true)
    if [ -n "$MATCHES" ]; then
        if [ "$FOUND_SECRETS" = false ]; then
            echo -e "${YELLOW}! Found potential secrets (review manually):${NC}"
            FOUND_SECRETS=true
        fi
        echo "$MATCHES"
    fi
done

if [ "$FOUND_SECRETS" = false ]; then
    echo -e "${GREEN}✓ No obvious secret patterns found${NC}"
fi

# Summary
echo
echo -e "${BLUE}╭────────────────────────────────────────────────────╮${NC}"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}│  ✓ Security check passed!                         │${NC}"
    echo -e "${GREEN}│  Project is safe for public release               │${NC}"
else
    echo -e "${RED}│  ✗ Security issues found: $ISSUES                        │${NC}"
    echo -e "${RED}│  Fix issues before making public                   │${NC}"
fi
echo -e "${BLUE}╰────────────────────────────────────────────────────╯${NC}"

exit $ISSUES
