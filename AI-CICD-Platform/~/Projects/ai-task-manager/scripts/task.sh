#!/bin/bash

# Main entry point for AI Task Manager
# Usage: ./task.sh [command] [options]

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Commands
case "$1" in
  status)
    echo -e "${BLUE}Current Task Status:${NC}"
    python3 "$SCRIPT_DIR/task-tracker.py" --status
    ;;
    
  complete)
    echo -e "${GREEN}Completing current task...${NC}"
    "$SCRIPT_DIR/complete-current-task.sh" "${@:2}"
    ;;
    
  next)
    echo -e "${YELLOW}Generating next task prompt...${NC}"
    "$SCRIPT_DIR/generate-next-task-prompt.sh" "${@:2}"
    ;;
    
  start)
    echo -e "${GREEN}Preparing task for Claude...${NC}"
    # Get the prompt
    PROMPT=$("$SCRIPT_DIR/next-task-for-claude.sh")
    
    # Copy to clipboard
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      echo "$PROMPT" | pbcopy
      echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      # Linux with xclip
      if command -v xclip &> /dev/null; then
        echo "$PROMPT" | xclip -selection clipboard
        echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
      elif command -v xsel &> /dev/null; then
        echo "$PROMPT" | xsel --clipboard
        echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
      else
        echo -e "${YELLOW}Could not copy to clipboard. Please install xclip or xsel.${NC}"
      fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
      # Windows
      echo "$PROMPT" | clip
      echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
    else
      echo -e "${YELLOW}Clipboard not supported on this OS. Task prompt not copied.${NC}"
    fi
    
    # Open Claude if requested
    if [[ "$2" == "--browser" || "$2" == "-b" ]]; then
      echo -e "${BLUE}Opening Claude in browser...${NC}"
      if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "https://claude.ai"
      elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "https://claude.ai"
      elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        start "https://claude.ai"
      else
        echo -e "${YELLOW}Could not open browser on this OS.${NC}"
      fi
    fi
    ;;
    
  help|--help|-h)
    echo -e "${BLUE}AI Task Manager - Help${NC}"
    echo "Usage: ./task.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status              Show current task status"
    echo "  complete [options]  Complete the current task"
    echo "  next [options]      Generate the next task prompt"
    echo "  start [options]     Prepare task for Claude and copy to clipboard"
    echo "  help                Show this help message"
    echo ""
    echo "Options for 'complete' and 'next':"
    echo "  --template NAME     Use specified template (default, concise, detailed)"
    echo "  --sub-task NAME     Specify a sub-task"
    echo ""
    echo "Options for 'start':"
    echo "  --browser, -b       Open Claude in the default browser"
    ;;
    
  *)
    if [ -z "$1" ]; then
      echo -e "${BLUE}AI Task Manager${NC}"
      echo "Run './task.sh help' for usage information"
    else
      echo -e "${RED}Unknown command: $1${NC}"
      echo "Run './task.sh help' for usage information"
      exit 1
    fi
    ;;
esac
