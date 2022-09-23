#!/bin/bash
DAY=$(date '+%-d')
MONTH=$(date '+%-m')
YEAR=$(date '+%Y')
HASH=$(git describe --always)
V="$YEAR.$MONTH.$DAY+$HASH"

newVersion="__version__ = \"$V\""

sed -i '' "1s/^.*$/$newVersion/" "laboratory/__init__.py"
sed -i '' "s/^version = \".*\"/version = \"$V\"/" "pyproject.toml"
