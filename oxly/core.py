
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

from __future__ import print_function

from . import __version__

import sys
import os
import random
import filecmp
import ConfigParser
import string
import json
import itertools
import subprocess as sp
import pickledb
from functools import wraps
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from .utils import make_sure_path_exists, get_relpaths_recurse, utc_to_localtz
from .utils import calc_dropbox_content_hash

USER_AGENT = 'oxly/' + __version__
OXLYDIRVERSION = "1"
OXLYSEP1 = '::'
OXLYSEP2 = ':::'
OXLYHOME = '.oxly'
OXLYMETAMETA = 'metametadb.json'
OXLYINDEX = 'index'
OLDDIR = '.old'
LOGFILENAME = 'log.txt'
HASHREVDB = 'hashrevdb.json'
# 100 appears to be free Dropbox svc max, non-free max?
NREVS_MAX = 100

# defaults 2-way diff/merge
MERGE_BIN = "emacsclient"
MERGE_EVAL = "--eval"
MERGE_EVALFUNC = "ediff-merge-files"
DEFAULT_MERGE_CMD = MERGE_BIN + ' ' + MERGE_EVAL + ' \'('\
                    + MERGE_EVALFUNC + ' %s %s' + ')\''
DEFAULT_DIFF_CMD = 'diff %s %s'
DEFAULT_CAT_CMD = 'cat %s'

# defaults 3-way diff/merge
MERGE3_EVALFUNC = "ediff-merge-with-ancestor"
DEFAULT_MERGE3RC_CMD = MERGE_BIN + ' ' + MERGE_EVAL + ' \'('\
                    + MERGE3_EVALFUNC + ' %s %s %s' + ')\''
DEFAULT_EDIT_CMD = 'emacsclient %s'
DIFF3_BIN = 'diff3'
DIFF3_BIN_ARGS = '-m'
ANCDBNAME = '_oxly_ancestor_pickledb.json'

