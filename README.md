#Status

Brand new as of late Oct 2016.

Used daily by the author but that's total usage so far -- beta testers and comments welcome.

#Intro

oxit uses the Drobox API to observ/merge diffs of any two Dropbox file revisions with a git-style cli.

So you can edit/save the same file on multiple clients (laptop, Android Orgzly) and then later run oxit (on laptop) to observe the diffs and merge/resolve-conflicts if necessary.

The merge cmd is user setable and defaults to the emacs/client ediff cmd.

And oxit has a git(1) style cli flow we all know and love/hate

#Backstory

*Every time* you edit/save or copy over an existing file a new revision is made.
And Dropbox will save them for 1 month (free) or 1 year (paid).
And as a long time casual Dropbox user this was news to me recently.

And  my fave org-mode mobile app Orgzly supports Dropbox but not git(1) yet so I needed a way to merge notes that are modified on both laptop and mobile.

And if you squint hard enough Dropbox's auto-versioning looks like lightweight commits and maybe we can simulate a (limited) DVCS here.

#Caveats

As far as a poor-man's DVCS goes, oxit is useful when git is not avail but lacks many of git's often used features...

* oxit is not git

* Only handles a single file on Dropbox as remote repo

#Quick start

##One time
* Install

```bash
git clone 
setup ...
```
* Dropbox auth token

##Daily(ish)

1. Save org-mode notes (on two Dropbox clients)

2. Run oxit cmds on laptop

```bash
$ oxit clone dropbox://orgzly/oxit-me-maybe.org 

$ oxit log orgzly/oxit-me-maybe.org 

$ oxit diff --change-type head-headminus1 orgzly/oxit-me-maybe.org 

$ oxit merge --change-type head-headminus1 orgzly/oxit-me-maybe.org 

$ oxit add orgzly/oxit-me-maybe.org

$ oxit status

$ oxit push --no-dry-run orgzly/oxit-me-maybe.org
```

#Usage
```bash
$ oxit --help

$ oxit sub-cmd --help
```

#Test

```bash
bash test/run-tests.sh
```

#License

#Warranty
 
