
import click
from oxit.main import Oxit

__version__ = "0.6" #xxx mv to setup?

@click.group()
@click.version_option(version=__version__)
@click.option('--oxit-conf', envvar='OXIT_CONF', default='~/.oxitconfig')
@click.option('--oxit-repo', envvar='OXIT_REPO', default='.',
              help='Dir to store working tree and oxit-home.')
@click.option('--oxit-home', envvar='OXIT_HOME', default='.oxit',
              help='Dir within local repo to store all revs and meta data.')
@click.option('--debug/--no-debug', default=False,
                        envvar='OXIT_DEBUG')
@click.pass_context
def cli(ctx, oxit_conf, oxit_repo, oxit_home, debug):
    ctx.obj = Oxit(oxit_conf, oxit_repo, oxit_home, debug)

@cli.command()
@click.argument('filepath')
@click.pass_obj
def add(oxit, filepath):
    oxit.add(filepath)

@cli.command()
@click.argument('filepath')
@click.pass_obj
def reset(oxit, filepath):
    oxit.reset(filepath)

@cli.command()
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--nrevs',
              help='number of latest revs to download',
              required=False, default=10)
@click.argument('src')
@click.pass_obj
def clone(oxit, dry_run, src, nrevs):
    oxit.clone(dry_run, src, nrevs)

@cli.command()
@click.option('--diff-cmd', required=False,
              envvar='DIFF_CMD',
              help='diff sh cmd, format: prog %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Defaults to HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are wd (working dir) and index (staging area).')
@click.option('--revb', required=False, default='HEAD',
              help='Defaults to HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def diff(oxit, diff_cmd, reva, revb, filepath):
    oxit.diff(diff_cmd, reva, revb, filepath)
    
@cli.command()
@click.pass_obj
def init(oxit):
    oxit.init()

@cli.command()
@click.argument('filepath', required=True, default=None)
@click.pass_obj
def log(oxit, filepath):
    oxit.log(filepath)

@cli.command()
@click.option('--emacsclient-path', required=False,
              envvar='EMACSCLIENT_PATH',
              help='If necessary set full path of default emacsclient.')
@click.option('--merge-cmd', required=False,
              envvar='MERGE_CMD',
              help='format: prog %s %s')
@click.option('--reva', required=False, default='HEADMINUS1',
              help='Defaults to HEADMINUS1 (latest rev-1 in Dropbox), other special keywords are wd (working dir) and index (staging area).')
@click.option('--revb', required=False, default='HEAD',
              help='Defaults to HEAD (latest rev in Dropbox) ... ditto --reva.')
@click.argument('filepath')
@click.pass_obj
def merge(oxit, emacsclient_path, merge_cmd, reva, revb, filepath):
    oxit.merge(emacsclient_path, merge_cmd, reva, revb, filepath)

@cli.command()
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--post-push-clone/--no-post-push-clone',
              help='After success on push, (no) resync w/Dropbox.)',
              default=True)
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def push(oxit, dry_run, post_push_clone, filepath):
    oxit.push(dry_run, post_push_clone, filepath)
    
@cli.command()
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def checkout(oxit, filepath):
    oxit.checkout(filepath)

@cli.command()
@click.argument('filepath', required=False, default=None)
@click.pass_obj
def status(oxit, filepath):
    oxit.status(filepath)

@cli.command()
@click.argument('key', required=False)
@click.pass_obj
def getmetameta(oxit, key):
    oxit.getmm(key)

if __name__ == '__main__':
    cli()
