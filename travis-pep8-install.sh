#!/usr/bin/env bash

set -eo pipefail

# -------------------------------------------------------------------------------- #
# Description                                                                      #
# -------------------------------------------------------------------------------- #
# Install the softwre that is required for scan.sh to be able to perform the       #
# testing / validation that is required.                                           #
# -------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------- #
# Find requirements                                                                #
# -------------------------------------------------------------------------------- #
# Find any 'requirements.txt' files within the repository.                         #
# -------------------------------------------------------------------------------- #
find_requirements()
{
    git ls-files | grep -E 'requirements.txt'
}

# -------------------------------------------------------------------------------- #
# Install all requirements                                                         #
# -------------------------------------------------------------------------------- #
# Run a pip install -r for all reqrements files located.                           #
# -------------------------------------------------------------------------------- #
install_all_requirements()
{
    echo 'Installing all requirements'

    while IFS= read -r filename
    do
        pip install -r "${filename}"
    done < <(find_requirements)
}

# -------------------------------------------------------------------------------- #
# Main()                                                                           #
# -------------------------------------------------------------------------------- #
# This is the actual 'script' and the functions/sub routines are called in order.  #
# -------------------------------------------------------------------------------- #

pip install pycodestyle

install_all_requirements

# -------------------------------------------------------------------------------- #
# End of Script                                                                    #
# -------------------------------------------------------------------------------- #
# This is the end - nothing more to see here.                                      #
# -------------------------------------------------------------------------------- #
