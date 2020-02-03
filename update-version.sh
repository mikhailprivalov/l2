#!/bin/bash
DAY=$(date '+%-d')
MONTH=$(date '+%-m')
YEAR=$(date '+%Y')
HASH=$(git describe --always)

newVersion="__version__ = ($YEAR, $MONTH, $DAY, '$HASH')"

sed -i '' "1s/^.*$/$newVersion/" "laboratory/__init__.py"
