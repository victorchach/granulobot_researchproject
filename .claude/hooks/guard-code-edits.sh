#!/bin/sh
# PreToolUse hook (Edit/Write/NotebookEdit): code changes only on a feature
# branch whose spec exists, i.e. only through the `feature` skill.
input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
case "$file" in
    *.py|*.ipynb|*/Makefile|Makefile) ;;
    *) exit 0 ;;
esac
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
branch=$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null)
case "$branch" in
    feature/[0-9][0-9][0-9]-*)
        spec="$root/specs/${branch#feature/}/spec.md"
        [ -f "$spec" ] && exit 0
        echo "Blocked: $spec is missing. Write the spec first (feature skill)." >&2
        exit 2 ;;
esac
echo "Blocked: code edits ($file) need the feature skill: spec in specs/NNN-name/, branch feature/NNN-name (current branch: $branch)." >&2
exit 2
