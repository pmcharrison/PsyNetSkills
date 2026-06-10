#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 PAGES_DIR PAGES_BRANCH" >&2
  exit 2
fi

pages_dir="$1"
pages_branch="$2"

for attempt in 1 2 3 4 5; do
  if git -C "${pages_dir}" push origin "HEAD:${pages_branch}"; then
    exit 0
  fi

  if [ "${attempt}" = "5" ]; then
    echo "Failed to push ${pages_branch} after ${attempt} attempts." >&2
    exit 1
  fi

  echo "Push to ${pages_branch} failed; rebasing on latest remote before retry."
  if git ls-remote --exit-code --heads origin "${pages_branch}" >/dev/null 2>&1; then
    git -C "${pages_dir}" fetch origin "${pages_branch}"
    git -C "${pages_dir}" rebase FETCH_HEAD
  fi
  sleep $((attempt * 2))
done
