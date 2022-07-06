#!/usr/bin/python3

import numpy as np
import json
import lconfig as lc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os,sys,shutil
from multiprocessing import Pool

def worker(args):
    sourcedir, force, quiet = args
    if not quiet:
        print('Working on :' + sourcedir)
        
    vtest = 2.0
    itest = 25.0
    
    # Check for prior post1 results
    # Make the post1 directory if it doesn't already exist
    targetdir = os.path.join(sourcedir, 'post1')
    if os.path.isdir(targetdir):
        if not force and 'y':
            raise Exception(f'Disallowed from overwriting {targetdir}. Use "force" to override.')
        shutil.rmtree(targetdir)
    os.mkdir(targetdir)

    prefile = os.path.join(sourcedir, 'pre.dat')
    postfile = os.path.join(sourcedir, 'post.dat')
    burnfile = os.path.join(sourcedir, 'burn.dat')
    
    # Initialize an output dictionary for easy JSON dumping
    out = {}
    
    conf,data = lc.load(prefile, data=True, cal=True)
    out['fg_pre_scfh'] = np.mean(data.get_channel('Fuel Gas'))
    out['o2_pre_scfh'] = np.mean(data.get_channel('Oxygen'))
    out['fo_pre_ratio'] = out['fg_pre_scfh'] / out['o2_pre_scfh']
    out['flow_pre_scfh'] = out['fg_pre_scfh'] + out['o2_pre_scfh']

    conf,data = lc.load(postfile, data=True, cal=True)
    out['fg_post_scfh'] = np.mean(data.get_channel('Fuel Gas'))
    out['o2_post_scfh'] = np.mean(data.get_channel('Oxygen'))
    out['fo_post_ratio'] = out['fg_post_scfh'] / out['o2_post_scfh']
    out['flow_post_scfh'] = out['fg_post_scfh'] + out['o2_post_scfh']
    
    # Calculate mean values
    out['fg_scfh'] = 0.5*(out['fg_pre_scfh'] + out['fg_post_scfh'])
    out['o2_scfh'] = 0.5*(out['o2_pre_scfh'] + out['o2_post_scfh'])
    out['fo_ratio'] = out['fg_scfh'] / out['o2_scfh']
    out['flow_scfh'] = out['fg_scfh'] + out['o2_scfh']
    
    # Load the burn data
    conf,data = lc.load(burnfile, data=True, cal=True)
    
    # Grab the meta data
    out['standoff_in'] = conf.get_meta('standoff_in')
    out['fuel'] = 'CH4'
    
    # OK, we're ready to write the meta data file
    with open(os.path.join(targetdir, 'conditions.json'), 'w') as ff:
        json.dump(out, ff, indent=2)
        
    vv = data.get_channel('Voltage')
    ii = data.get_channel('Current')
    tt = data.time()
    
    # Let's make an animation of the IV characteristic
    # The FPS will be the same as the actual analog output frequency
    fps = conf.aoch[0].aofrequency
    samples_per_frame = int(conf.samplehz / fps)
    frames = int(data.ndata() / samples_per_frame)
    
    f = plt.figure(1)
    f.clf()
    ax = f.subplots(1,1)
    ax.set_xlabel('Voltage (V)')
    ax.set_ylabel('Current (uA)')
    ax.set_ylim([-100., 250.])
    ax.set_xlim([-10., 10.])
    ax.axvline(vtest,0,1, color='r')
    ax.axhline(itest,0,1, color='r')
    ax.grid('on')
    
    def update(index, ax, line):
        start = samples_per_frame * index
        stop = samples_per_frame * (index + 1)
        line.set_data(vv[start:stop], ii[start:stop])
        ax.set_title(f'{tt[start]:.1f} seconds')
    
    line = ax.plot(vv[:samples_per_frame], ii[:samples_per_frame], '.')[0]
    #line_animation = animation.FuncAnimation(f, update, frames=frames, interval=1000./fps, fargs=(ax,line))
    line_animation = animation.FuncAnimation(f, update, frames=frames, interval=.01*1000./fps, fargs=(ax,line), repeat=False)
    #plt.show()
    line_animation.save(os.path.join(targetdir,'ivchar.mp4'), fps = fps)
    
    # Grab the vtest crossing events
    testy = []
    testx = []
    indices = data.get_events('Voltage', level=vtest)
    for index in indices:
        # interpolate
        x = (vtest - vv[index])/(vv[index+1] - vv[index])
        testy.append(x*ii[index+1] + (1-x)*ii[index])
        testx.append(x*tt[index+1] + (1-x)*tt[index])

    # Generate a plot
    f.clf()
    ax = f.subplots(1,1)
    ax.plot(testx, testy, 'k.')
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Current ($\mu$A)')
    ax.grid('on')
    ax.set_title(f'Constant Voltage {vtest}V')
    f.savefig(os.path.join(targetdir,'vtest.png'))
    # Throw it to an output file
    with open(os.path.join(targetdir, 'vtest.dat'), 'w') as ff:
        ff.write('time (sec), current (uA)\n')
        for x,y in zip(testx,testy):
            ff.write(f'{x:.3f}, {y:.2f}\n')

    # Grab the itest crossing events
    testy = []
    testx = []
    indices = data.get_events('Current', level=itest)
    for index in indices:
        # interpolate
        x = (itest - ii[index])/(ii[index+1] - ii[index])
        testy.append(x*vv[index+1] + (1-x)*vv[index])
        testx.append(x*tt[index+1] + (1-x)*tt[index])

    # Generate a plot
    f.clf()
    ax = f.subplots(1,1)
    ax.plot(testx, testy, 'k.')
    ax.set_xlabel('Time (sec)')
    ax.set_ylabel('Voltage ($\mu$A)')
    ax.grid('on')
    ax.set_title(f'Constant Current {itest}$\mu$A')
    f.savefig(os.path.join(targetdir,'itest.png'))
    # Throw it to an output file
    with open(os.path.join(targetdir, 'itest.dat'), 'w') as ff:
        ff.write('time (sec), voltage (V)\n')
        for x,y in zip(testx,testy):
            ff.write(f'{x:.3f}, {y:.2f}\n')


#
# These are lines of code you may want to edit before running post.py
#
datadir = '../data'
####

argv = sys.argv.copy()
# Always pop the executable call
argv.pop(0)
force = False
quiet = False
if 'force' in argv:
    argv.pop(argv.index('force'))
    force = True
if 'quiet' in argv:
    argv.pop(argv.index('quiet'))
    quiet = True

# If there are no datasets listed, process them all
if len(argv) == 0:
    argv = os.listdir(datadir)
    argv.sort()

worker_args = []
for index, arg in enumerate(argv):
    sourcedir = None
    for this in os.listdir(datadir):
        if this.endswith(arg):
            if sourcedir:
                raise Exception(f'POST1.PY: found multiple data entries that end with {arg}')
            sourcedir = os.path.join(datadir,this)
    worker_args.append((sourcedir, force, quiet))

#with Pool(8) as pool:
#    pool.map(worker, worker_args)

for args in worker_args:
    worker(args)
