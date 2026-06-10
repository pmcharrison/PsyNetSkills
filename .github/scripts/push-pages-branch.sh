#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 PAGES_DIR PAGES_BRANCH" >&2
  exit 2
fi

pages_dir="$1"
pages_branch="$2"
remote_ref="refs/heads/${pages_branch}"
message_file="$(mktemp)"
publish_branch="publish-${pages_branch//\//-}-$$"

git -C "${pages_dir}" log -1 --format=%B > "${message_file}"

if git -C "${pages_dir}" ls-remote --exit-code --heads origin "${pages_branch}" >/dev/null 2>&1; then
  expected_remote="$(git -C "${pages_dir}" ls-remote origin "${pages_branch}" | awk '{print $1}')"
  lease_arg="--force-with-lease=${remote_ref}:${expected_remote}"
else
  lease_arg="--force"
fi

git -C "${pages_dir}" checkout --orphan "${publish_branch}"
git -C "${pages_dir}" add -A
git -C "${pages_dir}" commit -F "${message_file}"

for attempt in 1 2 3 4 5; do
  if git -C "${pages_dir}" push "${lease_arg}" origin "HEAD:${pages_branch}"; then
    exit 0
  fi

  if [ "${attempt}" = "5" ]; then
    echo "Failed to publish ${pages_branch} snapshot after ${attempt} attempts." >&2
    exit 1
  fi

  echo "Push to ${pages_branch} failed; retrying with the same remote lease."
  sleep $((attempt * 2))
done
