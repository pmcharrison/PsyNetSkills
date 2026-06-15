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
patch_file="$(mktemp)"
remote_url="$(git -C "${pages_dir}" remote get-url origin)"

git -C "${pages_dir}" log -1 --format=%B > "${message_file}"
intended_commit="$(git -C "${pages_dir}" rev-parse HEAD)"
if base_commit="$(git -C "${pages_dir}" rev-parse "${intended_commit}^" 2>/dev/null)"; then
  git -C "${pages_dir}" diff --binary --full-index "${base_commit}" "${intended_commit}" > "${patch_file}"
else
  git -C "${pages_dir}" diff --binary --full-index --root "${intended_commit}" > "${patch_file}"
fi

for attempt in 1 2 3 4 5; do
  publish_dir="$(mktemp -d)"

  remote_line="$(git -C "${pages_dir}" ls-remote --heads origin "${pages_branch}")"
  if [ -n "${remote_line}" ]; then
    git -C "${pages_dir}" fetch --no-tags origin "refs/heads/${pages_branch}"
    expected_remote="$(git -C "${pages_dir}" rev-parse FETCH_HEAD)"
    lease_arg="--force-with-lease=${remote_ref}:${expected_remote}"
    git -C "${pages_dir}" worktree add --detach "${publish_dir}" "${expected_remote}"
  else
    lease_arg="--force-with-lease=${remote_ref}:"
    git -c init.defaultBranch="${pages_branch}" init "${publish_dir}"
    git -C "${publish_dir}" remote add origin "${remote_url}"
  fi

  git -C "${publish_dir}" config user.name "github-actions[bot]"
  git -C "${publish_dir}" config user.email "41898282+github-actions[bot]@users.noreply.github.com"

  if ! git -C "${publish_dir}" apply --index --3way "${patch_file}"; then
    git -C "${pages_dir}" worktree remove --force "${publish_dir}" >/dev/null 2>&1 || rm -rf "${publish_dir}"
    echo "Failed to apply ${pages_branch} changes to the latest remote state." >&2
    exit 1
  fi

  if git -C "${publish_dir}" diff --cached --quiet; then
    git -C "${pages_dir}" worktree remove --force "${publish_dir}" >/dev/null 2>&1 || rm -rf "${publish_dir}"
    echo "${pages_branch} already contains the requested changes."
    exit 0
  fi

  tree="$(git -C "${publish_dir}" write-tree)"
  commit="$(git -C "${publish_dir}" commit-tree "${tree}" -F "${message_file}")"

  if git -C "${publish_dir}" push "${lease_arg}" origin "${commit}:${pages_branch}"; then
    git -C "${pages_dir}" worktree remove --force "${publish_dir}" >/dev/null 2>&1 || rm -rf "${publish_dir}"
    exit 0
  fi

  git -C "${pages_dir}" worktree remove --force "${publish_dir}" >/dev/null 2>&1 || rm -rf "${publish_dir}"

  if [ "${attempt}" = "5" ]; then
    echo "Failed to publish ${pages_branch} snapshot after ${attempt} attempts." >&2
    exit 1
  fi

  echo "Push to ${pages_branch} failed; retrying on top of the latest remote state."
  sleep $((attempt * 2))
done
