
import click
from oxit.main import Oxit

__version__ = "0.5.0" #xxx mv to setup?

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
@click.argument('path')
@click.pass_obj
def add(oxit, path):
    oxit.add(path)

@cli.command()
@click.argument('path')
@click.pass_obj
def reset(oxit, path):
    oxit.reset(path)

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
@click.option('--rev-diff-type', required=True,
              type=click.Choice(['wt-index', 'wt-head',
                                 'index-head',
                                 'head-headminus1',  'reva-revb']),
              help='wt=working tree, index=staging area, head=latest rev.')
@click.argument('path', required=True, default=None)
@click.argument('reva', required=False, default=None)
@click.argument('revb', required=False, default=None)
@click.pass_obj
def diff(oxit, diff_cmd, rev_diff_type, path, reva, revb):
    oxit.diff(diff_cmd, rev_diff_type, path, reva, revb)

@cli.command()
@click.pass_obj
def init(oxit):
    oxit.init()

@cli.command()
@click.argument('path', required=True, default=None)
@click.pass_obj
def log(oxit, path):
    oxit.log(path)

@cli.command()
@click.option('--emacsclient-path', required=False,
              envvar='EMACSCLIENT_PATH',
              help='If necessary set full path of default emacsclient.')
@click.option('--merge-cmd', required=False,
              envvar='MERGE_CMD',
              help='format: prog %s %s')
@click.option('--rev-diff-type', required=True,
              type=click.Choice(['wt-index', 'wt-head',
                                 'index-head',
                                 'head-headminus1',
                                  'reva-revb']),
              help='wt=working tree, index=staging area, head=latest rev.')
@click.argument('path')
@click.argument('reva', required=False, default=None)
@click.argument('revb', required=False, default=None)
@click.pass_obj
def merge(oxit, emacsclient_path, merge_cmd, rev_diff_type, path, reva, revb):
    oxit.merge(emacsclient_path, merge_cmd, rev_diff_type, path, reva, revb)


@cli.command()
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--post-push-clone/--no-post-push-clone',
              help='After success on push, (no) resync w/Dropbox.)',
              default=True)
@click.argument('path', required=False, default=None)
@click.pass_obj
def push(oxit, dry_run, post_push_clone, path):
    oxit.push(dry_run, post_push_clone, path)
    
@cli.command()
@click.option('--status-type',
              required=False,
              type=click.Choice(['wt-index',
                                 'index-head',
                                 'untracked']),
              help='wt=working tree, index=staging area, head=latest rev.')
@click.argument('path', required=False, default=None)
@click.pass_obj
def status(oxit, status_type, path):
    oxit.status(status_type, path)

@cli.command()
@click.argument('key', required=False)
@click.pass_obj
def getmetameta(oxit, key):
    oxit.getmm(key)

if __name__ == '__main__':
    cli()
