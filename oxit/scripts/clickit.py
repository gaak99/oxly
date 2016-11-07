
import click
from oxit.main import Oxit

from . import __version__

@click.group()
@click.version_option(version=__version__)
@click.option('--oxit-conf',
              envvar='OXIT_CONF',
              default='~/.oxitconfig',
              help='User config file, default is ~/.oxitconfig,\nVar list (INI format):\n[misc]\nauth_token=$mytoken')
@click.option('--oxit-repo', envvar='OXIT_REPO', default='.',
              help='Local dir to store working dir and .oxit.')
@click.option('--debug/--no-debug', default=False,
                        envvar='OXIT_DEBUG')
@click.pass_context
def cli(ctx, oxit_conf, oxit_repo, debug):
    ctx.obj = Oxit(oxit_conf, oxit_repo, debug)

@cli.command(help='Copy modded file from working dir to index pre push.')
@click.argument('filepath')
@click.pass_obj
def add(oxit, filepath):
    oxit.add(filepath)

@cli.command(help='Remove file from index.')
@click.argument('filepath')
@click.pass_obj
def reset(oxit, filepath):
    oxit.reset(filepath)

@cli.command(help='Download revisions of Dropbox file to local dir/repo and checkout HEAD to working dir. Local dir default is $PWD but can be set (see global opts), SRC format: dropbox://$filepath')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--nrevs',
              help='Number of latest file revisions (defaults to 5) to download from Dropbox.',
              required=False, default=5)
@click.argument('src')
@click.pass_obj
def clone(oxit, dry_run, src, nrevs):
    oxit.clone(dry_run, src, nrevs)

@cli.command(help='Run diff-cmd to display the data differences of two revisions.')
@click.option('--diff-cmd', required=False,
              envvar='DIFF_CMD',
              help='Diff sh cmd, default is diff(1), format: program %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Default is HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are wd (working dir) and index (staging area), SRC format: dropbox://filepath')
@click.option('--revb', required=False, default='HEAD',
              help='Default is HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def diff(oxit, diff_cmd, reva, revb, filepath):
    oxit.diff(diff_cmd, reva, revb, filepath)
    
@cli.command(help='Prep local repo dir (used mostly by clone).')
@click.pass_obj
def init(oxit):
    oxit.init()

@cli.command(help='Display meta data of revisions downloaded from Dropbox, format: rev-string date-modded file-size')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def log(oxit, filepath):
    oxit.log(filepath)

@cli.command(help='Run merge-cmd to allow user to merge two revs.')
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
def merge(oxit, emacsclient_path, merge_cmd, reva, revb, filepath):
    oxit.merge(emacsclient_path, merge_cmd, reva, revb, filepath)

@cli.command(help='Upload result of locally merged files to Dropbox.')
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--post-push-clone/--no-post-push-clone',
              help='After success on push, (no) resync w/Dropbox.)',
              default=True)
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def push(oxit, dry_run, post_push_clone, filepath):
    oxit.push(dry_run, post_push_clone, filepath)
    
@cli.command(help='Copy file from .oxit/ to working dir. If staged version exists revert working dir one to it instead.')
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def checkout(oxit, filepath):
    oxit.checkout(filepath)

@cli.command(help='Display modded file name in index and/or working dir.')
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def status(oxit, filepath):
    oxit.status(filepath)

@cli.command(help='Display internal sys file, mostly for debug.')
@click.argument('key', required=False)
@click.pass_obj
def getmetameta(oxit, key):
    oxit.getmm(key)

if __name__ == '__main__':
    cli()
