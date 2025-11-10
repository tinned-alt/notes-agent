#!/bin/bash
# Script to create a new release and update Homebrew formula

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╭────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│  Obsidian Notes Agent - Release Helper Script     │${NC}"
echo -e "${BLUE}╰────────────────────────────────────────────────────╯${NC}"
echo

# Check if version is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: ./scripts/create-release.sh <version>"
    echo "Example: ./scripts/create-release.sh 0.1.0"
    exit 1
fi

VERSION=$1
TAG="v${VERSION}"

# Verify we're in project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must be run from project root${NC}"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${BLUE}→ Updating version in pyproject.toml...${NC}"
sed -i "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml

echo -e "${BLUE}→ Building distribution...${NC}"
python -m build

echo -e "${BLUE}→ Calculating SHA256...${NC}"
TARBALL="dist/obsidian_notes_agent-${VERSION}.tar.gz"
if [ ! -f "$TARBALL" ]; then
    echo -e "${RED}Error: Tarball not found: $TARBALL${NC}"
    exit 1
fi

SHA256=$(sha256sum "$TARBALL" | cut -d' ' -f1)
echo -e "${GREEN}SHA256: $SHA256${NC}"

echo -e "${BLUE}→ Creating git tag...${NC}"
git add pyproject.toml
git commit -m "Bump version to ${VERSION}" || true
git tag -a "$TAG" -m "Release ${VERSION}"

echo
echo -e "${GREEN}╭────────────────────────────────────────────────────╮${NC}"
echo -e "${GREEN}│  Release prepared successfully!                    │${NC}"
echo -e "${GREEN}╰────────────────────────────────────────────────────╯${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Push to GitHub:"
echo -e "   ${BLUE}git push origin main${NC}"
echo -e "   ${BLUE}git push origin $TAG${NC}"
echo
echo -e "2. Create GitHub release:"
echo -e "   • Go to: https://github.com/yourusername/obsidian-notes-agent/releases/new"
echo -e "   • Select tag: $TAG"
echo -e "   • Add release notes"
echo -e "   • Publish release"
echo
echo -e "3. Update Homebrew formula with:"
echo -e "   ${BLUE}url \"https://github.com/yourusername/obsidian-notes-agent/archive/refs/tags/$TAG.tar.gz\"${NC}"
echo -e "   ${BLUE}sha256 \"$SHA256\"${NC}"
echo
echo -e "4. Test installation:"
echo -e "   ${BLUE}brew reinstall --build-from-source obsidian-notes-agent${NC}"
echo