class Oxly():
    """Oxly class -- use the Dropbox API to observ/merge
          diffs of any two Dropbox file revisions
    """
    def __init__(self, oxly_conf, oxly_repo, debug):
        """Initialize Oxly class.

        oxly_conf:  user's conf file path
        oxly_repo:  local copy of Dropbox file revisions data and md
        """
        self.debug = debug
        self.repo = os.getcwd() if oxly_repo == '.' else oxly_repo 
        self.home = OXLYHOME
        self.conf = oxly_conf
        self.dbx = None
        self.mmdb_path_dir = self.repo + '/' + OXLYHOME + '/.tmp'
        #self.mmdb_path_dir = self._get_pname_home_base_tmp()
        self.mmdb_path = self.mmdb_path_dir + '/oxly' + OXLYSEP1 + OXLYMETAMETA
        if os.path.isfile(self.mmdb_path):
            self.mmdb = pickledb.load(self.mmdb_path, False)

    def _debug(self, s):
        if self.debug:
            print(s)  # xxx stderr?

    def _try_dbxauth(self):
        token = self._get_conf('auth_token')
        if not token:
            sys.exit("ERROR: auth_token not in ur oxly conf file brah")
        self.dbx = dropbox.Dropbox(token, user_agent=USER_AGENT)
        try:
            self.dbx.users_get_current_account()
            self._debug('debug push auth ok')
        except AuthError as err:
            print("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
            sys.exit(1)
        except Exception as e:
            print("ERROR: push call to Dropbox fail: %s" % e)
            sys.exit(1)

    def _dbxauth(fn):
        @wraps(fn)
        def dbxauth(*args, **kwargs):
            #print 'gbdev: ' + fn.__name__ + " was called"
            self = args[0]
            if self.dbx == None:
                self._try_dbxauth()
            return fn(*args, **kwargs)
        return dbxauth

    def _log_revs_md(self, md_l, log_path, hrdb_path):
        self._debug('_log_revs_md %s %s' % (len(md_l), log_path))
        if os.path.isfile(log_path):
            os.remove(log_path)
        make_sure_path_exists(os.path.dirname(log_path))
        hrdb = pickledb.load(hrdb_path, 'False')
        with open(os.path.expanduser(log_path), "wb") as logf:
            for md in md_l:
                logf.write('%s%s%s%s%s%s%s\n' % (md.rev, OXLYSEP1,
                                             md.server_modified,
                                             OXLYSEP1, md.size,
                                             OXLYSEP1, md.content_hash,))
                #xxx check if key already exists??
                hrdb.set(md.content_hash, md.rev)
            hrdb.dump()
            
    @_dbxauth
    def _download_data_one_rev(self, rev, src):
        dest = self.repo
        self._debug('_download_data_one_rev: %s, %s, %s' % (rev, src, dest))
        dest_data = self._get_pname_by_rev(src, rev)
        self._debug('_download_one_rev: dest_data %s' % dest_data)
        try:
            self.dbx.files_download_to_file(dest_data, src, rev)
        except Exception as err:
            print('Call to Dropbox to download file data failed: %s' % err)
            sys.exit(1)

    @_dbxauth
    def _download_ancdb(self, ancdb_path, init_ancdb):
        self._debug('_download_ancdb: ancdb_path %s' % ancdb_path)
        ancdb_fp = self.repo + '/' + ancdb_path # full path
        rem_path = '/'+ancdb_path
        try:
            self.dbx.files_download_to_file(ancdb_fp, rem_path)
            return True
        except ApiError as err:
            if err.error.is_path() and err.error.get_path().is_not_found():
                if init_ancdb:
                    print(' ancestor db not on Dropbox yet so it will be created ...')
                    return False
                print('Warning: ancestor db %s not found on Dropbox.' % rem_path)
                print('Warning: did you run \'oxly clone --init-ancdb url\' once to init this file?')
                print('Warning: See README.md doc for full oxly process.')
                sys.exit(1)
            else:
                print('Call to Dropbox to download ancestor db data failed: %s' % err)
                sys.exit(1)
        except Exception as err:
            print('Call to Dropbox to download ancestor db data failed: %s'
                     % err)
            sys.exit(1)
            
    @_dbxauth
    def _get_revs_md(self, path, nrevs):
        self._debug('debug: _get_revs_md %s, %d' % (path, nrevs))
        try:
            revs = sorted(self.dbx.files_list_revisions(path,
                                                        limit=nrevs).entries,
                          key=lambda entry: entry.server_modified,
                          reverse=True)
        except Exception as err:
            sys.exit('Call to Dropbox to list file revisions failed: %s' % err)
        if not revs:
            self._debug('debug: _get_revs_md rt not')
        return revs

    # Start get_pname internal api
    #

    def _get_pname_index(self):
        return self._get_pname_home_base_tmp() + '/' + 'oxly'\
            + OXLYSEP1 + OXLYINDEX

    def _get_pname_index_path(self, path):
        return self._get_pname_index() + '/' + path

    def _get_pname_wt_path(self, path):
        return self._get_pname_repo_base() + '/' + path

    def _get_pname_repo_base(self):
        return self.repo

    def _hash2rev(self, filepath, hash):
        hrdb = pickledb.load(self._get_pname_hrdbpath(filepath),
                             'False')
        return hrdb.get(hash)
    
    def _head2rev(self, path, rev):
        r = rev.lower()
        if r == 'head':
            logs = self._get_log(path)
            h = logs[0]
            (rev, date, size, content_hash) = h.split(OXLYSEP1)
        elif r == 'headminus1':
            logs = self._get_log(path)
            if len(logs) == 1:
                sys.exit('warning: only one rev so far so no headminus1')
            h = logs[1]
            (rev, date, size, content_hash) = h.split(OXLYSEP1)
        return rev

    def _get_pname_by_rev(self, path, rev='head'):
        if rev == 'head' or rev == 'headminus1':
            rev = self._head2rev(path, rev)

        self._debug('by_rev: rev=%s' % rev)
        pn_revdir = self._get_pname_home_revsdir(path)
        make_sure_path_exists(pn_revdir)
        return pn_revdir + '/' + rev

    def _get_pname_logpath(self, path):
        # one per file
        return self._get_pname_home_revsdir(path) + '/' + LOGFILENAME

    def _get_pname_hrdbpath(self, path):
        # one per file
        return self._get_pname_home_revsdir(path) + '/' + HASHREVDB

    #xxx
    def OLD_get_pname_mmpath(self):
        mm_path = self._get_pname_home_base() + '/.oxly'\
                  + OXLYSEP1 + OXLYMETAMETA
        return os.path.expanduser(mm_path)

    def _get_pname_home_revsdir(self, path):
        base_path = self._get_pname_home_base()
        path_dir = os.path.dirname(path)
        path_f = os.path.basename(path)
        return base_path + '/' + path_dir + '/.oxly' + OXLYSEP1 + path_f

    def _get_pname_home_base(self):
        return self.repo + '/' + self.home

    def _get_pname_home_base_tmp(self):
        return self._get_pname_home_base() + '/.tmp'
    
    def _get_pname_home_paths(self):
        path = self._get_pname_home_base_tmp() + '/oxly' + OXLYSEP1 + 'filepaths'
        return os.path.expanduser(path)

    def _get_pname_by_wdrev(self, path, rev):
        if rev == 'head' or rev == 'headminus1':
            rev = self._head2rev(path, rev)

        return self._get_pname_wt_path(path) + OXLYSEP1 + rev

    def _get_pname_wdrev_ln(self, path, rev, suffix=''):
        """Return linked file path of rev::suffix in wd.
        """
        self._debug("_get_pname_wdrev_ln: %s, %s" % (path, rev))
        src = self._get_pname_by_rev(path, rev)
        dest = self._get_pname_by_wdrev(path, rev)
        dest = dest + suffix
        if not os.path.isfile(dest):
            self._debug("_get_pname_wdrev_ln no dest lets ln it: %s, %s" % (src, dest))
            os.system("ln %s %s" % (src, dest))
        else:
            isrc = os.stat(src).st_ino
            idest = os.stat(dest).st_ino
            self._debug("_get_pname_wdrev_ln: src/dest got dest file now cmp inodes (%d)" % isrc)
            if isrc != idest:
                make_sure_path_exists(OLDDIR)
                os.system("mv %s %s" % (dest, OLDDIR))
                self._debug("_get_pname_wdrev_ln: post old ln mv, src/dest hard linkn me maybe")
                os.system("ln %s %s" % (src, dest))
        return dest

    # End get_pname internal api

    # Start _repohome_files internal api
    def _repohome_files_put(self, path):
        self._debug('debug _repohome_paths_put start %s' % path)
        f = open(self._get_pname_home_paths(), "a")
        f.write('%s\n' % path)
        f.close()

    def _repohome_files_get(self):
        # Return list of all relative path of files in home
        self._debug('debug _repohome_paths_get start')
        p = self._get_pname_home_paths()
        try:
            with open(p) as f:
                content = f.readlines()
        except IOError as err:
            sys.exit('internal error: repo home file of file paths not found')
        self._debug('debug _repohome_paths_get end %s' % content)
        return [x.rstrip() for x in content]

    # End _repohome_files internal api

    def _get_fp_triple(self, fp):
        # Given an fp, return a triple wt/index/head
        # where each is a fp if it exists else None.
        wt = self._get_pname_wt_path(fp)
        self._debug('debug triple wt: %s' % wt)
        wt = None if not os.path.isfile(wt) else wt
        ind = self._get_pname_index_path(fp)
        ind = None if not os.path.isfile(ind) else ind
        head = self._get_pname_by_rev(fp)
        head = None if not os.path.isfile(head) else head
        return wt, ind, head

    def checkout(self, filepath):
        """Checkout/copy file from .oxly/ to working dir (wd).

        if staged version exists revert wd one to it instead.
        """
        if filepath:
            if not os.path.isfile(self._get_pname_by_rev(filepath)):
                sys.exit('error: filepath name not found in repo home -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._repohome_files_get()

        if not fp_l:
            print('internal error: checkout2 repo home empty')
            sys.exit(1)
    
        make_sure_path_exists(self._get_pname_index())
        for p in fp_l:
            self._debug('debug checkout2 p=`%s`' % p)
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            if p_wt:
                #xxx save wt data first?
                if p_ind:
                    self._debug('debug checkout2: cp index wt')
                    os.system('cp %s %s' % (p_ind, p_wt))
                elif p_head:
                    self._debug('debug checkout2: cp head wt')
                    os.system('cp %s %s' % (p_head, p_wt))
            else:
                    self._debug('debug checkout2 no wt: cp head wt')
                    make_sure_path_exists(
                        os.path.dirname(self._get_pname_wt_path(p)))
                    os.system('cp %s %s' % (p_head,
                                            self._get_pname_wt_path(p)))

    def _get_conf(self, key):
        path = os.path.expanduser(self.conf)
        if not os.path.isfile(path):
            sys.exit('error: conf file not found: %s' % self.conf)
        cf = ConfigParser.RawConfigParser()
        cf.read(path)
        return cf.get('misc', key)

    def _mmdb_populate(self, src_url, nrevs):
        # Concoct&save orgzly_dir&ancdb path
        # ancdb per dir or one per tree??? --later
        orgzly_dir = src_url.split('//')[1].split('/')[0] #top dir only
        ancdb_path = orgzly_dir + '/' + ANCDBNAME

        # Save meta meta & update master file path list
        self.mmdb.set('remote_origin', src_url)
        self.mmdb.set('orgzly_dir', orgzly_dir)
        self.mmdb.set('ancdb_path', ancdb_path)
        self.mmdb.set('nrevs', nrevs)
        self.mmdb.dump()

    def clone(self, dry_run, src_url, nrevs, init_ancdb, dl_ancdb=True):
        """Given a dropbox url for one file*, fetch the
        n revisions of the file and store locally in repo's
        .oxly dir and checkout HEAD to working dir.
        *current limit -- might be expanded
        """
        nrevs = int(nrevs)
        self._debug('debug clone: nrevs=%d' % (nrevs))

        if nrevs > NREVS_MAX:
            print('Warning: max number of revisions for free service is %s' % NREVS_MAX)

        if dry_run:
            print('clone dry-run: remote repo = %s' % src_url)
            print('clone dry-run: local repo = %s' % self.repo)
            sys.exit(0)

        self.init()

        # src_url should-not-must be a dropbox url for chrimony sakes
        filepath = src_url.lower()  # XXX dbx case insensitive
        if filepath.startswith('dropbox://'):
            filepath = filepath[len('dropbox:/'):]  # keep single leading slash
        if not filepath.startswith('/') or filepath.endswith('/'):
            print('error: URL must have leading slash and no trailing slash')
            sys.exit(1)

        pl = filepath.split('/')
        if len(pl) < 3:
            sys.exit('Error: url form is dropbox://<orgzly>/[/<subdirs>/]<file.org>')
        
        repo_home = self._get_pname_home_base() + filepath
        repo_home_dir = os.path.dirname(os.path.expanduser(repo_home))
        make_sure_path_exists(repo_home_dir)

        self._mmdb_populate(src_url, nrevs)

        self._repohome_files_put(filepath.strip('/'))

        # Finally! download the revs data and checkout themz to wt
        self._debug('debug clone: download %d revs of %s to %s' % (nrevs,
                                                                   filepath,
                                                                   self.repo))
        # Get revs' metadata
        print("Downloading metadata of %d (max) latest revisions on Dropbox ..." %
              nrevs, end='')
        md_l = self._get_revs_md(filepath, nrevs)
        print(' done.')
        self._log_revs_md(md_l,
                          self._get_pname_logpath(filepath),
                          self._get_pname_hrdbpath(filepath))
        print('Checking 2 latest revisions in Dropbox...')
        self.pull(md_l[0].rev, filepath)
        if len(md_l) > 1:
            self.pull(md_l[1].rev, filepath)
        else:
            print('\tonly one revision found.')
        self.checkout(filepath)
        if dl_ancdb:
            print('Downloading ancestor db ...', end='')
            rt = self._download_ancdb(self.mmdb.get('ancdb_path'),
                                      init_ancdb)
            if rt:
                print(' done.')
            if init_ancdb:
                self._debug('clone: init_ancdb True')
                self.ancdb_set(filepath.strip('/'))
                self._ancdb_pushit()
            else:
                self._debug('clone: init_ancdb False')
                ancdb = self._open_ancdb()
                anchash = ancdb.get(filepath.strip('/'))
                if anchash == None:
                    print('Warning: ancestor hash and rev not found: clone anchash==None')
                    print('Warning: 3-way merge cant be done now, to merge by hand w/emacsclient ediff and reset ancestor db:')
                    print('Warning: \toxly merge2 %s' % filepath.strip('/'))
                    print('Warning: \toxly push --add %s' % filepath.strip('/'))
                    sys.exit(1)
                rev = self._hash2rev(filepath, anchash)
                if rev == None:
                    print('Warning: ancestor rev not found in local metadata cache; anchash=%s' % anchash[:8])
                    if nrevs < NREVS_MAX:
                        print('Warning: Try clone with higher nrevs (%d max).' % NREVS_MAX)
                        print('Warning: try; oxly clone --nrevs %d %s' % (NREVS_MAX, src_url))
                        print('Warning: if that succeeds, you can rerun oxmerge or continue with oxly merge.')
                    else:
                        print('Warning: max nrevs (for free svc, %d) have been downloaded and rev not found.' % NREVS_MAX)
                        print('Warning: 3-way merge cant be done now, to merge by hand w/emacsclient ediff and reset ancestor db:')
                        print('Warning: \toxly merge2 %s' % filepath.strip('/'))
                        print('Warning: \toxly push --add %s' % filepath.strip('/'))
                    sys.exit(1)
                print('Checking ancestor rev data ...')
                self.pull(rev, filepath)

    def _add_one_path(self, path):
        # cp file from working tree to index tree dir
        index_path = self._get_pname_index()
        dp = os.path.dirname(path)
        if dp:
            index_path = index_path + '/' + dp
        wt = self._get_pname_wt_path(path)
        self._debug('debug _add_one_path cp %s %s' % (wt, index_path))
        make_sure_path_exists(index_path)
        os.system('cp %s %s' % (wt, index_path))

    def add(self, filepath):
        """Copy file from wd to index (aka staging area)"""
        self._debug('debug: start add: %s' % filepath)
        fp_l = self._get_paths(filepath)
        for p in fp_l:
            self._add_one_path(p)

    def _reset_one_path(self, path):
        ind_path = self._get_pname_index() + '/' + path
        if not os.path.isfile(ind_path):
            sys.exit('error: file does not exist in index (staging area): %s'
                     % path)
        os.unlink(ind_path)

    def reset(self, filepath):
        """Remove file from index (staging area)"""
        self._debug('debug: start reset: %s' % filepath)
        if filepath:
            self._reset_one_path(filepath)
            return
        fp_l = self._get_index_paths()
        for p in fp_l:
            self._reset_one_path(p)

    def _get_wt_paths(self):
        wt_dir = self._get_pname_repo_base()
        self._debug('debug: _get_wt_paths: %s' % wt_dir)
        return get_relpaths_recurse(wt_dir)

    def _scrub_fnames(self, fp_l):
        ifp_l = itertools.ifilterfalse(lambda x: x.startswith('.oxly'), fp_l)
        if not ifp_l:
            return None
        # emacs prev version
        ifp_l = itertools.ifilterfalse(lambda x: x.endswith('~'), ifp_l)
        if not ifp_l:
            return None
        return ifp_l
    
    def status(self, filepath):
        """List modified file(s) in staging area or wd"""
        if filepath:
            if not os.path.isfile(self._get_pname_wt_path(filepath)):
                sys.exit('error: file name not found in repo wt -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._get_wt_paths()

        ifp_l = self._scrub_fnames(fp_l)
        if not ifp_l:
            print('warning: internal err status: wt paths empty')
            sys.exit(1)

        self._debug('debug status2 %s' % ifp_l)
        # changes staged but not pushed
        mods = 0
        for p in ifp_l:
            self._debug('debug status2 p=%s' % p)
            modded = False
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            if p_ind and p_head:
                modded = not filecmp.cmp(p_ind, p_head)
            if modded:
                mods += 1
                if mods == 1:
                    print('Changes to be pushed:')
                print('\tmodified: %s' % p)

        # changes not staged
        ifp_l = self._scrub_fnames(fp_l)
        mods = 0
        for p in ifp_l:
            self._debug('debug status2 p=%s' % p)
            modded = False
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            self._debug('debug status triple wt: %s' % p_wt)
            self._debug('debug status triple head: %s' % p_head)
            if not p_wt:
                pass
                # Damned if ya do
                # print('warning: file does not exist in wt: %s' % p)
            elif p_ind:
                modded = not filecmp.cmp(p_wt, p_ind)
            else:
                self._debug('debug status else wt: %s' % p_wt)
                self._debug('debug status else head: %s' % p_head)
                modded = not filecmp.cmp(p_wt, p_head)
            if modded:
                mods += 1
                if mods == 1:
                    print('\nChanges not staged:')
                print('\tmodified: %s' % p)

    # xxx still needed??
    def _get_paths(self, path):
        # todo: recurse wt --> list
        return [path]

    def _wd_or_index(self, rev, p):
        if rev == 'wd':
            return self._get_pname_wt_path(p)
        if rev == 'index':
            return self._get_pname_index_path(p)
        return None

    def _get_diff_pair(self, reva, revb, path):
        ap = self._wd_or_index(reva, path)
        bp = self._wd_or_index(revb, path)
        ap = ap if ap else self._get_pname_wdrev_ln(path, reva)
        self._debug("_get_diff_pair: ap=%s" % ap)
        bp = bp if bp else self._get_pname_wdrev_ln(path, revb)
        return ap, bp

    def _diff_one_path(self, diff_cmd, reva, revb,  path):
        self._pull_me_maybe(reva.lower(), path)
        self._pull_me_maybe(revb.lower(), path)
        (fa, fb) = self._get_diff_pair(reva.lower(), revb.lower(), path)
        diff_cmd = diff_cmd if diff_cmd else DEFAULT_DIFF_CMD
        self._debug('debug _diff2_one_path: %s' % diff_cmd)
        shcmd = diff_cmd % (fa, fb)
        self._debug('debug _diff2_one_path: %s' % shcmd)
        os.system(shcmd)

    def diff(self, diff_cmd, reva, revb, filepath):
        """Run diff_cmd to display diffs from two revisions of file.

        diff_cmd format: program %s %s
        """
        self._debug('debug2: start diff: %s %s %s' % (reva, revb, filepath))
        if reva == revb:
            sys.exit('error: reva and revb the same yo diggity just no')

        if filepath:
            if not os.path.isfile(self._get_pname_wt_path(filepath)):
                sys.exit('error: file name not found in repo working dir -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._get_wt_paths()

        ifp_l = self._scrub_fnames(fp_l)
        if not ifp_l:
            sys.exit('warning: internal err diff: wt empty')
        for p in ifp_l:
            self._debug('debug diff2 p=%s' % p)
            self._diff_one_path(diff_cmd, reva, revb, p)

    def pull(self, rev, filepath):
        self._debug('pull: %s, %s' % (rev, filepath))
        fp = self._wd_or_index(rev, filepath)
        fp = fp if fp else self._get_pname_by_rev(filepath, rev)
        self._debug('pull: fp %s' % (fp))
        if not os.path.isfile(fp):
            filepath = filepath if filepath[0] == '/' else '/'+filepath 
            print('\tdownloading rev %s data ...' % rev, end='')
            if self.debug:
                print()
            self._download_data_one_rev(rev, filepath)
            print(' done.')
        else:
            print('\trevision %s already downloaded.' % rev)

    def _pull_me_maybe(self, rev, filepath):
        fp = self._wd_or_index(rev, filepath)
        fp = fp if fp else self._get_pname_by_rev(filepath, rev)
        if not os.path.isfile(fp):
            sys.exit('Warning: rev data is not local. Pls run: oxly pull --rev %s %s'
                     % (rev, filepath))

    def _cat_one_path(self, cat_cmd, rev, filepath):
        self._pull_me_maybe(rev.lower(), filepath)
        cat_cmd = cat_cmd if cat_cmd else DEFAULT_CAT_CMD
        self._debug('debug _cat_one_path: %s' % cat_cmd)
        fp = self._wd_or_index(rev, filepath)
        fp = fp if fp else self._get_pname_by_rev(filepath, rev)
        try:
            shcmd = cat_cmd % (fp)
        except TypeError:
            sys.exit('cat cat-cmd bad format. Try: oxly cat --help')
        self._debug('debug _cat_one_path: %s' % shcmd)
        os.system(shcmd)
            
    def cat(self, cat_cmd, rev, filepath):
        """Run cat_cmd to display cats from a revision of file.

        cat_cmd format: program %s
        """
        self._debug('debug start cat: %s %s' % (rev, filepath))
        if filepath:
            if not os.path.isfile(self._get_pname_wt_path(filepath)):
                sys.exit('error: file name not found in repo working dir -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._get_wt_paths()

        ifp_l = self._scrub_fnames(fp_l)
        if not ifp_l:
            sys.exit('warning: internal err cat: wt empty')
        for p in ifp_l:
            self._debug('debug cat p=%s' % p)
            self._cat_one_path(cat_cmd,
                               self._head2rev(p, rev.lower()),
                               p)
            
    def _open_ancdb(self):
        ancdb_path = self.repo + '/' + self.mmdb.get('ancdb_path')
        if not ancdb_path:
            print('Error: ancestor db not found. Was oxly clone run?')
            sys.exit(1)
        return pickledb.load(ancdb_path, 'False')

    def _set_ancdb(self, filepath):
        if filepath[0] != '/':
            fp = self.repo + '/' + filepath
        else:
            fp = filepath
        self._debug('_set_ancdb calc hash of %s' % fp)
        hash = calc_dropbox_content_hash(fp)
        ancdb = self._open_ancdb()
        ancdb.set(filepath, hash)
        ancdb.dump()
        return hash

    def ancdb_set(self, filepath):
        hash = self._set_ancdb(filepath)
        print('Dropbox file content_hash %s added to ancestor db locally.' % hash[:8])

    def ancdb_get(self, filepath):
        ancdb = self._open_ancdb()
        print('%s' %  ancdb.get(filepath))

    def _ancdb_pushit(self):
        self._push_ancestor_db()
        
    def ancdb_push(self, filepath): # --set
        # lockmemaybe upstream
        print('Downloading latest ancestor db ...', end='')
        rt = self._download_ancdb(self.mmdb.get('ancdb_path'), True)
        if rt:
            print(' done.')
        self.ancdb_set(filepath)
        self._ancdb_pushit()
        # unlockmemaybe upstream
        
    def calc_dropbox_hash(self, filepath):
        """Calculate/display the Dropbox files metadata content_hash of the version in the working dir.
        """
        # cmd needed for lulz?
        print('The Dropbox file content_hash is %s' %
              calc_dropbox_content_hash(filepath))
    
    def merge3(self, dry_run, merge_cmd, reva, revb, filepath):
        """Run cmd for 3-way merge (aka auto-merge when possible)
        """
        reva = self._head2rev(filepath, reva)
        revb = self._head2rev(filepath, revb)

        self._pull_me_maybe(reva, filepath)
        self._pull_me_maybe(revb, filepath)
        (fa, fb) = self._get_diff_pair(reva, revb, filepath)
        ancdb = self._open_ancdb()
        hash = ancdb.get(filepath)
        if hash == None:
            print('Warning hash==None: cant do a 3-way merge as ancestor revision not found.')
            sys.exit('Warning: you can still do a 2-way merge (oxly merge2 --help).')
        anc_rev = self._hash2rev(filepath, hash)
        if anc_rev == None: #not enough revs downloaded 
            print('Warning ancrev==None: cant do a 3-way merge as no ancestor revision found.')
            sys.exit('Warning: you can still do a 2-way merge (oxly merge2 --help).')
            sys.exit(1)

        if reva == anc_rev:
            print('Warning: reva %s == anc_rev %s' % (reva, anc_rev))
            print('Warning: does not look like a merge is necessary. Try Sync on Orgzly.')
            sys.exit('Warning: you can still do a 2-way merge if necessary (oxly merge2 --help).')
        if revb == anc_rev:
            print('Warning: revb %s == anc_rev %s' % (revb, anc_rev))
            print('Warning: does not look like a merge is necessary, try Sync on Orgzly.')
            sys.exit('Warning: you can still do a 2-way merge if necessary (oxly merge2 --help).')
            sys.exit(1)
        f_anc = self._get_pname_wdrev_ln(filepath, anc_rev, suffix=':ANCESTOR')
        mcmd = margs = None
        if merge_cmd:
            mc = merge_cmd.split(' ')
            mcmd = mc[0]
            margs = mc[1:] if len(mc)>1 else []
        mcmd = [mcmd] if mcmd else [DIFF3_BIN]
        margs = margs if margs else [DIFF3_BIN_ARGS]
        cmd3 = mcmd + margs + [fa, f_anc, fb]
        self._debug('debug merge3: cmd3=%s' % cmd3)
        if dry_run:
            print('merge3 dry-run: %s' % cmd3)
        tmpf = '/tmp/tmpoxlymerge3.' + str(os.getpid())
        fname = '/dev/null' if dry_run else tmpf
        with open(fname, 'w') as fout:
            rt = sp.call(cmd3, stdout=fout)
            self._debug('debug merge3: rt=%d, fname=%s' % (rt, fname))
            if dry_run:
                print('merge3 dry-run: %s exit value=%d' % (cmd3[0], rt))
                sys.exit(rt)
            if rt > 1:
                print('Error: diff3 returned %d' % rt)
            if rt == 0:
                os.system('mv %s %s' % (fname, filepath))
                print('No conflicts found. File fully merged locally in %s'  % filepath)
            if rt == 1:
                fcon = filepath + ':CONFLICT'
                os.system('mv %s %s' % (fname, fcon))
                print('Conflicts found, pls run either ...')
                print('\temacsclient ediff 3-way merge: oxly mergerc --reva %s --revb %s %s' % (reva, revb, filepath))
                print('\t\t then run: oxly push --add %s' % (filepath))
                print('\tedit diff3 output: $EDITOR %s' % (fcon))
                print('\t\t then run: mv %s %s' % (fcon, filepath))
                print('\t\t then run: oxly push --add %s' % (filepath))
            sys.exit(rt)
            
    def merge3_rc(self, dry_run, emacsclient_path, mergerc_cmd, reva, revb, filepath):
        """Run mergerc_cmd to allow user to merge 3 revs.

        merge_cmd format:  program %s %s
        """
        reva = self._head2rev(filepath, reva)
        revb = self._head2rev(filepath, revb)
        self._pull_me_maybe(reva, filepath)
        self._pull_me_maybe(revb, filepath)
        (fa, fb) = self._get_diff_pair(reva, revb, filepath)
        ancdb = self._open_ancdb()
        hash = ancdb.get(filepath)
        if hash == None:
            print('Warning hash==None: cant do a 3-way merge as ancestor revision not found.')
            sys.exit('Warning: you can still do a 2-way merge (oxly merge2 --help).')
        anc_rev = self._hash2rev(filepath, hash)
        if anc_rev == None: #not enough revs downloaded 
            print('Warning ancrev==None: cant do a 3-way merge as no ancestor revision found.')
            sys.exit('Warning: you can still do a 2-way merge (oxly merge2 --help).')
            sys.exit(1)

        if reva == anc_rev:
            print('Warning: reva %s == anc_rev %s' % (reva, anc_rev))
            print('Warning: does not look like a merge is necessary. Try Sync on Orgzly.')
            sys.exit('Warning: you can still do a 2-way merge if necessary (oxly merge2 --help).')
        if revb == anc_rev:
            print('Warning: revb %s == anc_rev %s' % (revb, anc_rev))
            print('Warning: does not look like a merge is necessary, try Sync on Orgzly.')
            sys.exit('Warning: you can still do a 2-way merge if necessary (oxly merge2 --help).')
            sys.exit(1)
        f_anc = self._get_pname_wdrev_ln(filepath, anc_rev, suffix=':ANCESTOR')
        qs = lambda(s): '\"' + s + '\"'
        (fa, fb) = self._get_diff_pair(reva, revb, filepath)
        if mergerc_cmd:
            shcmd = mergerc_cmd % (qs(fa), qs(fb), qs(f_anc))  # quotes cant hurt, eh?
        elif emacsclient_path:
            m_cmd = emacsclient_path + '/' + DEFAULT_MERGE3RC_CMD
            shcmd = m_cmd % (qs(fa), qs(fb), qs(f_anc))
        else:
            shcmd = DEFAULT_MERGE3RC_CMD % (qs(fa), qs(fb), qs(f_anc))
        self._debug('debug mergerc: %s' % shcmd)
        if dry_run:
            print('mergerc dry-run: %s' % shcmd)
            return
        os.system(shcmd)
        
    def merge(self, dry_run, merge_cmd, reva, revb, filepath):
        """Run cmd for 3-way merge (aka auto-merge when possible)
        """
        self.merge3(dry_run, merge_cmd, reva, revb, filepath)

    def merge_rc(self, dry_run, emacsclient_path, mergerc_cmd, reva, revb, filepath):
        """If the 3-way diff/merge finished with some conflicts to resolve, run the editor to resolve them"
        """
        self.merge3_rc(dry_run, emacsclient_path, mergerc_cmd, reva, revb, filepath)

    def merge2(self, dry_run, emacsclient_path, merge_cmd, reva, revb, filepath):
        """Run merge_cmd to allow user to merge two revs.

        merge_cmd format:  program %s %s
        """
        self._pull_me_maybe(reva.lower(), filepath)
        self._pull_me_maybe(revb.lower(), filepath)
        qs = lambda(s): '\"' + s + '\"'
        (fa, fb) = self._get_diff_pair(reva.lower(), revb.lower(), filepath)
        if merge_cmd:
            shcmd = merge_cmd % (qs(fa), qs(fb))  # quotes cant hurt, eh?
        elif emacsclient_path:
            m_cmd = emacsclient_path + '/' + DEFAULT_MERGE_CMD
            shcmd = m_cmd % (qs(fa), qs(fb))
        else:
            shcmd = DEFAULT_MERGE_CMD % (qs(fa), qs(fb))
        self._debug('debug merge: %s' % shcmd)
        if dry_run:
            print('merge dry-run: %s' % shcmd)
            return
        os.system(shcmd)

    def init(self):
        """Initialize local repo .oxly dir"""
        base_path = self._get_pname_home_base()
        if os.path.isdir(base_path) or os.path.isfile(base_path):
            self._save_repo()

        make_sure_path_exists(base_path)

        # mmdb one per repo
        #self.mmdb_path_dir = self.repo + '/' + OXLYHOME + '/.tmp'
        self.mmdb_path_dir = self._get_pname_home_base_tmp()
        make_sure_path_exists(self.mmdb_path_dir)
        self.mmdb_path = self.mmdb_path_dir + '/oxly' + OXLYSEP1 + OXLYMETAMETA
        self.mmdb = pickledb.load(self.mmdb_path, False)
            
        self._debug('debug init: set basic vars in mmdb')
        self.mmdb.set('version', __version__)
        self.mmdb.set('home_version', OXLYDIRVERSION)
        self.mmdb.set('repo_local', self.repo)
        self.mmdb.dump()

    def _get_log(self, path):
        self._debug('debug _get_log start %s' % path)
        # on disk '$fileOXLYSEP2log':
        #   $rev||$date||$size
        log_path = self._get_pname_logpath(path)
        self._debug('debug _get_log `%s`' % log_path)
        try:
            with open(log_path) as f:
                content = f.readlines()
        except IOError as err:
            sys.exit('error: log file not found -- check file name spelling or if clone completed ok')
        return content

    def _log_one_path(self, oneline, recent, path):
        # on disk '$fileOXLYSEP2log':
        #   $rev $date $size $hash
        nout = 0
        logs = self._get_log(path)
        if oneline:
            for l in logs:
                if nout >= recent:
                    break

                (rev, date, size, content_hash) = l.split(OXLYSEP1)
                print('%s\t%s\t%s\t%s' % (rev, size.rstrip(),
                                          utc_to_localtz(date),
                                          content_hash[:8]))
                nout += 1
        else:
            for l in logs:
                if nout >= recent:
                    break

                (rev, date, size, content_hash) = l.split(OXLYSEP1)
                print('Revision:  %s' % rev)
                print('Size (bytes):  %s' % size.rstrip())
                print('Server modified:  %s' % utc_to_localtz(date))
                print('Content hash:  %s' % content_hash)
                nout += 1

 
    def log(self, oneline, recent, filepath):
        """List all local revisions (subset of) meta data""" 
        self._debug('debug: start log: %s' % filepath)
        fp_l = self._get_paths(filepath)
        l = len(fp_l)
        for p in fp_l:
            if l > 1:
                print('%s:' % p)
            self._log_one_path(oneline, recent, p)
            if l > 1:
                print()

    @_dbxauth
    def _push_one_path(self, path):
        # Push a given path upstream
        rem_path = '/' + path
        index_dir = self._get_pname_index()
        local_path = index_path = index_dir + '/' + path

        # Skip if no change from current rev
        logs = self._get_log(path)
        head = logs[0]
        (rev, date, size, hash) = head.split(OXLYSEP1)
        head_path = self._get_pname_by_rev(path, rev)
        if filecmp.cmp(index_path, head_path):
            print('Warning: no change between working dir version and HEAD (latest version cloned).')
            sys.exit('Warning: so no push needed.')
        self._debug('debug push one path: %s' % local_path)
        with open(local_path, 'rb') as f:
            print("Uploading staged " + path + " to Dropbox as " +
                  rem_path + " ...", end='')
            try:
                self.dbx.files_upload(f.read(), rem_path, mode=WriteMode('overwrite'))
                print(' done.')
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().error.is_insufficient_space()):
                    sys.exit("ERROR: Cannot back up; insufficient space.")
                elif err.user_message_text:
                    print(err.user_message_text)
                    sys.exit(100)
                else:
                    print(err)
                    sys.exit(101)
            except Exception as err:
                sys.exit('Call to Dropbox to upload file data failed: %s' % err)

        hash = calc_dropbox_content_hash(local_path)
        os.remove(index_path)
        return hash

    
    @_dbxauth
    def _push_ancestor_db(self):
        ancdb_path = self.mmdb.get('ancdb_path')  # *ass*ume relative to repo
        if not ancdb_path:
            print('Error: ancestor db not found. Was oxly clone run?')
            sys.exit(1)
        rem_path = '/' + ancdb_path
        ancdb_fp = self.repo + '/' + ancdb_path # full path
        with open(ancdb_fp, 'rb') as f:
            print("Uploading ancestor db to Dropbox as " + '/' + ancdb_path + " ...", end='')
            try:
                self.dbx.files_upload(f.read(), rem_path, mode=WriteMode('overwrite'))
                print(' done.')
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().error.is_insufficient_space()):
                    print("ERROR: Cannot upload; insufficient space.")
                    print('When problem resolved, try:')
                    print('\noxly ancdb_push')
                    print("Then select Sync (regular, Forced not neccessary) note on Orgzly now.")
                    print("It should be done before any other changes are saved to this file on Dropbox.")
                    sys.exit(1)
                elif err.user_message_text:
                    print(err.user_message_text)
                    print('When problem resolved, try:')
                    print('\noxly ancdb_push')
                    print("Then select Sync (regular, Forced not neccessary) note on Orgzly now.")
                    print("It should be done before any other changes are saved to this file on Dropbox.")
                    sys.exit(1)
                else:
                    print(err)
                    sys.exit(1)
            except Exception as err:
                sys.exit('Call to Dropbox to upload ancestor db failed: %s' % err)

    def _get_index_paths(self):
        index_dir = self._get_pname_index()
        return get_relpaths_recurse(index_dir)

    def push(self, dry_run, add, post_push_clone, filepath):
        """Push/upload staged file upstream to Dropbox.

        post_push_clone -- bool -- normally after push completes
           a clone is done to resync with Dropbox
        """
        fp_l = self._get_index_paths()
        self._debug('debug push: %s' % fp_l)
        if post_push_clone:
                    self._debug('debug post_push_clone true')

        if filepath:
            if filepath not in [s.strip('./') for s in fp_l]:
                if filepath.startswith('dropbox:'):
                    print('Warning: file should be local path not url')
                if not add:
                    sys.exit('Warning: %s not in index. Try push --add.' % filepath)
            if dry_run:
                print('push dryrun add: %s' % add)
                print('push dryrun filepath: %s' % filepath)
                print('push dryrun from local repo: %s' % self.repo)
                print('push dryrun to remote repo: %s' %
                      self._get_mmval('remote_origin'))
            else:
                if add:
                    self._add_one_path(filepath)
                self._push_one_path(filepath)
                print('Running ancdb_push ...') # in case it fails, user can rerun it
                self.ancdb_push(filepath)
        else:
            if not fp_l:
                print('Nothing to push')
                return
            for p in fp_l:
                if dry_run:
                    print('push dryrun add: %s' % add)
                    print('push dryrun filepath: %s' % filepath)
                    print('push dryrun from local repo: %s' % self.repo)
                    print('push dryrun to remote repo: %s' %
                          self._get_mmval('remote_origin'))
                else:
                    if add:
                        self._add_one_path(filepath)
                    print('Running ancdb_push ...') # in case it fails, user can rerun it
                    self.ancdb_push(filepath)

        if dry_run:
            return

        dropbox_url = self._get_mmval('remote_origin')
        if dropbox_url and post_push_clone:
            nrevs = self._get_mmval('nrevs')
            self._save_repo()
            print('Re-cloning to get current metadata/data from Dropbox...')
            self.clone(dry_run, dropbox_url, nrevs, dl_ancdb=False)

        # Our work is done here praise $DIETY as the user syncs on Orgzly.
        print("\nPlease select Sync (regular, Forced not necessary) note on Orgzly now.")
        print("It should be done before any other changes are saved to this file on Dropbox/Emacs/Orgzly.")

    def _save_repo(self):
        # Save current .oxly/.tmp (includes index dir, maybe for recovery?).
        # This will save/clear repo metmaeta but not per file
        # revs data/revhashdb/etc which we like to persist between clones.
        src = self._get_pname_home_base_tmp()
        if os.path.isdir(src):
            dest = self._get_pname_home_base() + '/' + OLDDIR + '/oxlytmp.' + str(os.getpid())
            make_sure_path_exists(dest)
            print('Moving/saving old %s to %s ...'
                  % (src, dest), end='')
            os.system('mv %s %s' % (src, dest))
            print(' done.')
            if self.mmdb:
                self.mmdb = None #xxx del?
                
    def _get_mmval(self, key):
        return self.mmdb.get(key)

    def getmm(self, key):
        """Fetch internal oxly sys file vars -- mostly for debug"""
        print('%s=%s' % (key, self._get_mmval(key)))

