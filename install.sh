#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────
# install.sh — Symlink skills from this repository
#
# Usage:
#   ./install.sh                                    # Interactive mode
#   ./install.sh --global                           # All skills → ~/.agents/skills/
#   ./install.sh --global skill1 skill2             # Specific skills → ~/.agents/skills/
#   ./install.sh --target /path/to/project          # All skills → project
#   ./install.sh --target /path/to/project s1 s2    # Specific skills → project
#   ./install.sh --uninstall --global               # Remove global symlinks
#   ./install.sh --uninstall --target /path/project # Remove project symlinks
#   ./install.sh --list                             # List available skills
# ─────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/.agents/skills"
GLOBAL_TARGET="$HOME/.agents/skills"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Helpers ──────────────────────────────────────────────────────

get_available_skills() {
  local skills=()
  for dir in "$SKILLS_SRC"/*/; do
    [ -f "$dir/SKILL.md" ] && skills+=("$(basename "$dir")")
  done
  echo "${skills[@]}"
}

get_skill_description() {
  local skill="$1"
  local skillfile="$SKILLS_SRC/$skill/SKILL.md"
  if [ -f "$skillfile" ]; then
    # Extract description from frontmatter (handles both inline and multiline YAML)
    awk '/^description:/{
      # Try inline: description: "text" or description: text
      sub(/^description:[[:space:]]*[">]*/, "")
      sub(/["]*$/, "")
      if (length($0) > 5) { print substr($0, 1, 80); exit }
      # Multiline: next non-empty indented line
      getline; sub(/^[[:space:]]*/, ""); sub(/["]*$/, "")
      print substr($0, 1, 80); exit
    }' "$skillfile"
  fi
}

list_skills() {
  echo -e "${BLUE}Available skills:${NC}\n"
  for skill in $(get_available_skills); do
    local desc
    desc=$(get_skill_description "$skill")
    echo -e "  ${GREEN}$skill${NC}"
    [ -n "$desc" ] && echo -e "    $desc"
  done
  echo ""
}

link_skill() {
  local skill="$1"
  local target_dir="$2"
  local src="$SKILLS_SRC/$skill"

  if [ ! -d "$src" ] || [ ! -f "$src/SKILL.md" ]; then
    echo -e "  ${RED}✗${NC} $skill — not found in repository"
    return 1
  fi

  mkdir -p "$target_dir"
  local dest="$target_dir/$skill"

  if [ -L "$dest" ]; then
    local current_target
    current_target=$(readlink -f "$dest")
    if [ "$current_target" = "$(readlink -f "$src")" ]; then
      echo -e "  ${YELLOW}~${NC} $skill — already linked"
      return 0
    fi
    rm "$dest"
  elif [ -d "$dest" ]; then
    echo -e "  ${YELLOW}!${NC} $skill — directory exists (not a symlink), skipping"
    echo -e "    Remove it manually if you want to replace: rm -rf $dest"
    return 1
  fi

  ln -s "$src" "$dest"
  echo -e "  ${GREEN}✓${NC} $skill → $dest"
}

unlink_skill() {
  local skill="$1"
  local target_dir="$2"
  local dest="$target_dir/$skill"

  if [ -L "$dest" ]; then
    rm "$dest"
    echo -e "  ${GREEN}✓${NC} $skill — removed"
  elif [ -d "$dest" ]; then
    echo -e "  ${YELLOW}~${NC} $skill — not a symlink, skipping"
  else
    echo -e "  ${YELLOW}~${NC} $skill — not installed"
  fi
}

# ── Interactive mode ─────────────────────────────────────────────

interactive_mode() {
  echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║   Skills Installer (Interactive)     ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
  echo ""

  # Choose target
  echo -e "Where do you want to install skills?\n"
  echo -e "  ${GREEN}1)${NC} Global (~/.agents/skills/)"
  echo -e "  ${GREEN}2)${NC} Specific project"
  echo ""
  read -rp "Choose [1/2]: " choice

  local target_dir
  case "$choice" in
    1) target_dir="$GLOBAL_TARGET" ;;
    2)
      read -rp "Project path: " project_path
      project_path="${project_path/#\~/$HOME}"
      if [ ! -d "$project_path" ]; then
        echo -e "${RED}Error: $project_path does not exist${NC}"
        exit 1
      fi
      target_dir="$project_path/.agents/skills"
      ;;
    *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
  esac

  # Choose skills
  echo ""
  echo -e "Available skills:\n"
  local available
  available=($(get_available_skills))
  local i=1
  for skill in "${available[@]}"; do
    echo -e "  ${GREEN}$i)${NC} $skill"
    ((i++))
  done
  echo -e "  ${GREEN}a)${NC} All skills"
  echo ""
  read -rp "Choose skills (comma-separated numbers, or 'a' for all): " selection

  local selected_skills=()
  if [ "$selection" = "a" ]; then
    selected_skills=("${available[@]}")
  else
    IFS=',' read -ra indices <<< "$selection"
    for idx in "${indices[@]}"; do
      idx=$(echo "$idx" | tr -d ' ')
      if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "${#available[@]}" ]; then
        selected_skills+=("${available[$((idx-1))]}")
      fi
    done
  fi

  if [ ${#selected_skills[@]} -eq 0 ]; then
    echo -e "${RED}No skills selected${NC}"
    exit 1
  fi

  # Install
  echo ""
  echo -e "${BLUE}Installing to: $target_dir${NC}\n"
  for skill in "${selected_skills[@]}"; do
    link_skill "$skill" "$target_dir"
  done

  echo ""
  echo -e "${GREEN}Done!${NC}"
}

# ── CLI mode ─────────────────────────────────────────────────────

MODE=""
TARGET=""
UNINSTALL=false
SKILLS_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)    MODE="global"; shift ;;
    --target)    MODE="target"; TARGET="$2"; shift 2 ;;
    --uninstall) UNINSTALL=true; shift ;;
    --list)      list_skills; exit 0 ;;
    --help|-h)
      echo "Usage:"
      echo "  ./install.sh                                    # Interactive"
      echo "  ./install.sh --global [skill1 skill2 ...]       # Global install"
      echo "  ./install.sh --target /path [skill1 skill2 ...] # Project install"
      echo "  ./install.sh --uninstall --global               # Remove global"
      echo "  ./install.sh --uninstall --target /path          # Remove from project"
      echo "  ./install.sh --list                              # List skills"
      exit 0
      ;;
    *)           SKILLS_ARGS+=("$1"); shift ;;
  esac
