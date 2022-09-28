#!/bin/bash

# get prev tag and last tag
PREV_TAG=$(git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1))
LAST_TAG=$(git describe --abbrev=0 --tags $(git rev-list --tags --max-count=1))

# get commits between tags
COMMITS=$(git log --pretty=format:"%s" $PREV_TAG..$LAST_TAG)

DATE_UTC=$(date -u +"%Y-%m-%d")

echo "## [$LAST_TAG] — [$DATE_UTC]" >> CHANGELOG.md
# add each commit to changelog with messages
for COMMIT in $COMMITS
do
    echo "- $COMMIT" >> CHANGELOG.md
done

# add new line
echo "" >> CHANGELOG.md
