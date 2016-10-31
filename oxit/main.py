
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
            try:
                self.dbx.files_download_to_file(dest_data, src, rev)
            except Exception as err:
                sys.exit('Call to Dropbox to download file data failed: %s' % err)

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
        try:
            revisions = sorted(self.dbx.files_list_revisions(path, limit=nrevs).entries,
                               key=lambda entry: entry.server_modified, reverse=True)
        except Exception as err:
            sys.exit('Call to Dropbox to list file revisions failed: %s' % err)
        return revisions #aka meta data

    ### start get_pname internal api
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

    def _get_pname_home_paths(self):
        #home all paths list file path
        path = self._get_pname_home_base() + '/.' + OXITSEP1 + 'filepaths'
        return os.path.expanduser(path)

    ### end get_pname internal api

    ### start _repohome_files internal api
    def _repohome_files_put(self, path):
        self._debug('debug _repohome_paths_put start %s' % path)
        f = open(self._get_pname_home_paths(), "a")
        f.write('%s\n' % path)
        f.close()

    def _repohome_files_get(self):
        # return list of all relative path of files in home
        self._debug('debug _repohome_paths_get start')
        p = self._get_pname_home_paths()
        try:
            with open(p) as f:  
                content = f.readlines()
        except IOError as err:
            sys.exit('internal error: repo home file of file paths not found')
        self._debug('debug _repohome_paths_get end %s' % content)
        return [x.rstrip() for x in content]
    ### end _repohome_files internal api

    def _get_fp_triple(self, fp):
        # Given an fp, return a triple wt/index/head
        # where each is a fp if it exists else None.
        wt = self._get_pname_wt_path(fp)
        wt = None if not os.path.isfile(fp) else wt
        ind = self._get_pname_index_path(fp)
        ind = None if not os.path.isfile(ind) else ind
        head = self._get_pname_by_rev(fp)
        head = None if not os.path.isfile(head) else head
        return wt, ind, head
        
    def checkout(self, filepath):
        # Revert local wt changes w/staged version if it exists,
        # else with HEAD (aka `cp HEAD wt` regardless of wt filepath).
        if filepath:
            if not os.path.isfile(self._get_pname_by_rev(filepath)):
                sys.exit('error: filepath name not found in repo home -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._repohome_files_get()

        if not fp_l:
            sys.exit('internal error: checkout2  repo home empty')

        make_sure_path_exists(self._get_pname_index())
        for p in fp_l:
            self._debug('debug checkout2 p=`%s`' % p)
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            if p_wt:
                if p_ind:
                    self._debug('debug checkout2: cp ind wt')
                    os.system('cp %s %s' % (p_ind, p_wt))
                elif p_head:
                    self._debug('debug checkout2: cp head wt')
                    os.system('cp %s %s' % (p_head, p_wt))
            else:
                    self._debug('debug checkout2 no wt: cp head wt')
                    make_sure_path_exists(os.path.dirname(self._get_pname_wt_path(p)))
                    os.system('cp %s %s' % (p_head, self._get_pname_wt_path(p)))

    def _get_conf(self, key):
        path = os.path.expanduser(self._conf)
        if not os.path.isfile(path):
            sys.exit('error: conf file not found: %s' % self._conf)
        cf = ConfigParser.RawConfigParser()
        cf.read(path)
        return cf.get('misc', key)
    
    def clone(self, dry_run, src_url, nrevs):
        # Given a dropbox url for one file (limitation at least for now),
        # fetch the nrevs of the file and store locally in repo home and
        # checkout HEAD to working dir.
        self._debug('debug clone: %s' % (src_url))

        token =  self._get_conf('auth_token')
        if not token:
            sys.exit("ERROR: auth_token not in ur oxit conf file")            
        self.dbx = dropbox.Dropbox(token)
        try:
            self.dbx.users_get_current_account()
            self._debug('debug clone auth ok')
        except dropbox.exceptions.HttpError as err:
            sys.exit('Call to Dropbox failed: http error')
        #except requests.exceptions.ConnectionError:
            #sys.exit('Call to Dropbox failed: https connection')
        except AuthError as err:
            sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
        except dropbox.exceptions.ApiError as err:
            sys.exit('Call to Dropbox failed: api error')
        except Exception as err:
            sys.exit('Call to Dropbox failed: %s' % err)

        if dry_run:
            print('dry-run: repo = %s' % self.repo)
            print('dry-run: home = %s' % self.home)
            return

        self.init()

        # src_url should-not-must be a dropbox url for chrimony sakes
        file = src_url.lower() #XXX dbx case insensitive
        #self.dropbox_url = file
        if file.startswith('dropbox://'):
            file = file[len('dropbox:/'):]  # keep single leading slash
        if not file.startswith('/') or file.endswith('/'):
            sys.exit('error: URL must have leading slash and no trailing slash')
        self._debug('debug clone: file=%s' % (file))
        
        # Get all revs' metadata
        md_l = self._get_revs(file, nrevs)
        repo_home = self._get_pname_home_base() + file
        repo_home_dir = os.path.dirname(os.path.expanduser(repo_home))
        make_sure_path_exists(repo_home_dir)

        # Save meta meta & update master file path list
        mmf = open(self._get_pname_mmpath(), "a")
        #self._debug('debug: clone late %s %s'% (mm_path, src_url))
        mmf.write('remote_origin=%s\n' % src_url)
        mmf.close()
        self._repohome_files_put(file.strip('/'))

        # Finally! download the revs data and checkout themz to wt
        self._debug('debug clone: download %d revs of %s to %s' % (nrevs, file, self.repo))
        self._download_data(md_l, file, self.repo, nrevs)
        self.checkout(file)
        print('... cloned into %s.' % self.repo)

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
    
    def add(self, filepath):
        # cp file from working tree to index tree
        self._debug('debug: start add: %s' % filepath)
        fp_l = self._get_paths(filepath)
        for p in fp_l:
            self._add_one_path(p)

    def _reset_one_path(self, path):
        ind_path = self._get_pname_index() + '/' + path        
        if not os.path.isfile(ind_path):
            sys.exit('error: path does not exist in index (staging area): %s' % path)
        os.unlink(ind_path)
        
    def reset(self, filepath):
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
    
    def status(self, filepath):
        # status take2 - more git like #amirite
        if filepath:
            if not os.path.isfile(self._get_pname_wt_path(filepath)):
                sys.exit('error: file name not found in repo wt -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._get_wt_paths()

        ifp_l = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), fp_l)
        if not ifp_l:
            print('warning: wt empty')

        self._debug('debug status2 %s' % ifp_l)
        # changes staged but not pushed
        print('Changes to be pushed:')
        for p in ifp_l:
            self._debug('debug status2 p=%s' % p)
            modded = False
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            if p_ind and p_head:
                modded = not filecmp.cmp(p_ind, p_head)
            if modded:
                print('\tmodified: %s' % p)
                 
        # changes not staged
        ifp_l = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), fp_l)
        print('\nChanges not staged:')
        for p in ifp_l:
            self._debug('debug status2 p=%s' % p)
            modded = False
            p_wt, p_ind, p_head = self._get_fp_triple(p)
            if not p_wt:
                pass
                #damned if ya do
                #print('warning: file does not exist in wt: %s' % p)
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

    def diff(self, diff_cmd, reva, revb, filepath):
        # diff take 2 - less clunky ui and lesss buggy to boot $diety willing
        self._debug('debug2: start diff: %s %s %s' % (reva, revb, filepath))
        if reva == revb:
            sys.exit('error: reva and revb the same yo diggity just no')

        if filepath:
            if not os.path.isfile(self._get_pname_wt_path(filepath)):
                sys.exit('error: file name not found in repo working dir -- spelled correctly?')
            fp_l = [filepath]
        else:
            fp_l = self._get_wt_paths()

        ifp_l = itertools.ifilterfalse(lambda x: x.startswith('.oxit'), fp_l)
        if not ifp_l:
            print('warning: wt empty')
        for p in ifp_l:
            self._debug('debug diff2 p=%s' % p)
            self._diff_one_path(diff_cmd, reva, revb, p)

    def merge(self, emacsclient_path, merge_cmd, reva, revb, filepath):
        qs = lambda(s): '\"' + s + '\"'
        (fa, fb) = self._get_diff_pair(reva.lower(), revb.lower(), filepath)
        if merge_cmd:
            shcmd = merge_cmd % (qs(fa), qs(fb)) # quotes cant hurt, eh?
        elif emacsclient_path:
            m_cmd = emacsclient_path + '/' + DEFAULT_MERGE_CMD
            shcmd = m_cmd % (qs(fa), qs(fb))
        else:
            shcmd = DEFAULT_MERGE_CMD % (qs(fa), qs(fb))
        self._debug('debug merge: %s ' % shcmd)
        os.system(shcmd)

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
        self._debug('debug _get_log start %s' % path)
        # on disk '$fileOXITSEP2log':
        #   $rev||$date||$size
        log_path = self._get_pname_logpath(path)
        self._debug('debug _get_log `%s`' % log_path)
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

    def log(self, filepath):
        self._debug('debug: start log: %s' % filepath)
        fp_l = self._get_paths(filepath)
        l = len(fp_l)
        for p in fp_l:
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

    def push(self, dry_run, post_push_clone, filepath):
        # Push filepath or all staged filepaths upstream
        fp_l = self._get_index_paths()
        self._debug('debug push: %s' % fp_l)
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
        except Exception as e:
            sys.exit("ERROR: push call to Dropbox fail: %s" % e)
            
        if filepath:
            if filepath not in [s.strip('./') for s in fp_l]:
                sys.exit('push %s not in index' % filepath)
            if dry_run:
                print('push dryrun: %s' % filepath)
            else:
                self._push_one_path(filepath)
        else:
            if not fp_l:
                print('Nothing to push')
                return
            for p in fp_l:
                if dry_run:
                    print('push dryrun: %s' % p)
                else:
                    self._push_one_path(p)

        if dry_run:
            return

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
