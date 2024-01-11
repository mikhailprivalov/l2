#!/usr/bin/env pwsh

echo $(Get-Content pyproject.toml | Select-String -Pattern 'version = "(.*)"' | ForEach-Object { $_.Matches[0].Groups[1].Value })
