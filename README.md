# Intro
oxit uses the Dropbox API to view/merge diffs of any two Dropbox file revisions with a git-like cli/flow.

So you can edit and save the same file simultaneously on multiple clients (e.g. Emacs/laptop, Orgzly/Android) and then later run oxit (on laptop) to view the diffs, 3-way auto-merge revisions and resolve-conflicts (if necessary), and push merged file to Dropbox.

The `merge` cmd uses diff3 and will try to auto-merge. If it can't auto-merge all hunks the conflicts can be resolved by hand with emacs ediff-merge-with-ancestor (nice UI) or $EDITOR the diff3 output.

## Status
Used dailyish by the developer (w/2 Dropbox clients, Emacs laptop and Orgzly mobile) but that's total usage so far -- beta testers aka early adopters and comments/issues welcome (submit an issue/suggestion/question https://github.com/gaak99/oxit/issues).

You probably want to try master HEAD before fetching a release.

oxit does no Deletes via Dropbox API and all edits/merges are saved as a new revision, so should be low risk to give it a try. And note if a mismerge is saved you can easily revert to the revision you want, see Caveats/Gotchas below

## Backstory
*Every time* you edit/save or copy over an existing file (_citation needed_) a new revision is quietly made by Dropbox.
And Dropbox will save them for 1 month (free) or 1 year (paid).
And as a long time casual Dropbox user this was news to me recently.

And my fave org-mode mobile app Orgzly supports Dropbox but not git(1) yet so I needed a way to merge notes that are modified on both laptop and mobile.

And if you squint hard enough Dropbox's auto-versioning looks like lightweight commits and maybe we can simulate a (limited) DVCS here enough to be useful.


## Theory of operation
On Dropbox we keep a small&simple filename=content_hash kv db called the ancdb.
The content_hash is the official Dropbox one.

`oxit clone/merge/push` will (pseudocode):
```bash
	# fpath is file path being merged
	fa = dropbox_download(revs[latest])
	fb = dropbox_download(revs[latest_rev-1])
	fanc = dropbox_download(ancdb_get(fpath))
	rt = diff3 -m fa fanc fb #> fout
	if rt == 0: # no conflicts
		pass
	elseif rt == 1:
		# hand edit fout or 3-way ediff
	dropbox_upload(fout)
	ancdb_set(fpath); dropbox_upload(ancdb)
```

## Merge Flow
 1. On Orgzly (when regular `Sync` fails) select `Forced sync`.

 2. On laptop run oxmerge (wrapper around oxit). If auto-merge does not resolve all conflicts, resolve them by hand.

 3. On Orgzly run `Sync`.

# Oxit Usage
```bash
$ oxit --help
$ oxit sub-cmd --help
```

## Quick Start
### One time
* Install

```bash
git clone https://github.com/gaak99/oxit.git
export SUDO=sudo           # set for your env
cd oxit && $SUDO python setup.py install
export MYBIN=/usr/local/bin # set for your env
$SUDO cp oxit/scripts/oxmerge.sh $MYBIN/oxmerge
$SUDO chmod 755 $MYBIN/oxmerge
```

* Dropbox API app and OAuth 2 token

Create a Dropbox API app (w/full access to files and types) from Dropbox app console
   `<https://www.dropbox.com/developers/apps>`
and generate an access token for yourself.

And add it to ~/.oxitconfig. Note no quotes needed around $token.

```
[misc]
auth_token=$token
```

### One time per file
1. Make sure Orgzly has a clean `Sync` of file.

2. Run oxit cmds to init file in the ancestor db on laptop something like this:
 
	```bash
	$ mkdir /tmp/myoxitrepo ;  cd /tmp/myoxitrepo 
	$ oxit clone dropbox://orgzly/foo.org
	$ oxit ancdb_set orgzly/foo.org
	$ oxit ancdb_push
	```

### As needed (dailyish)
#### Save same file/note on Emacs and Orgzly
* The key point here is the latest Emacs version and latest Orgzly version need to be the last two revisions in Dropbox for the oxmerge script to work good.  (note advanced users can merge any two revisions via oxit)

1. Save file shared via Dropbox on laptop/Emacs (~/Dropbox) as needed.

2. On mobile/Orgzly save (locally) the same note as needed.

3. When ready to sync/merge, on Orgzly select `Sync` notes on Orgzly main menu.

4. If the sync fails and the Orgzly error msg says it's modified both local and remote -- *this* is the case we need oxit -- then `Force Save` (long press on note) on Orgzly.

   The forced save is safe cuz the prev edits will be saved by Dropbox as seperate revisions.

   But once you do this don't make any more changes (via Emacs/Orgzly/etc) to the file as it may cause problems with the merge. See section Caveats/Gotchas below.
	
#### Merge revisions
Now the 2 most recent revisions -- one each from laptop/Orgzly -- in Dropbox are ready to be merged with oxit:

1. Run oxit cmds via oxmerge script on laptop something like this:

	```bash
	$ cd /tmp/myoxitrepo 
	$ oxmerge dropbox://orgzly/foo.org
	```
	
