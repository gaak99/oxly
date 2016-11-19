#Intro
oxit uses the Dropbox API to view/merge diffs of any two Dropbox file revisions with a git-style cli.

So you can edit/save the same file simultaneously on multiple clients (e.g. laptop, Android Orgzly) and then later run oxit (on laptop) to view the diffs, merge last two (usually) revisions (and resolve-conflicts if necessary), and push merged file to Dropbox.

The merge cmd is user setable and defaults to the emacs/client ediff cmd.

##Keywords
oxit emacs ediff org-mode orgzly dropbox cloud sync

##Status
Brand new as of late Oct 2016.

Used dailyish by the author (w/2 Dropbox clients) but that's total usage so far -- beta testers aka early adopters and comments/issues welcome (submit an issue here on github).

##Backstory
*Every time* you edit/save or copy over an existing file (_citation needed_) a new revision is quietly made by Dropbox.
And Dropbox will save them for 1 month (free) or 1 year (paid).
And as a long time casual Dropbox user this was news to me recently.

And my fave org-mode mobile app Orgzly supports Dropbox but not git(1) yet so I needed a way to merge notes that are modified on both laptop and mobile.

And if you squint hard enough Dropbox's auto-versioning looks like lightweight commits and maybe we can simulate a (limited) DVCS here enough to be useful.


#Usage
```bash
$ oxit --help

$ oxit sub-cmd --help
```

##Quick start
###One time
* Install

```bash
git clone https://github.com/gaak99/oxit.git
cd oxit && sudo python setup.py install 
```
* Dropbox auth token

Generate your auth (w/full access to files and types) from Dropbox app console
   `<https://www.dropbox.com/developers/apps>`
   
And add it to ~/.oxitconfig. Note no quotes needed around $token.

```
[misc]
auth_token=$token
```

###As needed (dailyish)
#### Save same file/note on Dropbox clients
1. Save file shared via Dropbox on laptop (~/Dropbox) as needed.
   When you want to sync/merge with Orgzly don't save any more revisions on laptop until the oxit push is completed.
   It's not terrible if you do -- no data loss -- but you may have to redo the oxit procedure below.

2. On Android/Orgzly save the same note (locally).

3. On Android/Orgzly select `Sync` notes on Orgzly main menu.

4. If sync fails and the Orgzly error msg says it's modified both local and remote -- *this* is the case we need oxit -- then `Force save` (long press on note) on Orgzly.

   The forced save is safe cuz the prev edits will be saved by Dropbox as seperate revisions.

####Merge last two revisions w/oxit on laptop
1. Run oxit cmds on laptop

	```bash
	$ mkdir /tmp/myoxitrepo && cd /tmp/myoxitrepo 

	$ oxit clone dropbox://orgzly/foo.txt

	(optional) $ oxit log orgzly/foo.txt

	(optional) $ oxit diff orgzly/foo.txt # diff(1) last two revisions

	(optional) $ oxit merge --dry-run orgzly/foo.txt

	$ oxit merge --no-dry-run orgzly/foo.txt # merge last two revisions (with emacs ediff)

	(note merged buffer should be saved in repo working dir -- $repo/$filepath, *not* under $repo/.oxit/)

	(optional) $ oxit status

	$ oxit add orgzly/foo.txt # add merged file to staging area

	(optional) $ oxit status

	(optional) $ oxit diff --reva HEAD --revb index orgzly/foo.txt # diff(1) last Dropbox revision and staged version

	(optional) $ oxit push --dry-run orgzly/foo.txt

	$ oxit push --no-dry-run orgzly/foo.txt # upload merged file to Dropbox
	```

####Finish with Orgzly sync
1. Finally on Orgzly select main menu `Sync` to load merged/latest revision from Dropbox.


###Tips/Tricks/Caveats/Gotchas

####Design
* oxit is not git -- Def not git as no real commits, no branches, single user, etc. But as far as a poor-man's DVCS goes, oxit can be useful when git is not avail. Oxit just implements enough of a subset of git to support a basic clone-merge-add-push flow (and a few others to view the revisions and merged file). New files in wd/index not supported.

* My use case is laptop and Android Orgzly so far only only that config has much real world use. More clients should be viable as long as two at a time are merged/pushed in a careful manner (don't save any non-oxit changes to Dropbox while this is being done). There's no locking done here so the user has to be careful and follow the procedure above.


* Only handles a single file on Dropbox as remote repo (might be expanded to a dir tree in future). 

* The merge is done by hand which is not as nice as automated merge but at least you have full control over merged file and conflicts must be resolved by hand in any model (_citation needed_) anyways.
(It's not automated cuz it's a two-way merge cuz not a real VCS as no common ancestor can be identified for three-way merge).

####Using oxit

#####Running merge-cmd
* Use the ```merge --dry-run``` opt to see merge-cmd that will be run.
By default it's ediff via emacsclient so the usual gotchas apply here -- in emacs run ```server-start```.
* If you are like me and have several versions of emacs installed and emacsclient can't connect, try setting  ```merge --emacsclient-path``` (or sh ```$EMACSCLIENT_PATH```).

####Using ediff
* ediff skillz def a plus here. But if not currently avail then this is good way to learn it. It's def a non-trivial -- UI-wise and concept-wise  -- Emacs app.
* Typically in ediff you'll choose buffer A or buffer B for each change chunk, but for this type of merge (2 way) sometimes (appended chunks in A&B for example) you may want both and thus you may need to hand edit the merge buffer (better way?).
* The merged buffer should be saved in repo working dir -- ```$repo/$filepath```, *not* under ```$repo/.oxit/```.
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

#Test

```bash
export PYTHONPATH=/tmp/pypath
python setup.py develop --install-dir /tmp/pypath

# note valid Dropbox auth token needed in ~/.oxitconfig
PATH=$PATH:/tmp/pypath bash  oxit/tests/run-tests.sh
```

#Legalese
##License

MIT.  See LICENSE file for full text.

##Warranty
 
None.

##Copyright
Copyright (c) 2016 GT Barry (gaak99@gmail.com)

#Refs
<http://www.orgzly.com>

<https://www.gnu.org/software/emacs/manual/html_node/ediff/>

<http://blog.plasticscm.com/2010/11/live-to-merge-merge-to-live.html?m=1>

#Props
The hackers behind Dropbox, Orgzly, emacs/org-mode/ediff, Python/Click, git/github/git-remote-dropbox, and others I'm probably forgetting.
  
#Future work
* More tests
  * init tests - finer grained and mocked so can be done locally
  * tests for each big fix
* A magit style emacs ui?
* oxitless?!? (inspired by gitless) 
     
