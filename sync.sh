#!/usr/bin/env bash
# agent-ops — установка в глобальный конфиг OpenCode.
# Использование: ./sync.sh [--check] [--target <каталог>] [--force]
#   --check   ничего не менять; код 0 — совпадает, код 1 — расхождение.
#   --target  каталог конфига (по умолчанию $HOME/.config/opencode).
#   --force   перезаписать AGENTS.md без маркера agent-ops.
# Интерпретатор указывать явно: WSL и Git Bash дают разные $HOME и пути.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${HOME}/.config/opencode"
CHECK=0
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --check|-c) CHECK=1 ;;
        --force|-f) FORCE=1 ;;
        --target) shift; TARGET="${1:?--target нужен каталог}" ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) echo "неизвестный аргумент: $1" >&2; exit 2 ;;
    esac
    shift
done

fail=0
agents="$REPO/AGENTS.md"
[ -f "$agents" ] || { echo "FAIL  нет $agents" >&2; exit 1; }

chars="$(wc -m < "$agents" | tr -d '[:space:]')"
points="$(grep -cE '^[0-9]+\. ' "$agents" || true)"
echo "AGENTS.md: $chars знаков, $points пунктов"
if [ "$chars" -gt 2000 ]; then echo "FAIL  AGENTS.md длиннее 2 000 знаков" >&2; fail=1; fi
if [ "$points" -lt 6 ] || [ "$points" -gt 10 ]; then echo "FAIL  нужно 6-10 пунктов" >&2; fail=1; fi

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
    if [ ! -f "$src" ]; then echo "FAIL  нет $src" >&2; fail=1; return; fi
    mkdir -p "$(dirname "$dst")"
    if [ "$guard" = yes ] && [ -f "$dst" ] && [ "$FORCE" = 0 ]; then
        if ! head -c 200 "$dst" | grep -qiE 'agent[- ]?op'; then
            cp "$src" "$(dirname "$dst")/AGENTS.agent-ops.md"
            echo "ЕСТЬ    $rel не от agent-ops — не тронут; наш вариант: AGENTS.agent-ops.md"
            fail=1
            return
        fi
    fi
    cp "$src" "$dst"
    echo "СТАВЛЮ  $rel"
}

if [ "$CHECK" = 1 ]; then
    echo "Сверка с $TARGET"
    check_file "$agents" "$TARGET/AGENTS.md" "AGENTS.md"
    for d in "$REPO"/skills/*/; do
        [ -f "${d}SKILL.md" ] || continue
        name="$(basename "$d")"
        check_file "${d}SKILL.md" "$TARGET/skills/$name/SKILL.md" "skills/$name/SKILL.md"
    done
    if [ "$fail" = 0 ]; then echo "Установка совпадает с репозиторием."; fi
    exit "$fail"
fi

echo "Установка в $TARGET"
install_file "$agents" "$TARGET/AGENTS.md" "AGENTS.md" yes
for d in "$REPO"/skills/*/; do
    [ -f "${d}SKILL.md" ] || continue
    name="$(basename "$d")"
    install_file "${d}SKILL.md" "$TARGET/skills/$name/SKILL.md" "skills/$name/SKILL.md" no
done

echo "Готово. Проверка: ./sync.sh --check"
exit "$fail"
