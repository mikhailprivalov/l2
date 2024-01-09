#!/usr/bin/env pwsh

if (git status --porcelain)
{
    Write-Host "There are uncommitted changes. Please commit or stash them before checking out a version." -ForegroundColor Red
    exit 1
}

git fetch --all
git checkout $args[0]
