
sh_debug="" #"-x"
dbxpath="$HOME/Dropbox"

subsh_debug='--no-debug'

tests_path=oxit/tests/oxit-test-basic.sh

# top level dbx file
path=oxit-testf.txt
touch $dbxpath/$path
date >> $dbxpath/$path
repo=/tmp/test-oxit$RANDOM
bash $sh_debug $tests_path 'top level file' $repo $path $subsh_debug

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
