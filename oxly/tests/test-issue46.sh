
### oxly issue #46 test
###
### Notes:
###   1) valid auth token needed in oxly conf file
###   2) it will creat test files/dirs in ~/Dropbox

#set -e # exit on error

if [[ $# != 4 ]]; then
    echo 'Usage: $0 test-name repo path debug'
    exit 1
fi

tname=$1
repo=$2
path=$3
debug=$4

url=dropbox://$path
repo=$repo.$RANDOM

oxly --version

echo "Starting test $tname ..."
#oxly --oxly-repo $repo clone --init-ancdb $url
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

# irl would do some mods on both dbx clients here

#full_local_path=$repo/$path
#oxly --oxly-repo $repo clone $url

#echo 'test fix for #46...'
let "NREVS_MAX = 100"
let "max_me_maybe = $NREVS_MAX + 1"
#echo "max_me_maybe = $max_me_maybe"
oxly --oxly-repo $repo clone --nrevs $max_me_maybe $url | \
    grep -i 'Warning: max number of revisions'
if [[ $? > 0 ]]; then
   echo "results: FAIL: $tname"
   exit 1
fi
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

echo "results: success: $tname"
