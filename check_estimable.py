from os.path import join as pjoin
import os
import sys
# import glob as gb
# import shutil as sh
import nibabel as nib
import fnmatch
import re
from tempfile import mkdtemp
#----
# Define the default size of the image
IMG_FILE_SIZE =  614728
PAT = r'(.*)(\d{12})(.*)' # pattern to match a PSC in a filename (with path)

#------------------------------------------------------------------------------#
# deal - badly - with the onlines arguments
#------------------------------------------------------------------------------#
def usage(msg):
    print('\n Usage: "python check_estimable.py in_dir out_dir [*.nii] " %s'
          % msg)
    print('\n in_dir : a directory that contains all the contrast images')
    print(' (contrasts can be in several sub-directories)')
    print('\n out_dir : a directory that contains the resulting txt files \n')
    quit()

if len(sys.argv) < 2:
    usage(' ')

# get directory - check it exists
basedir = sys.argv[1]
if not os.path.exists(basedir):
    msg = 'directory %s does not exist' % basedir
    usage(msg)

# if a second argument is provided:
if len(sys.argv) > 2:
    savedir = sys.argv[2]
    if not os.path.exists(savedir):
        usage(str('save directory %s doesnt exist' % savedir))
else:
    savedir = mkdtemp()

# if a third argument is provided:
if len(sys.argv) > 3:
    PSC = sys.argv[3]
else:
    PSC = '*.nii'

print('searching %s images in directory %s ' % (PSC,basedir))

#------------------------------------------------------------------------------#
# find files with a given pattern
def find_files(directory, pattern):
    """find files in directory and subdirectory with a given pattern

    Parameters
    ----------
    directory: string
        The directory where to find files recursively

    Returns
    -------
    pattern: string
        A pattern to match

    Examples
    --------
        find_files('/home/user/code','*.py')
    """
    for root, dirs, files in os.walk(directory):
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = pjoin(root, base_name)
                yield filename

class LoadImgError(Exception):
    """ exception if load image fails """

#------------------------------------------------------------------------------#
def find_files_with_string_header(lfiles, searchstring='unestimable',
                                  pscpatt = PAT):
    """ Find the files with the string in the header

    Parameters
    ----------
    lfiles: list
        list of files names

    searchstring : str
        the string to search in the header

    Returns
    -------
    dictionary, list_with_string: list
        lists of filenames

    """
    fdic = {    'all': [],
                'psc': [],
                'bad_psc': [],
                'too_small': [],
                'cannot_load': [],
                'nonestim': [],
                'estim': []
           }

    r = re.compile(pscpatt)

    for filename in lfiles:

        fdic['all'].append(filename)

        # check if filename has a PSC
        #-----------------------------------------------------------------
        m = r.match(filename)
        if m:
            fdic['psc'].append(m.groups()[1])
        else:
            fdic['bad_psc'].append(filename)
            continue

        # check if filename has a reasonable size
        #-----------------------------------------------------------------
        if os.lstat(filename).st_size < IMG_FILE_SIZE:
            fdic['too_small'].append(filename)
            continue

        # check if filename can be loaded by nibabel and header readable
        #-----------------------------------------------------------------
        try:
            img = nib.load(filename)
        except:
            print('Nibabel Could not load file : %s ' % filename)
            fdic['cannot_load'].append(filename)
            continue

        try:
            imghdr = img.get_header()
        except:
            print('Nibabel Could not get header of file : %s ' % filename)
            fdic['cannot_load'].append(filename)
            continue

        # check if the filename has string ("unestimable") in the descrip
        #-----------------------------------------------------------------
        if imghdr['descrip'].tostring().find(searchstring) >= 0:
            print(imghdr['descrip'].tostring())
            print('%s',filename)
            fdic['nonestim'].append(filename)
        else:
            fdic['estim'].append(filename)

    return(fdic)

#------------------------------------------------------------------------------#
# save the txt files in savedir, use basedir to provide a name
def save_results(savedir, basedir, lfiles, suffix):
    fname = (basedir[1:] + suffix).replace(os.path.sep,'_')
    fid = open(pjoin(savedir,fname), 'w')
    fid.writelines("%s\n" % item for item in lfiles)
    fid.close()
    print('Saved text files: \n\t%s\n in directory %s\n' % (fname, savedir))

#------------------------------------------------------------------------------#
# do it:
#------------------------------------------------------------------------------#

# print(' find the files ...')
lfiles = find_files(basedir, PSC)
# print('find those that are not estimable')
res = find_files_with_string_header(lfiles)

for k in res:
    if res[k]: # not empty
        print('number of %s is : %d' % (k,len(res[k])))
        save_results(savedir, basedir, res[k], '_' + k + '.txt')

#------------------------------------------------------------------------------#
