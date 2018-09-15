
# Copyright (c) 2016 Glenn Barry (gmail: gaak99)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import click
from oxly.core import Oxly, NREVS_MAX

from . import __version__

@click.group()
@click.version_option(version=__version__)
@click.option('--oxly-conf',
              envvar='OXLY_CONF',
              default='~/.oxlyconfig',
              help='User config file, default is ~/.oxlyconfig,\nVar list (INI format):\n[misc]\nauth_token=$mytoken')
@click.option('--oxly-repo', envvar='OXLY_REPO', default='.',
              help='Local dir to store working dir and .oxly.')
@click.option('--debug/--no-debug', default=False,
                        envvar='OXLY_DEBUG')
@click.pass_context
def cli(ctx, oxly_conf, oxly_repo, debug):
    ctx.obj = Oxly(oxly_conf, oxly_repo, debug)

@cli.command(help='Copy modded file from working dir to index pre push.')
@click.argument('filepath')
@click.pass_obj
def add(oxly, filepath):
    oxly.add(filepath)

@cli.command(help='Remove file from index.')
@click.argument('filepath')
@click.pass_obj
def reset(oxly, filepath):
    oxly.reset(filepath)

@cli.command(help='Download revisions of Dropbox file to local dir/repo and checkout HEAD to working dir. Local dir default is $PWD but can be set (see global opts), SRC format: dropbox://<orgzly>/[/<subdirs>/]<file.org>')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--init-ancdb/--no-init-ancdb', default=False)
@click.option('--nrevs',
              help='Number of latest metadata of revisions (defaults to 50) to download from Dropbox.',
              required=False, default=NREVS_MAX)
@click.argument('src')
@click.pass_obj
def clone(oxly, dry_run, src, nrevs, init_ancdb):
    oxly.clone(dry_run, src, nrevs, init_ancdb)

@cli.command(help='Run diff(1) to display the data differences of two revisions.')
@click.option('--diff-cmd', required=False,
              envvar='DIFF_CMD',
              help='Diff sh cmd, default is diff(1), format: program %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Default is HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are wd (working dir) and index (staging area), SRC format: dropbox://filepath')
@click.option('--revb', required=False, default='HEAD',
              help='Default is HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def diff(oxly, diff_cmd, reva, revb, filepath):
    oxly.diff(diff_cmd, reva, revb, filepath)
    
@cli.command(help='Prep local repo dir (used mostly by clone).')
@click.pass_obj
def init(oxly):
    oxly.init()

@cli.command(help='Display meta data of revisions downloaded from Dropbox, oneline format: rev-string file-size (bytes) date-modded Dropbox-content-hash (first 8 chars)')
@click.option('--oneline/--no-oneline', required=False, default=False,
              help='One line per revision.')
@click.option('--recent', required=True, default=NREVS_MAX,
              type=click.IntRange(1, NREVS_MAX),
              help='Only output N most recent entries.')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def log(oxly, oneline, recent, filepath):
    oxly.log(oneline, recent, filepath)

@cli.command(help='Run 3-way merge. Default: diff3 -m HEADMINUS1 ANCESTOR HEAD')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--merge-cmd', required=False,
              envvar='MERGE_CMD',
              help='Program to merge three revs, default is: diff3 -m')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Defaults to HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are working dir and index.')
@click.option('--revb', required=False, default='HEAD',
              help='Defaults to HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath')
@click.pass_obj
def merge(oxly, dry_run, merge_cmd, reva, revb, filepath):
    oxly.merge(dry_run, merge_cmd, reva, revb, filepath)

@cli.command(help='Run 2-way merge (by hand). Default: (emacsclient) ediff HEADMINUS1 HEAD')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--emacsclient-path', required=False,
              envvar='EMACSCLIENT_PATH',
              help='If necessary set full path of default emacsclient.')
@click.option('--merge-cmd', required=False,
              envvar='MERGE_CMD',
              help='Program to merge two revs, default is ediff via emacsclient, format: prog %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Defaults to HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are working dir and index.')
@click.option('--revb', required=False, default='HEAD',
              help='Defaults to HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath')
@click.pass_obj
def merge2(oxly, dry_run, emacsclient_path, merge_cmd, reva, revb, filepath):
    oxly.merge2(dry_run, emacsclient_path, merge_cmd, reva, revb, filepath)

@cli.command(help='Run emacsclient/ediff to allow user to resolve conflicts post merge aka diff3 run.')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--emacsclient-path', required=False,
              envvar='EMACSCLIENT_PATH',
              help='If necessary set full path of default emacsclient.')
@click.option('--mergerc-cmd', required=False,
              envvar='MERGERC_CMD',
              help='Program to resolve conflicts post merge, default is ediff via emacsclient, format: prog %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Defaults to HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are working dir and index.')
@click.option('--revb', required=False, default='HEAD',
              help='Defaults to HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath')
@click.pass_obj
def mergerc(oxly, dry_run, emacsclient_path, mergerc_cmd, reva, revb, filepath):
    oxly.merge_rc(dry_run, emacsclient_path, mergerc_cmd, reva, revb, filepath)

@cli.command(help='Upload result of locally merged files to Dropbox.')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--add/--no-add', required=False, default=False,
              help='Add filepath to staging area pre-push.')
@click.option('--post-push-clone/--no-post-push-clone',
              help='After success on push, (no) resync w/Dropbox.)',
              default=False)
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def push(oxly, dry_run, add, post_push_clone, filepath):
    oxly.push(dry_run, add, post_push_clone, filepath)
    
@cli.command(help='Copy file from .oxly/ to working dir. If staged version exists revert working dir one to it instead.')
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def checkout(oxly, filepath):
    oxly.checkout(filepath)

@cli.command(help='Display modded file name in index and/or working dir.')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def status(oxly, filepath):
    oxly.status(filepath)

@cli.command(help='Display internal sys file, mostly for debug.')
@click.argument('key', required=False)
@click.pass_obj
def getmetameta(oxly, key):
    oxly.getmm(key)

@cli.command(help='Calculate and display Dropbox filesMetaData content_hash.')
@click.argument('filepath')
@click.pass_obj
def calchash(oxly, filepath):
    oxly.calc_dropbox_hash(filepath)

@cli.command(help='Calculate and set Dropbox filesMetaData content_hash into ancestor db locally.')
@click.argument('filepath')
@click.pass_obj
def ancdb_set(oxly, filepath):
    oxly.ancdb_set(filepath)

@cli.command(help='Get Dropbox filesMetaData content_hash from local copy of ancestor db.')
@click.argument('filepath')
@click.pass_obj
def ancdb_get(oxly, filepath):
    oxly.ancdb_get(filepath)

@cli.command(help='Calc/Set dropbox hash in local ancestor db and upload ancestor db to Dropbox.')
@click.argument('filepath')
@click.pass_obj
def ancdb_push(oxly, filepath):
    oxly.ancdb_push(filepath)

@cli.command(help='Run cat(1) to display to stdout the data of a revision.')
@click.option('--cat-cmd', required=False,
              envvar='CAT_CMD',
              help='Cat/display rev data, default is cat(1), format: program [opts] %s')
@click.option('--rev', required=False, default='HEAD',
              help='Default is HEAD (latest rev downloaded from Dropbox).')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def cat(oxly, cat_cmd, rev, filepath):
    oxly.cat(cat_cmd, rev, filepath)

@cli.command(help='Download the data of a revision.')
@click.option('--rev', required=True, default='HEAD',
              help='Default is HEAD (latest rev downloaded from Dropbox).')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def pull(oxly, rev, filepath):
    oxly.pull(rev, filepath)

if __name__ == '__main__':
    cli()
