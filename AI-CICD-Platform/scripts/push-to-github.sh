#!/bin/bash

# Script to push changes to GitHub

# Ensure we're in the project root directory
cd "$(dirname "$0")/.."

# Check if there are any changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to commit."
    exit 0
fi

# Add all changes
git add .

# Commit changes with a descriptive message
git commit -m "Enhance Self-Healing Debugger with expanded error pattern recognition and auto-patching

- Added over 100 new error patterns across multiple categories
- Enhanced auto-patching with templates for network, resource, test, and security issues
- Improved error categorization logic
- Updated documentation with new architecture diagrams and testing strategy
- Created comprehensive project plan"

# Push changes to GitHub
git push origin main

echo "Changes pushed to GitHub successfully."
