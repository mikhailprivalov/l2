#!/bin/bash

make release

if [ $(git rev-parse --abbrev-ref HEAD) != "develop" ]; then
    echo "You are not on the develop branch"
    exit 1
fi

echo "Sleeping for 3 seconds to allow you to cancel"
sleep 3

V=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)

echo "Releasing version $V"

git tag -a v$V -m "Release $V"
git push origin v$V
