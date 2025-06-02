#!/bin/bash

install_script=git-pre-commit-format
formatter=apply-format

bash_source="${BASH_SOURCE[0]:-$0}"

top_dir=$(git -C "$git_test_dir" rev-parse --show-toplevel) || \
    error_exit "You need to be in the git repository to run this script."

hook_path="$top_dir/.git/hooks"

my_path=$(realpath "$bash_source") || exit 1
my_dir=$(dirname "$my_path") || exit 1

echo "Installing pre-commit hook"
$my_dir/$install_script install || exit 1

existing_formatter=$hook_path/$formatter
if [ ! -e "$existing_formatter" ]; then
    cp $my_dir/apply-format $hook_path/
    echo "Copied formatter script"
fi
