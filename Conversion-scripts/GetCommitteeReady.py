#!/usr/bin/env python3

# outline of script task
""" This script is designed to combine the outputs of an I-PI/Lammps N2P2 simulation and allow me to place them into 
a single datafile that I can then split and run committee prediction on as required. To ensure that this is done in the
smartest way possible, I'm going to outline the criteria for inclusion as the following...
1. Any frame that has EW > 5 are being placed into the datafile, particularly as the potential seems to mainly baseline
most of the frames as being entirely represented. 
2. Random selection procedure occurs after this from the remaining frames, I hope to gather about 10% of all the remaining frames.

Overall then, I'm sampling N frames and removing the EW frames, so sampling 1% of N-x frames.

To acheive this, the script outlines a number of parsers in function form, that will parse the necessary line given a requisite frame
number. 
"""

# import the modules needed to complete this task
import os, sys
import numpy as np
from ase.io import read, write
from ase.geometry import Cell
import random 
import argparse
import subprocess

# define command line arguments to make easier writing
parser = argparse.ArgumentParser(description='Combines multiple output files into N2P2 workable ones')
parser.add_argument('-e', type=str, help='The ensemble this simulation was run in', metavar='--ensemble', choices=['NVT', 'NST', 'NPT', 'NVE'], required=True)
parser.add_argument('-w', type=bool, help='Ignore all extrapolation warning frames and sample as complete set', metavar='--warnings', default=False, required=False)
parser.add_argument('-f', type=str, help='File extensions used within I-PI', metavar='--file_extension', required=False)
parser.add_argument('-t', type=int, help='Threshold for extrapolation warning inclusion', metavar='--threshold', required=False, default=5)
parser.add_argument('-s', type=bool, help='Automatic random sampling of extrapolative frames', metavar='--shuffle', required=False, default=True)

# Define function to convert xyz file to readible string
def Frame2Lines(frame, filename):
    flname = f'{filename}.pos_0.xyz'
    start_line = (frame*274)+1
    end_line = (frame+1)*274
    cmd = f'sed -n {start_line},{end_line}p {flname}'
    oframe = subprocess.run(cmd.split(), capture_output=True)
    return oframe.stdout.decode('utf-8')
        

def Lines2XYZ(output, handle):
    lines = output.splitlines()
    for line in lines:
        if '# CELL' in line:
            cellpar = [float(x) for x in line.split()[2:8]]
            cell = Cell.fromcellpar(cellpar)
            newLine = f'Lattice="{cell[0][0]} {cell[0][1]} {cell[0][2]} {cell[1][0]} {cell[1][1]} {cell[1][2]} {cell[2][0]} {cell[2][1]} {cell[2][2]}" Properties=species:S:1:pos:R:3\n'
            handle.writelines(newLine)
        elif len(line.split()) == 1:
            handle.writelines(f'{line}\n')
        else:
            oline = line.split()
            fline = f"{oline[0]}\t{oline[1]}\t{oline[2]}\t{oline[3]}\n"
            handle.writelines(fline)

# Define function to get all frames with extrapolation warnings
def get_EW_frames(Lammpsfile, threshold):
    with open(Lammpsfile, 'r') as handle:
        data = handle.readlines()
    EW_dict = {}
    for line in data:
        if 'EW' in line:
            frame = line.split()[6]
            numWarnings = int(line.split()[8])
            if numWarnings >= threshold:
                EW_dict[f'frame {frame}'] = numWarnings
    return EW_dict 
    
# Execute programme
if __name__ == '__main__':

    # Read the parser
    args = parser.parse_args()
    threshold = args.t 
    filename = args.f
    shuffle = args.s

    # define functions to parse the required information
    
    # Get EW dictionary
    EWdict = get_EW_frames('lmp.out', threshold)
    with open('CommitteeFrames.xyz', 'w+') as handle:
        print(f"{len(EWdict)} frames to convert...\n")
        if shuffle == True:
            print('Shuffle selected...\n')
            print(f'Selecting 500 frames of the entire extrapolative dataset...\n')
            for ii in range(500):
                sampledframe = random.choice(list(EWdict.keys()))
                frameNum = int(sampledframe.split()[1])
                print(frameNum)
                frameData = Frame2Lines(frameNum, filename)
                Lines2XYZ(frameData, handle)
        else:
            for EWframe in list(EWdict.keys()):
                frameNum = int(EWframe.split()[1])
                frameData = Frame2Lines(frameNum, filename)
                Lines2XYZ(frameData, handle)
