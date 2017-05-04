
set -e # exit on error

sh_debug="" #"-x"
#sh_debug="-x"
dbxhome="$HOME/Dropbox"

subsh_debug='--no-debug'

tests_path=oxly/tests/oxly-test-basic.sh

# fresh orgzly dir

fname=oxly-testf.txt
orgzly_dir=oxly-testmedir
fresh_orgzly_dir=oxly-testmedir-$RANDOM
#i said top yo path=$orgzly_dir/$td
path=$fresh_orgzly_dir

dbxpath=$dbxhome/$orgzly_dir
mkdir -p $dbxpath
frdbxpath=$dbxhome/$fresh_orgzly_dir
mkdir -p $frdbxpath
sleep 2 #syncmemaybe

path=$path/$fname
date >> $frdbxpath/$fname

repo=/tmp/test-oxly$RANDOM
sleep 2 #syncmemaybe
bash $sh_debug $tests_path 'fresh orgzly_dir' $repo $path $subsh_debug
mv $frdbxpath $dbxpath #dont clutter top level brah
#exit 99 #tmp

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

echo
echo '======================================================================'
echo

# fresh orgzly dir

fname=oxly-testf.txt
orgzly_dir=oxly-testmedir
fresh_orgzly_dir=oxly-testmedir-$RANDOM
#i said top yo path=$orgzly_dir/$td
path=$fresh_orgzly_dir

dbxpath=$dbxhome/$path
mkdir -p $dbxpath
frdbxpath=$dbxhome/$path
mkdir -p $frdbxpath
sleep 2 #syncmemaybe

path=$path/$fname

date >> $dbxpath/$fname
repo=/tmp/test-oxly$RANDOM
sleep 5 #syncmemaybe
bash $sh_debug $tests_path 'top level orgzly_dir/file' $repo $path $subsh_debug
#rm-me-maybe-dir $dbxox