done

# No mode specified → interactive
if [ -z "$MODE" ] && [ "$UNINSTALL" = false ]; then
  interactive_mode
  exit 0
fi

# Resolve target directory
TARGET_DIR=""
case "$MODE" in
  global) TARGET_DIR="$GLOBAL_TARGET" ;;
  target)
    TARGET="${TARGET/#\~/$HOME}"
    if [ ! -d "$TARGET" ]; then
      echo -e "${RED}Error: $TARGET does not exist${NC}"
      exit 1
    fi
    TARGET_DIR="$TARGET/.agents/skills"
    ;;
  *)
    echo -e "${RED}Error: specify --global or --target /path${NC}"
    exit 1
    ;;
esac

# Resolve skills list
if [ ${#SKILLS_ARGS[@]} -eq 0 ]; then
  SKILLS_ARGS=($(get_available_skills))
fi

# Execute
echo ""
if [ "$UNINSTALL" = true ]; then
  echo -e "${BLUE}Removing skills from: $TARGET_DIR${NC}\n"
  for skill in "${SKILLS_ARGS[@]}"; do
    unlink_skill "$skill" "$TARGET_DIR"
  done
else
  echo -e "${BLUE}Installing to: $TARGET_DIR${NC}\n"
  for skill in "${SKILLS_ARGS[@]}"; do
    link_skill "$skill" "$TARGET_DIR"
  done
fi

echo ""
echo -e "${GREEN}Done!${NC}"
