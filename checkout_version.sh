#!/usr/bin/env bash
set -e

if [[ -n $(git status --porcelain) ]]; then
  echo "You have uncommitted changes. Please stash them before running this script."
  exit 1
fi

git fetch --tags

RELEASE=$1
echo "Getting release: $RELEASE"

git checkout $RELEASE
