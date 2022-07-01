#!/usr/bin/python3

import numpy as np
import lconfig as lc
import matplotlib.pyplot as plt
import os,sys
from multiprocessing import Pool

def worker(target):
    print(target)
    os.system(f'./post1.py quiet force {target}')

#
# These are lines of code you may want to edit before running post.py
#
datadir = '../data'
####

# The early data are scanned one block at a time to identify the first 
# block where preheating had begun.  This is used to identify the 
# standoff offset height.


force = 'force' in sys.argv[1:]
quiet = 'quiet' in sys.argv[1:]
arg = sys.argv[-1]
sourcedir = None

if arg == 'all':
    contents = os.listdir(datadir)
    contents.sort()
    with Pool(processes=8) as pool:
       pool.map(worker, contents) 
    exit(0)

for this in os.listdir(datadir):
    if this.endswith(arg):
        if sourcedir:
            raise Exception(f'POST1.PY: found multiple data entries that end with {arg}')
        sourcedir = os.path.join(datadir,this)
        
if not quiet: 
    print('Working on: ' + sourcedir)


source = os.path.join(sourcedir,'burn.dat')

# Check for prior post1 results
# Make the post1 directory if it doesn't already exist
targetdir = os.path.join(sourcedir, 'post1')
if os.path.isdir(targetdir):
    if not force and 'y' != input('Overwrite previous post1 results? (y/n):'):
        raise Exception('Disallowed from overwriting prior post1 results')
    os.system(f'rm -rf {targetdir}')
os.mkdir(targetdir)

# LOAD DATA!
data = lc.LConf(source, data=True, cal=True)

# Get channels
voltage = data.get_channel(1)
current = data.get_channel(0)
t = data.get_time()

