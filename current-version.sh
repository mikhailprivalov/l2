#!/usr/bin/env bash

version=`sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
echo $version
