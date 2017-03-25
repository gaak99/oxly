"""Utils for oxit"""

import os
import pytz
from datetime import datetime
from tzlocal import get_localzone

def make_sure_path_exists(path):
    import errno
    try:
        os.makedirs(path)  
    except OSError as exception:  
        if exception.errno != errno.EEXIST:  
            raise  

# from StOflw
def get_relpaths_recurse(rootDir):
    fileSet = set()
    for dir_, _, files in os.walk(rootDir):
        for fileName in files:
            relDir = os.path.relpath(dir_, rootDir)
            relFile = os.path.join(relDir, fileName)
            fileSet.add(relFile)
    return fileSet

def utc_to_localtz(dt_str):
    """Given a date/time string in Dropbox utc format
       return date/time string in local timezone
    """
    local_tz = get_localzone()
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    dt_utc = dt.replace(tzinfo=pytz.timezone('UTC'))
    dt_local = dt_utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z%z")

#from __future__ import absolute_import, division, print_function, unicode_literals
from dropbox_content_hasher import DropboxContentHasher

def calc_dropbox_content_hash(fname):
    hasher = DropboxContentHasher()
    with open(fname, 'rb') as f:
        while True:
            chunk = f.read(1024)  # or whatever chunk size you want
            if len(chunk) == 0:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
