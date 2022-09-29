#!/bin/bash
DAY=$(date -u '+%-d')
MONTH=$(date -u '+%-m')
YEAR=$(date -u '+%Y')
HOUR=$(date -u '+%-H')
HASH=$(git describe --always --abbrev=6 --exclude '*')
V="$YEAR.$MONTH.$DAY-$HOUR+$HASH"

newVersion="__version__ = \"$V\""

echo "New version is $V"
echo "Current directory is $(pwd)"

SEDOPTION="-i"

if [[ "$OSTYPE" == "darwin"* ]]; then
  SEDOPTION="-i ''"
fi

sed $SEDOPTION "1s/^.*$/$newVersion/" "laboratory/__init__.py"
sed $SEDOPTION "s/^version = \".*\"/version = \"$V\"/" "pyproject.toml"
