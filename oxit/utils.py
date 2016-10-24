
import os

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