2a. If oxmerge finished with no conflicts -- *YAAAY* -- goto step 3 below.

2b. If oxmerge finished with conflicts -- *BOOOO* -- choose one of the options output to resolve the conflict(s).

3. Finally on Orgzly select `Sync` (`Force Load` not necessary) to load merged/latest revision from Dropbox. This should be done before any other changes are saved to Dropbox.

Congrats your file is merged.

### Caveats/Gotchas

##### Careful no file locking!
* For a succesful merge, once the oxit merge process (aka 2 latest revisions downloaded) begins the user needs to be careful and not change the file anymore outside of the process (until process completes). A lock of the file would be useful here but I don't see it in the Dropbox v2 api.

##### Revert revision as fallback
* If a mismerge is saved you can easily revert to the revision you want using oxit or the Dropbox.com site.

###### Revert rev using oxit

```bash
$ oxit log --oneline orgzly/foo.org #find rev needed
$ oxit cat --rev $rev orgzly/foo.org > orgzly/foo.org
$ oxit push --no-dry-run orgzly/foo.org
# view/check it
$ oxit clone dropbox://orgzly/foo.org
$ oxit cat orgzly/foo.org
```
	
###### Revert rev on dropbox.com
* Login using web ui, look for menu right of file

##### 2-way ediff merge as fallback
* `oxit merge2` will do a 2-way merge -- no ancestor involved so no auto-merge -- which might be handy if the ancdb is not set correctly. Also note it can be done on any two revisions, see `oxit merge2 --help`


### Tips/Tricks

#### Using oxit

##### oxit cmds log (--oneline is nice), diff, and cat are handy to view a revision metadata/data
* See `oxit cmd --help`.

##### Tips for a clean -- no conflicts are a wonderful thang -- merge
* I have a misc notes file I slang url's and ideas to several times a day on Emacs and Orgzly and oxmerge once a day. And I'm mostly adding new (org top level) entries and much less changing older ones. To get a better chance of a clean (auto) merge I usually append note entries on Orgzly and prepend (below org TITLE header(s)) on Emacs. Also on Emacs I make sure the body of the note added has a empty line before and after as Orgzly likes it that way. So when Orgzly later groks it no changes are done that many result in an anoying dirty merge.

#### Using ediff
* ediff skillz def a plus here. But if you are not currently used to using ediff then this is good way to learn it. It's def a non-trivial -- UI-wise and concept-wise  -- but very useful Emacs app.
* Orgzly seems to add blank line(s) so don't ediff merge them out on Emacs else u will keep seeing them come back -- zombielike --  to haunt you and must re-merge again and again.
* BTW if you don't dig your ediff config try mines (that I found on the Net)

```lisp
;; don't start another frame
;; this is done by default in preluse
(setq ediff-window-setup-function 'ediff-setup-windows-plain)
;; put windows side by side
(setq ediff-split-window-function (quote split-window-horizontally))
;; revert windows on exit - needs winner mode
(winner-mode)
(add-hook 'ediff-after-quit-hook-internal 'winner-undo)
(add-hook 'ediff-prepare-buffer-hook #'show-all)
```

##### Developed/tested on MacOS and Linux so non-Unix-like systems may be trouble

#### Design
* oxit is not git -- no real commits, no branches, single user, etc. But as far as a poor-man's DVCS goes, oxit can be useful when git is not avail. Oxit just implements enough of a subset of git to support a basic clone-merge-add-push flow (and a few others to view the revisions and merged file). New files in wd/index not supported.

* My use case is Emacs on a Unix laptop and Android Orgzly on mobile phone so far only only that config has much real world use. More clients should be viable as long as two at a time are merged/pushed in a careful manner (don't save any non-oxit changes to Dropbox while this is being done). There's no locking done here so the user has to be careful and follow the procedure above.

* Only handles a single file on Dropbox as remote repo (might be expanded to a dir tree in future). 


# Tests

```bash
export PYTHONPATH=/tmp/pypath
mkdir /tmp/pypath && python setup.py develop --install-dir /tmp/pypath

# note valid Dropbox auth token needed in ~/.oxitconfig
PATH=/tmp/pypath:$PATH bash oxit/tests/run-tests.sh
```

# Legalese
## License

MIT.  See LICENSE file for full text.

## Warranty
 
None.

## Copyright
Copyright (c) 2016 Glenn Barry (gmail: gaak99)

# Refs
<http://www.orgzly.com>

<https://www.gnu.org/software/emacs/manual/html_node/ediff/>

<http://blog.plasticscm.com/2010/11/live-to-merge-merge-to-live.html?m=1>

<https://cloudrail.com/compare-consistency-models-of-cloud-storage-services/>

# Props
The hackers behind Dropbox, Orgzly, emacs/org-mode/ediff, Python/Click, git/github/git-remote-dropbox, and others I'm probably forgetting.
  
# Future work
## Features
* Remote repo can be a dir (not just a file as currently)

## More tests
* init tests - finer grained and mocked so can be done locally
* tests for each big fix

## Next level sh*t
* A magit style emacs ui?
* oxitless?!? (inspired by gitless) 
* CRDT!?! https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type     
