#!/usr/bin/python3

import os,sys
import time

data_dir = '../data'

target = os.path.join(data_dir, time.strftime('%Y%m%d%H%M%S'))
prefile = os.path.join(target, 'pre.dat')
burnfile = os.path.join(target, 'burn')
postfile = os.path.join(target, 'post.dat')

# Make the target directory
os.mkdir(target)

# Prompt the user for input
go_f = True
while go_f:
    standoff_in = float(input('Standoff (in):'))
    print('Are the above entries correct?')
    go_f = not (input('(Y/n):') == 'Y')

# Run the flow measurement
print('Pre-flow measurement')
os.system('lcburst -c flow.conf -d ' + prefile)

# Run the measurement
print('Measuring...')
os.system(f'lcrun -c burn.conf -d {burnfile} -f standoff_in={standoff_in}')

# Run the flow measurement
print('Post-flow measurement')
os.system('lcburst -c flow.conf -d ' + postfile)
