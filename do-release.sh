#!/bin/bash

make release

if [ $(git rev-parse --abbrev-ref HEAD) != "develop" ]; then
    echo "You are not on the develop branch"
    exit 1
fi

V=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)

git tag -a v$V -m "Release $V"
git push origin v$V
