
import sys
import os
import random
import filecmp
import ConfigParser
import string
import json
import itertools
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from .utils import make_sure_path_exists, get_relpaths_recurse

__version__ = "0.5.0" #xxx mv to setup

OXITDIRVERSION = "1"
OXITSEP1 = '::'
OXITSEP2 = ':::'
OXITMETAMETA = 'metameta'
OXITINDEX = '.index'

# Default merge cmd
MERGE_BIN = "emacsclient"
MERGE_EVAL  = "--eval"
MERGE_EVALFUNC = "ediff-merge-files"
DEFAULT_MERGE_CMD = MERGE_BIN + ' ' + MERGE_EVAL + ' \'(' + MERGE_EVALFUNC + ' %s %s'  + ')\''
DEFAULT_DIFF_CMD = 'diff %s %s'

class Oxit():
    def __init__(self, oxit_conf, oxit_repo, oxit_home, debug):
        self.debug = debug
        self.repo = oxit_repo 
        self.home = oxit_home
        self._conf = oxit_conf
        self.dbx = None
        
    def _debug(self, s):
        if self.debug:
            print(s)# xxx stderr?
            
    def _download_data(self, md_l, src, dest, nrevs):
        # Save log info
        #log_path = dest_base + OXITSEP2 + 'log'
        log_path = self._get_pname_logpath(src)
        if os.path.isfile(log_path):
            os.remove(log_path)

        make_sure_path_exists(os.path.dirname(log_path))
        logf = open(os.path.expanduser(log_path), "wb")
        for md in md_l:
            #print '\t%s  %s  %s' % (md.server_modified, md.rev, md.size)
            rev = md.rev
            #dest_data = dest_base + OXITSEP1 + rev
            dest_data = self._get_pname_by_rev(src, rev)
            self._debug('_download_data: dest_data %s' % dest_data)
            self.dbx.files_download_to_file(dest_data, src, rev)

            # Save file's metadata
            #dest_md = dest + OXITSEP2 + 'md'
            #dest_md = _get_pname_mdpath(src)
            #print '\t%s' % to_path_md
            #dest_file_md = open(os.path.expanduser(dest_md), "wb")
            # t = md.server_modified
            # md_d = dict([('rev', md.rev),
            #              ('server_modified', t.strftime('%m/%d/%Y %H:%M:%S')),
            #              ('size', md.size)])
            # json.dump(md_d, open(dest_md, 'w'))

            # Log entry "xOXITSEP1yOXITSEP1z".split (OXITSEP1)
            logf.write('%s%s%s%s%s\n' % (rev,
                                                   OXITSEP1,
                                                   md.server_modified,
                                                   OXITSEP1,
                                                   md.size))
        logf.close()

    def _get_revs(self, path, nrevs=10):
        print("Finding available revisions on Dropbox...")
        revisions = sorted(self.dbx.files_list_revisions(path, limit=nrevs).entries,
                           key=lambda entry: entry.server_modified, reverse=True)
        return revisions #aka meta data

    ### get_pname mini api start
    ###

    def _get_pname_index(self):
        return  self._get_pname_home_base()  + '/' + OXITINDEX

    def _get_pname_index_path(self, path):
        return  self._get_pname_index() + '/' + path

    def _get_pname_wt_path(self, path): #returns file path
        return self._get_pname_repo_base() + '/' + path
 
    def _get_pname_repo_base(self):
        return self.repo

    def _get_pname_by_rev(self, path, rev='head'):
        if rev == 'head':
            logs = self._get_log(path)
            h = logs[0]
            (rev, date, size) = h.split(OXITSEP1)
        elif rev == 'headminus1':
            logs = self._get_log(path)
            if len(logs) == 1:
                sys.exit('error:  only one rev so far so no headminus1')
            h = logs[1]
            (rev, date, size) = h.split(OXITSEP1)
  
        self._debug('by_rev: rev=%s' % rev)
        pn_revdir = self._get_pname_home_revsdir(path)
        make_sure_path_exists(pn_revdir)
        return  pn_revdir + '/' + rev 

    def _get_pname_logpath(self, path):
        return self._get_pname_home_revsdir(path) + '/' + 'log'
    
    def _get_pname_mmpath(self): #home metameta file path
        mm_path = self._get_pname_home_base() + '/.' + OXITSEP1 + OXITMETAMETA
        return os.path.expanduser(mm_path)

    def _get_pname_home_revsdir(self, path):
        #self._debug('revsdir: path %s.' % path)
        base_path = self._get_pname_home_base()
        path_dir = os.path.dirname(path)
        path_f = os.path.basename(path)
        return base_path + '/' + path_dir + '/.oxit' + OXITSEP1 + path_f # home pn v1

    def _get_pname_home_base(self): # see what u did there
        return self.repo + '/' + self.home

    ### get_pname api end

    
    def checkout(self, src, headmd):
        #  "Checkout" current file aka cf
        dest = self.repo
        wt_dir = os.path.dirname(self._get_pname_wt_path(src))
        make_sure_path_exists(wt_dir)
        wtf = open(self._get_pname_wt_path(src), "w")
        head_path = self._get_pname_by_rev(src, headmd.rev)
        headf = open(os.path.expanduser(head_path), "r")
        wtf.write(headf.read())
        wtf.close()
        headf.close()

    def _get_conf(self, key):
        path = os.path.expanduser(self._conf)
        if not os.path.isfile(path):
            sys.exit('error: conf file not found: %s' % self._conf)
        cf = ConfigParser.RawConfigParser()
        cf.read(path)
        return cf.get('misc', key)
    
    def clone(self, dry_run, src, nrevs):
        # src is a file
        # dest is a dir
        dest = self.repo
        self._debug('debug clone: %s %s' % (src, dest))

        token =  self._get_conf('auth_token')
        if not token:
            sys.exit("ERROR: auth_token not in ur oxit conf file")            
        self.dbx = dropbox.Dropbox(token)
        try:
            self.dbx.users_get_current_account()
            self._debug('debug clone auth ok')
        except AuthError as err:
            sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

        if dry_run:
            print('dry-run: repo = %s' % self.repo)
            print('dry-run: home = %s' % self.home)
            return

        self.init()

        # Src should-not-must be a dropbox url for chrimony sakes
        src_base = src.lower() #XXX dbx case insensitive
        #self.dropbox_url = src_base
        if src_base.startswith('dropbox://'):
            src_base = src_base[len('dropbox:/'):]  # keep single leading slash
        if not src_base.startswith('/') or src_base.endswith('/'):
            sys.exit('error: URL must have leading slash and no trailing slash\n')

        # Get all revs' metadata
        md_l = self._get_revs(src_base, nrevs)
        dest_base = self._get_pname_home_base() + src_base
        dest_base_dir = os.path.dirname(os.path.expanduser(dest_base))
        make_sure_path_exists(dest_base_dir)

        # Save meta meta
        mmf = open(self._get_pname_mmpath(), "a")
        #self._debug('debug: clone late %s %s'% (mm_path, src))
        mmf.write('remote_origin=%s\n' % src)
        mmf.close()

        # Cleanup prev clone
        # index_path = OXITPREDIR + OXITDIR + '/' + OXITSEP2 + 'index'
        # if os.path.isfile(index_path):
        #     os.remove(index_path)

        #self._download_data(md_l, src_base, dest, dest_base)
        self._download_data(md_l, src_base, dest, nrevs)
        self.checkout(src_base, md_l[0])        

    def _add_one_path(self, path):
        # cp file from working tree to index tree dir
        #base_path = self.repo
        #index_path = base_path + '/' + self.home + '/' + OXITINDEX
        index_path = self._get_pname_index()
        #index = index_path # isdir
        dp = os.path.dirname(path)
        if dp:
            index_path = index_path + '/' + dp
        #wt = base_path + '/' + path # is file
        wt = self._get_pname_wt_path(path)
        self._debug('debug _add_one_path cp %s %s' % (wt, index_path))
        make_sure_path_exists(index_path)
        os.system('cp %s %s' % (wt, index_path))
    
    def add(self, path):
        # cp file from working tree to index tree
        self._debug('debug: start add: %s' % path)
        paths = self._get_paths(path)
        for p in paths:
            self._add_one_path(p)

    def _reset_one_path(self, path):
        ind_path = self._get_pname_index() + '/' + path        
        if not os.path.isfile(ind_path):
            sys.exit('error: path does not exist in index (staging area): %s' % path)
        os.unlink(ind_path)
        
    def reset(self, path):
        self._debug('debug: start reset: %s' % path)
        if path:
            self._reset_one_path(path)
            return
        paths = self._get_index_paths()
        for p in paths:
            self._reset_one_path(p)

    def _get_wt_paths(self):
        wt_dir = self._get_pname_repo_base()
        self._debug('debug: _get_wt_paths: %s' % wt_dir)
        return get_relpaths_recurse(wt_dir)
    
    def status(self, path):
        # status take2 - more git like #amirite
        if path:
            if not os.path.isfile(self._get_pname_wt_path(path)):
                sys.exit('error: file name not found in repo wt -- spelled correctly?')
            paths = [path]
        else:
            paths = self._get_wt_paths()

        ipaths = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), paths)
        if not ipaths:
            print('warning: wt empty')

        self._debug('debug status2 %s' % ipaths)
        # changes staged but not pushed
        print('Changes to be pushed:')
        for p in ipaths:
            self._debug('debug status2 p=%s' % p)
            modded = False
            #p_wt = self._get_pname_wt_path(p)
            #p_wt = None if not os.path.isile(p) else p_wt
            p_ind = self._get_pname_index_path(p)
            p_ind = None if not os.path.isfile(p_ind) else p_ind
            p_head = self._get_pname_by_rev(p)
            p_head = None if not os.path.isfile(p_head) else p_head
            if p_ind and p_head:
                modded = not filecmp.cmp(p_ind, p_head)
            if modded:
                print('\tmodified: %s' % p)
                 
        # changes not staged
        ipaths = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), paths)
        print('\nChanges not staged:')
        for p in ipaths:
            self._debug('debug status2 p=%s' % p)
            modded = False
            p_wt = self._get_pname_wt_path(p)
            p_wt = None if not os.path.isfile(p_wt) else p_wt
            p_ind = self._get_pname_index_path(p)
            p_ind = None if not os.path.isfile(p_ind) else p_ind
            p_head = self._get_pname_by_rev(p)
            p_head = None if not os.path.isfile(p_head) else p_head
            if not p_wt:
                print('warning: file does not exist in wt: %s' % p)
            elif p_ind:
                modded = not filecmp.cmp(p_wt, p_ind)
            else:
                modded = not filecmp.cmp(p_wt, p_head)
            if modded:
                print('\tmodified: %s' % p)
                
    def _get_paths(self, path):
        #todo: recurse wt --> list
        return [path]
    
    def _get_diff_pair(self, reva, revb, path):
        def wd_or_index(rev, p):
            if rev == 'wd':
                return self._get_pname_wt_path(p)
            if rev == 'index':
                return self._get_pname_index_path(p)
            return None
            
        ap = wd_or_index(reva, path)
        bp = wd_or_index(revb, path)
        ap = ap if ap else self._get_pname_by_rev(path, reva)
        bp = bp if bp else self._get_pname_by_rev(path, revb)
        return ap, bp
        
    def _diff_one_path(self, diff_cmd, reva, revb,  path):
        (fa, fb) = self._get_diff_pair(reva.lower(), revb.lower(), path)
        diff_cmd = diff_cmd if diff_cmd else DEFAULT_DIFF_CMD
        self._debug('debug _diff2_one_path: %s' % diff_cmd)
        shcmd = diff_cmd % (fa, fb)
        self._debug('debug _diff2_one_path: %s' % shcmd)
        os.system(shcmd)

    def diff(self, diff_cmd, reva, revb, path):
        # diff take 2 - less clunky ui and lesss buggy to boot $diety willing
        self._debug('debug2: start diff: %s %s %s' % (reva, revb, path))
        if reva == revb:
            sys.exit('error: reva and revb the same yo diggity just no')

        if path:
            if not os.path.isfile(self._get_pname_wt_path(path)):
                sys.exit('error: file name not found in repo working dir -- spelled correctly?')
            paths = [path]
        else:
            paths = self._get_wt_paths()

        ipaths = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), paths)
        if not ipaths:
            print('warning: wt empty')
        for p in ipaths:
            self._debug('debug diff2 p=%s' % p)
            self._diff_one_path(diff_cmd, reva, revb, path)
        
    def merge(self, emacsclient_path, merge_cmd,  rev_diff_type,  path, reva, revb):
        qs = lambda(s): '\"' + s + '\"'
        (fa, fb) = self._change(rev_diff_type, path, reva, revb)
        if merge_cmd:
            shcmd = merge_cmd % (qs(fa), qs(fb)) # quotes cant hurt, eh?
        elif emacsclient_path:
            m_cmd = emacsclient_path + '/' + DEFAULT_MERGE_CMD
            shcmd = m_cmd % (qs(fa), qs(fb))
        else:
            shcmd = DEFAULT_MERGE_CMD % (qs(fa), qs(fb))
        self._debug('debug merge: %s ' % shcmd)
        os.system(shcmd)

    def _change(self, rev_diff_type,  path, reva, revb):
        # Changes  made
        #   a) wt  v index
        #   b) index v head
        #   c) wt v head
        #   d) head-headminus1
        #   e) reva v revb
        self._debug('_change %s %s %s %s' % (rev_diff_type, path, reva, revb))
        # base_path = self.repo + '/' + self.home + '/' + path
        # fa = wt_path = self.repo + '/' + path
        # ind_path = self.repo + '/' + self.home + '/' + OXITINDEX + '/' + path

        base_path = self._get_pname_home_base() + '/' + path
        fa = wt_path = self._get_pname_wt_path(path)
        ind_path = self._get_pname_index() + '/' + path        
        fb = head_path =  self._get_pname_by_rev(path, 'head')
        
        if rev_diff_type == 'wt-index':
            fb = ind_path
        elif rev_diff_type == 'wt-head':
            pass
        elif rev_diff_type == 'index-head':
            fa = ind_path
        elif rev_diff_type == 'head-headminus1':
            fa = head1_path = self._get_pname_by_rev(path, 'headminus1')
        elif rev_diff_type == 'reva-revb':
            if not reva or not revb:
                print('error: need reva and revb')
                sys.exit(2)
            fa = self._get_pname_by_rev(path, reva)
            fb = self._get_pname_by_rev(path, revb)
        else:
            print('error: _change() help me jesus aka guido!!')
            sys.exit(99)
        return fa, fb
            
    def init(self):
        base_path = self._get_pname_home_base()
        if os.path.isdir(base_path):
            print('error: %s dir exists. Pls mv or rm.' % base_path)
            exit(1)
        if os.path.isfile(base_path):
            print('error: %s file exists. Pls mv or rm.' % base_path)
            exit(1)

        make_sure_path_exists(base_path)
        mm_path = self._get_pname_mmpath()
        mmf = open(os.path.expanduser(mm_path), "w")
        mmf.write('[misc]\n')
        mmf.write('version=%s\n' % __version__)
        mmf.write('home_version=%s\n' % OXITDIRVERSION)
        mmf.write('repo_local=%s\n' % self.repo)
        mmf.close()

    def _get_log(self, path):
        self._debug('debug oxit.log start')
        # on disk '$fileOXITSEP2log':
        #   $rev||$date||$size
        log_path = self._get_pname_logpath(path)
        self._debug('debug get_log %s' % log_path)
        try:
            with open(log_path) as f:  
                content = f.readlines()
        except IOError as err:
            sys.exit('error: log file not found - clone complete ok?')
        return content

    def _log_one_path(self, path):
        # on disk '$fileOXITSEP2log':
        #   $rev||$date||$size
        logs = self._get_log(path)
        for l in logs:
            (rev, date, size) = l.split(OXITSEP1)
            print '%s\t%s\t%s' % (rev, date, size), #trailn comma ftw!

    def log(self, path):
        self._debug('debug: start log: %s' % path)
        paths = self._get_paths(path)
        l = len(paths)
        for p in paths:
            if l > 1:
                print('%s:' % p)
            self._log_one_path(p)
            if l > 1:
                print()

    def _push_one_path(self, path):
        # Push a given path upstream
        rem_path = '/' + path
        index_dir = self._get_pname_index()
        local_path = index_path = index_dir + '/' + path

        # Skip if no change from current rev
        logs = self._get_log(path)
        head = logs[0] # currrent rev
        (rev, date, size) = head.split(OXITSEP1)
        head_path = self._get_pname_by_rev(path, rev)# 'rev='head?
        if filecmp.cmp(index_path, head_path):
            print('%s: no change ... skipping ...' % path)
            return

        with open(local_path, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            print("Uploading " + local_path + " to Dropbox as " + rem_path + " ...")
            try:
                self.dbx.files_upload(f, rem_path, mode=WriteMode('overwrite'))
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
        os.remove(index_path)
        
    def _get_index_paths(self):
        index_dir = self._get_pname_index()
        return get_relpaths_recurse(index_dir)

    def push(self, dry_run, post_push_clone, path):
        # Push path or all staged paths upstream
        paths = self._get_index_paths()
        self._debug('debug push: %s' % paths)
        if post_push_clone:
                    self._debug('debug post_push_clone true')

        token =  self._get_conf('auth_token')
        if not token:
            sys.exit("ERROR: auth_token not in ur oxit conf file brah")            
        self.dbx = dropbox.Dropbox(token)
        try:
            self.dbx.users_get_current_account()
            self._debug('debug push auth ok')
        except AuthError as err:
            sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

        if path:
            if path not in [s.strip('./') for s in paths]:
                sys.exit('push %s not in index' % path)
            if dry_run:
                print('push dryrun: %s' % path)
            else:
                self._push_one_path(path)
        else:
            if not paths:
                print('Nothing to push')
                return
            for p in paths:
                if dry_run:
                    print('push dryrun: %s' % p)
                else:
                    self._push_one_path(p)

        dropbox_url = self._get_mmval('remote_origin')
        if dropbox_url  and post_push_clone: #need to read url from metameta dummy
            home = self._get_pname_home_base()
            destold = home + '.old.' + '%s' % random.randint(1, 99)
            print('Mving/saving current repo home %s to %s ...' % (home, destold))
            os.system('mv %s %s' % (home, destold))
            print('Re-cloning to get current meta data/data from Dropbox...')
            self.clone(dry_run, dropbox_url, 10)

    def _get_mmval(self, key):
        mm_path = self._get_pname_mmpath()
        if not os.path.isfile(mm_path):
            sys.exit('error: metameta file not found. oxit clone creates it.')
        mm = ConfigParser.RawConfigParser()
        mm.read(mm_path)
        if key:
            return mm.get('misc', key)
        else:
            return mm.items('misc')
        
    def getmm(self, key):
        if key:
            print('%s=%s' % (key, self._get_mmval(key)))
        else:
            print(self._get_mmval(key))
