#!/usr/bin/env bash
# agent-ops — install into the global OpenCode config.
# Usage: ./sync.sh [--check] [--target <dir>] [--force]
#   --check   change nothing; exit 0 when installed, exit 1 on any difference.
#   --target  config directory (default: $HOME/.config/opencode).
#   --force   overwrite AGENTS.md even without the agent-ops marker.
# Name the interpreter explicitly: WSL and Git Bash give different $HOME and paths.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${HOME}/.config/opencode"
CHECK=0
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --check|-c) CHECK=1 ;;
        --force|-f) FORCE=1 ;;
        --target) shift; TARGET="${1:?--target needs a directory}" ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

fail=0
agents="$REPO/AGENTS.md"
[ -f "$agents" ] || { echo "FAIL  missing $agents" >&2; exit 1; }

chars="$(wc -m < "$agents" | tr -d '[:space:]')"
points="$(grep -cE '^[0-9]+\. ' "$agents" || true)"
echo "AGENTS.md: $chars chars, $points points"
if [ "$chars" -gt 2000 ]; then echo "FAIL  AGENTS.md is longer than 2000 characters" >&2; fail=1; fi
if [ "$points" -lt 6 ] || [ "$points" -gt 10 ]; then echo "FAIL  AGENTS.md must have 6-10 points" >&2; fail=1; fi

check_file() {
    src="$1"; dst="$2"; rel="$3"
    if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
        echo "OK      $rel"
    else
        echo "DRIFT   $rel"
        fail=1
    fi
}

install_file() {
    src="$1"; dst="$2"; rel="$3"; guard="$4"
    if [ ! -f "$src" ]; then echo "FAIL  missing $src" >&2; fail=1; return; fi
    mkdir -p "$(dirname "$dst")"
    if [ "$guard" = yes ] && [ -f "$dst" ] && [ "$FORCE" = 0 ]; then
        if ! head -c 200 "$dst" | grep -qiE 'agent[- ]?op'; then
            cp "$src" "$(dirname "$dst")/AGENTS.agent-ops.md"
            echo "EXISTS  $rel is not from agent-ops — left untouched; ours: AGENTS.agent-ops.md"
            fail=1
            return
        fi
    fi
    cp "$src" "$dst"
    echo "WRITE   $rel"
}

if [ "$CHECK" = 1 ]; then
    echo "Checking against $TARGET"
    check_file "$agents" "$TARGET/AGENTS.md" "AGENTS.md"
    for d in "$REPO"/skills/*/; do
        [ -f "${d}SKILL.md" ] || continue
        name="$(basename "$d")"
        check_file "${d}SKILL.md" "$TARGET/skills/$name/SKILL.md" "skills/$name/SKILL.md"
    done
    if [ "$fail" = 0 ]; then echo "Install matches the repo."; fi
    exit "$fail"
fi

echo "Installing into $TARGET"
install_file "$agents" "$TARGET/AGENTS.md" "AGENTS.md" yes
for d in "$REPO"/skills/*/; do
    [ -f "${d}SKILL.md" ] || continue
    name="$(basename "$d")"
    install_file "${d}SKILL.md" "$TARGET/skills/$name/SKILL.md" "skills/$name/SKILL.md" no
done

echo "Done. Verify: ./sync.sh --check"
exit "$fail"
