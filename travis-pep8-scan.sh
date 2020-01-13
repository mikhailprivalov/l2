#!/usr/bin/env bash

set -eo pipefail

# -------------------------------------------------------------------------------- #
# Description                                                                      #
# -------------------------------------------------------------------------------- #
# This script will locate and process all relevant files within the given git      #
# repository. Errors will be stored and a final exit status used to show if a      #
# failure occured during the processing.                                           #
# -------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------- #
# Global Variables                                                                 #
# -------------------------------------------------------------------------------- #
# EXIT_VALUE - Used to store the script exit value - adjusted by the fail().       #
# -------------------------------------------------------------------------------- #
EXIT_VALUE=0

# -------------------------------------------------------------------------------- #
# Start                                                                            #
# -------------------------------------------------------------------------------- #
# UX - Show the user that the processing of a specific file has stared.            #
# -------------------------------------------------------------------------------- #
start()
{
    if [[ -x "$1" ]];  then
        SUFFIX="executable"
    else
        SUFFIX="NON executable"
    fi
    printf ' [ \033[00;33mInfo\033[0m ] Linting %s (%s)\n' "$1" "${SUFFIX}"
}

# -------------------------------------------------------------------------------- #
# Success                                                                          #
# -------------------------------------------------------------------------------- #
# UX - Show the user that the processing of a specific file was successful.        #
# -------------------------------------------------------------------------------- #
success()
{
    printf ' [  \033[00;32mOK\033[0m  ] Linting successful for %s\n' "$1"
}

# -------------------------------------------------------------------------------- #
# Fail                                                                             #
# -------------------------------------------------------------------------------- #
# UX - Show the user that the processing of a specific file failed and adjust the  #
# EXIT_VALUE to record this.                                                       #
# -------------------------------------------------------------------------------- #
fail()
{
    printf ' [ \033[0;31mFAIL\033[0m ] Linting failed for %s\n' "$1"
    EXIT_VALUE=1
}

# -------------------------------------------------------------------------------- #
# Skip                                                                             #
# -------------------------------------------------------------------------------- #
# UX - Show the user that the processing of a specific file was skipped.           #
# -------------------------------------------------------------------------------- #
skip()
{
    printf ' [ \033[00;36mSkip\033[0m ] Skipping %s\n' "$1"
}

# -------------------------------------------------------------------------------- #
# Check                                                                            #
# -------------------------------------------------------------------------------- #
# Check a specific file.                                                           #
# -------------------------------------------------------------------------------- #
check()
{
    local filename="$1"

    start "$filename"
    if pycodestyle "$filename"; then
        success "$filename"
    else
        fail "$filename"
    fi
}

# -------------------------------------------------------------------------------- #
# Find Relevant Files                                                              #
# -------------------------------------------------------------------------------- #
# Attempt to detect the operating system.                                          #
# -------------------------------------------------------------------------------- #
find_relevant_files()
{
    git ls-files | grep -E '.*.py$'
}

# -------------------------------------------------------------------------------- #
# Is Compatible                                                                    #
# -------------------------------------------------------------------------------- #
# The file is relevant but is it compatible with the testing we want to perform.   #
# -------------------------------------------------------------------------------- #
is_compatible()
{
    if [[ -z "${SKIP_INTERPRETER}" ]] || [[ "${SKIP_INTERPRETER}" != "true" ]]; then
        head -n1 "$1" | grep -E -w "python" >/dev/null 2>&1
    else
	true
    fi
}

# -------------------------------------------------------------------------------- #
# Scan Files                                                                       #
# -------------------------------------------------------------------------------- #
# Locate all of the relevant files within the repo and process compatible ones.    #
# -------------------------------------------------------------------------------- #
scan_files()
{
    echo 'Linting all *.py files'

    if [[ -z "${SKIP_INTERPRETER}" ]] || [[ "${SKIP_INTERPRETER}" != "true" ]]; then
        echo "We will test to ensure the script interpreter is set to python"
    else
        echo "We will NOT test for the existance of a script interpreter"
    fi

    while IFS= read -r filename
    do
        if is_compatible "$filename"; then
            check "$filename"
        else
            skip "$filename"
        fi
    done < <(find_relevant_files)

    exit $EXIT_VALUE
}

# -------------------------------------------------------------------------------- #
# Main()                                                                           #
# -------------------------------------------------------------------------------- #
# This is the actual 'script' and the functions/sub routines are called in order.  #
# -------------------------------------------------------------------------------- #

scan_files

# -------------------------------------------------------------------------------- #
# End of Script                                                                    #
# -------------------------------------------------------------------------------- #
# This is the end - nothing more to see here.                                      #
# -------------------------------------------------------------------------------- #
