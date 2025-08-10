#!/usr/bin/env bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
PRIVATE=false
while getopts "ph" opt; do
    case $opt in
        p)
            PRIVATE=true
            ;;
        h)
            echo "Usage: $0 [-p] [-h]"
            echo "  -p    Create a private repository (default: public)"
            echo "  -h    Show this help message"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            echo "Use -h for help"
            exit 1
            ;;
    esac
done

# Get the current directory name as repo name
REPO_NAME=$(basename "$PWD")

echo -e "${GREEN}GitHub Repository Initializer${NC}"
echo -e "${GREEN}==============================${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Install it with: sudo apt install gh (Ubuntu/Debian) or brew install gh (macOS)"
    exit 1
fi

# Check if already a git repo
if [ -d .git ]; then
    echo -e "${YELLOW}Warning: This directory is already a git repository.${NC}"
    read -p "Do you want to continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Initialize git repo
    echo -e "${GREEN}Initializing git repository...${NC}"
    git init
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Not authenticated with GitHub. Running 'gh auth login'...${NC}"
    gh auth login
fi

# Create initial commit if no commits exist
if ! git rev-parse HEAD &> /dev/null 2>&1; then
    echo -e "${GREEN}Creating initial commit...${NC}"
    
    # Create .gitignore if it doesn't exist
    if [ ! -f .gitignore ]; then
        echo -e "${YELLOW}Creating basic .gitignore...${NC}"
        cat > .gitignore << 'EOF'
# OS files
.DS_Store
Thumbs.db

# Editor directories and files
.idea/
.vscode/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Dependencies
node_modules/
vendor/
__pycache__/
*.pyc

# Environment variables
.env
.env.local
.env.*.local

# Build outputs
dist/
build/
out/
target/

# Git init script
gh-init.sh
EOF
    fi
    
    # Add all files and commit
    git add .
    git commit -m "Initial commit"
fi

# Create GitHub repository
echo -e "${GREEN}Creating GitHub repository: $REPO_NAME${NC}"

# Set visibility based on flag
if [ "$PRIVATE" = true ]; then
    VISIBILITY="--private"
    echo -e "${YELLOW}Creating as PRIVATE repository${NC}"
else
    VISIBILITY="--public"
    echo -e "${YELLOW}Creating as PUBLIC repository${NC}"
fi

# Create the repo
gh repo create "$REPO_NAME" $VISIBILITY --source=. --remote=origin --push

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Repository created successfully!${NC}"
    
    # Show repo URL
    REPO_URL=$(gh repo view --json url -q .url)
    echo ""
    echo -e "${GREEN}=====================================  ${NC}"
    echo -e "${GREEN}✓ All done! Your repository is live at:${NC}"
    echo -e "${GREEN}$REPO_URL${NC}"
    echo -e "${GREEN}=====================================${NC}"
else
    echo -e "${RED}Failed to create repository. Check the error message above.${NC}"
    exit 1
fi