#!/usr/bin/env bash

PYTHON=~/.pyenv/shims/python

if [ ! -f $PYTHON ]; then
    echo "pyenv DOES NOT exists. Please install it here first (https://github.com/pyenv/pyenv) and then install Python version 3"
    exit 9999
fi

$PYTHON ./Scripts/PostMergeHook.py