#!/bin/bash

# script to automate oxit merge typical case
#   gb april17

set -e

if [[ $# < 1 || $# > 2 ]]; then
    echo "Usage: $0 dropbox://file/path [local_repo]"
    echo "Usage: default local_repo is pwd"
    exit 1
fi

dbx_url=$1
if [[ $# == 2 ]]; then
    repo=$2
else
    repo=$(pwd)
fi

oxsite=dropbox
IFS=':' read -ra split <<< "$dbx_url"
site="${split[0]}"
fp=$(echo "${split[1]}" | sed 's,//,,')
if [[ $oxsite != "$site" ]]; then
    echo "Usage: $0 dropbox://file/path [local_repo]"
    echo "Usage: default local_repo is pwd"
    exit 1
fi

if [[ ! -d $repo ]]; then
    mkdir $repo
    cd $repo
fi

oxitcmd=oxit

echo "Cloning $oxurlpre/$fp into $(pwd) ..."
$oxitcmd clone $dbx_url
$oxitcmd log --oneline $fp | head -4
$oxitcmd merge $fp
$oxitcmd add   $fp
$oxitcmd push  $fp
