
### oxit basic sh test
###
### Notes:
###   1) valid auth token needed in oxit conf file
###   2) it will creat test files/dirs in ~/Dropbox

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

full_local_path=$repo/$path
oxit --oxit-repo $repo clone $url
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo log --oneline $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo diff $path
#oxit --oxit-repo $repo merge $path
date >> $full_local_path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo status $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo add $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo diff --reva head --revb index $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo status $path

tmpf=/tmp/fooxit.$RANDOM
cp $full_local_path $tmpf

# comment out this push to simulate fail yo
oxit $debug --oxit-repo $repo push --no-post-push-clone $path
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo status $path

mv $repo $repo.old
#echo rm $full_local_path

echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
oxit --oxit-repo $repo clone $url

cmp -s $tmpf $full_local_path
if [[ $? != 0 ]]; then
    echo "results: FAIL: $tname"
    exit 1
fi
echo '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
echo "results: success: $tname"
