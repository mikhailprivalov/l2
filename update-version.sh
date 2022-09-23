#!/bin/bash
DAY=$(date -u '+%-d')
MONTH=$(date -u '+%-m')
YEAR=$(date -u '+%Y')
HASH=$(git describe --always --dirty --abbrev=6 --exclude '*')
V="$YEAR.$MONTH.$DAY+$HASH"

newVersion="__version__ = \"$V\""

sed -i '' "1s/^.*$/$newVersion/" "laboratory/__init__.py"
sed -i '' "s/^version = \".*\"/version = \"$V\"/" "pyproject.toml"
