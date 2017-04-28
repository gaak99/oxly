
sh_debug="" #"-x"
dbxpath="$HOME/Dropbox"

subsh_debug='--no-debug'

tests_path=oxit/tests/oxit-test-basic.sh

# top level dbx file
fname=oxit-testf.txt
orgzly_dir=oxit-testmedir
path=$orgzly_dir/$fname
touch $dbxpath/$path
date >> $dbxpath/$path
repo=/tmp/test-oxit$RANDOM
bash $sh_debug $tests_path 'top level orgzly_dir/file' $repo $path $subsh_debug
#exit 99 #tmp

echo
echo '======================================================================'
echo

# file within dbx sub folders
path=oxit-testmedir/testdir2/mytest.txt
dir=$(dirname $path)
mkdir -p $dbxpath/$dir

touch $dbxpath/$path
date >> $dbxpath/$path
repo=/tmp/test-oxit$RANDOM
bash $sh_debug $tests_path 'file within subfolders' $repo $path $subsh_debug
