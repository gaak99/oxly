
set -e # exit on error

sh_debug="" #"-x"
#sh_debug="-x"
dbxhome="$HOME/Dropbox"

subsh_debug='--no-debug'

tests_path=oxly/tests/oxly-test-basic.sh

# top level dbx file
fname=oxly-testf.txt
orgzly_dir=oxly-testmedir
td=td${RANDOM}
#i said top yo path=$orgzly_dir/$td
path=$orgzly_dir

dbxpath=$dbxhome/$path
mkdir -p $dbxpath
sleep 2 #syncmemaybe

path=$path/$fname

date >> $dbxpath/$fname
repo=/tmp/test-oxly$RANDOM
sleep 5 #syncmemaybe
bash $sh_debug $tests_path 'top level orgzly_dir/file' $repo $path $subsh_debug
#exit 99 #tmp

echo
echo '======================================================================'
echo

# file within dbx sub folders
path=oxly-testmedir/$td/dir1/dir2/testdir2mytest.txt
dir=$(dirname $path)
mkdir -p $dbxhome/$dir

date >> $dbxhome/$path
sleep 5 #syncmemaybe
repo=/tmp/test-oxly$RANDOM
bash $sh_debug $tests_path 'file within subfolders' $repo $path $subsh_debug

#rm-me-maybe-dir $dbxox
