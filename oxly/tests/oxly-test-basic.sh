
### oxly basic sh test
###
### Notes:
###   1) valid auth token needed in oxly conf file
###   2) it will creat test files/dirs in ~/Dropbox

set -e # exit on error

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
oxly --oxly-repo $repo clone --init-ancdb $url
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

# irl would do some mods on both dbx clients here

full_local_path=$repo/$path
oxly --oxly-repo $repo clone $url
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#oxly --oxly-repo $repo log --oneline $path | head -5
oxly --oxly-repo $repo log --oneline --recent 5 $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
#need 2 revs oxly --oxly-repo $repo diff $path
#oxly --oxly-repo $repo merge $path
date >> $full_local_path
#echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo status $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo add $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo diff --reva head --revb index $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo status $path

tmpf=/tmp/fooxly.$RANDOM
cp $full_local_path $tmpf

# comment out this push to simulate fail yo
oxly $debug --oxly-repo $repo push --no-post-push-clone $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo status $path

mv $repo $repo.old
#echo rm $full_local_path

echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxly --oxly-repo $repo clone $url

cmp -s $tmpf $full_local_path
if [[ $? != 0 ]]; then
    echo "results: FAIL: $tname"
    exit 1
fi
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
echo "results: success: $tname"
