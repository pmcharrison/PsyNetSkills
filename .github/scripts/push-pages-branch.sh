#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <pages_dir> <pages_branch>" >&2
  exit 2
fi

pages_dir="$1"
pages_branch="$2"

git -C "${pages_dir}" push origin "HEAD:${pages_branch}"
