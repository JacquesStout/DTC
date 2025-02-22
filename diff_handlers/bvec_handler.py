#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:12:00 2020

@author: JS
"""

"""
import nibabel as nib
from nibabel.streamlines import Field
from nibabel.orientations import aff2axcodes
from dipy.io.streamline import load_trk
from dipy.tracking._utils import (_mapping_to_voxel, _to_voxel_coordinates)
import pickle
import smtplib
from email.mime.text import MIMEText
from types import ModuleType, FunctionType
from gc import get_referents
"""

import numpy as np

from os.path import splitext
import warnings
from nibabel.tmpdirs import InTemporaryDirectory
import os, re, sys, io, struct, socket, datetime
from DTC.file_manager.file_tools import largerfile
import glob
from DTC.file_manager.computer_nav import make_temppath
import copy
""""
from dipy.tracking.utils import unique_rows


from time import time
from dipy.io.image import load_nifti, save_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.reconst.shm import CsaOdfModel
from dipy.data import get_sphere
from dipy.direction import peaks_from_model
from dipy.tracking.local_tracking import LocalTracking
from dipy.direction import peaks
from nibabel.streamlines import detect_format
from dipy.io.utils import (create_tractogram_header,
                           get_reference_info)
from dipy.viz import window, actor

from dipy.segment.mask import segment_from_cfa
from dipy.segment.mask import bounding_box

import multiprocessing
# We must import this explicitly, it is not imported by the top-level
# multiprocessing module.
import multiprocessing.pool



from scipy.ndimage.morphology import binary_dilation
from dipy.tracking import utils
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.streamline import Streamlines
import matplotlib.pyplot as plt

#from dipy.denoise.localpca import mppca
from diff_handlers.denoise_processes import mppca
from dipy.denoise.gibbs import gibbs_removal

from random import randint

from mpl_toolkits.axes_grid1 import AxesGrid
import matplotlib
import matplotlib.pyplot as plt
#import dipy.tracking.life as life
import JSdipy.tracking.life as life
from dipy.viz import window, actor, colormap as cmap
import dipy.core.optimize as opt
from functools import wraps

from visualization_tools.figures_handler import denoise_fig, show_bundles, window_show_test, LifEcreate_fig
from tract_manager.tract_eval import bundle_coherence, LiFEvaluation
from tract_manager.dif_to_trk import QCSA_tractmake
#from diff_handlers.diff_preprocessing import make_tensorfit
"""


def orient_to_str(bvec_orient):
    mystr="_"
    for i in np.arange(3):
        if np.abs(bvec_orient[i]) == 1:
            if bvec_orient[i]<0:
                mystr = mystr+"mx"
            else:
                mystr = mystr+"px"
        if np.abs(bvec_orient[i]) == 2:
            if bvec_orient[i] < 0:
                mystr = mystr + "my"
            else:
                mystr = mystr + "py"
        if np.abs(bvec_orient[i])==3:
            if bvec_orient[i]<0:
                mystr = mystr+"mz"
            else:
                mystr = mystr+"pz"
    return mystr


def reorient_bvecs(bvecs, bvec_orient=[1,2,3]):

    #bvals, bvecs = get_bvals_bvecs(mypath, subject)
    bvec_sign = bvec_orient/np.abs(bvec_orient)
    bvecs = np.c_[bvec_sign[0]*bvecs[:, np.abs(bvec_orient[0])-1], bvec_sign[1]*bvecs[:, np.abs(bvec_orient[1])-1],
                  bvec_sign[2]*bvecs[:, np.abs(bvec_orient[2])-1]]
    return bvecs

def read_bvals(fbvals,fbvecs, sftp = None):

    vals=[]
    if sftp is not None:
        temp_path_bval = f'{os.path.join(os.path.expanduser("~"), os.path.basename(fbvals))}'
        temp_path_bvec = f'{os.path.join(os.path.expanduser("~"), os.path.basename(fbvecs))}'
        sftp.get(fbvals, temp_path_bval)
        sftp.get(fbvecs, temp_path_bvec)
        fbvals = temp_path_bval
        fbvecs = temp_path_bvec

    for this_fname in [fbvals, fbvecs]:
        # If the input was None or empty string, we don't read anything and
        # move on:
        if this_fname is None or not this_fname:
            vals.append(None)
        else:
            if isinstance(this_fname, str):
                base, ext = splitext(this_fname)
                if ext in ['.bvals', '.bval', '.bvecs', '.bvec', '.txt', '.eddy_rotated_bvecs', '']:
                    with open(this_fname, 'r') as f:
                        content = f.read()
                    # We replace coma and tab delimiter by space
                    with InTemporaryDirectory():
                        tmp_fname = "tmp_bvals_bvecs.txt"
                        with open(tmp_fname, 'w') as f:
                            f.write(re.sub(r'(\t|,)', ' ', content))
                        vals.append(np.squeeze(np.loadtxt(tmp_fname)))
                elif ext == '.npy':
                    vals.append(np.squeeze(np.load(this_fname)))
                else:
                    e_s = "File type %s is not recognized" % ext
                    raise ValueError(e_s)
            else:
                raise ValueError('String with full path to file is required')

    if sftp is not None:
        os.remove(fbvals)
        os.remove(fbvecs)
    # Once out of the loop, unpack them:
    bvals, bvecs = vals[0], vals[1]
    return bvals, bvecs


def cut_bvals_bvecs(fbvals, fbvecs, tocut, format="classic"):

    bvals, bvecs = read_bvals(fbvals, fbvecs)
    bvals_new = np.zeros(np.shape(bvals))
    for i in range(np.shape(bvals)[0]):
        if i in tocut:
            bvals_new[i] = -500
        else:
            bvals_new[i] = bvals[i]
    fbvals_new = fbvals.replace("bvals.txt","bvals_cut.txt")
    if format == "classic":
        np.savetxt(fbvals_new, bvals_new)
    if format=="dsi":
        with open(fbvals_new, 'w') as File_object:
            for bval in bvals_new:
                if np.abs(bval)>10:
                    bval = int(round(bval))
                else:
                    bval=0
                File_object.write(str(bval) + "\t")

    return(fbvals_new)


def fix_bvals_bvecs(fbvals, fbvecs, b0_threshold=50, atol=1e-2, outpath=None, identifier = "_fix",
                    writeformat="classic", writeover = False, sftp=None):
    """
    Read b-values and b-vectors from disk

    Parameters
    ----------
    fbvals : str
       Full path to file with b-values. None to not read bvals.
    fbvecs : str
       Full path of file with b-vectors. None to not read bvecs.

    Returns
    -------
    bvals : array, (N,) or None
    bvecs : array, (N, 3) or None

    Notes
    -----
    Files can be either '.bvals'/'.bvecs' or '.txt' or '.npy' (containing
    arrays stored with the appropriate values).
    """

    # Loop over the provided inputs, reading each one in turn and adding them
    # to this list:
    if type(fbvals)==str and type(fbvecs)==str:
        bvals, bvecs = read_bvals(fbvals,fbvecs, sftp)
    else:
        bvals = fbvals
        bvecs = fbvecs
        if outpath is None:
            raise Exception('Must feed some path information for saving the fixed files')
    # If bvecs is None, you can just return now w/o making more checks:
    if bvecs is None:
        return bvals, bvecs

    if bvecs.ndim != 2:
        if np.shape(bvecs)[0]%3 == 0:
            bvecs_new = np.zeros([3, int(np.shape(bvecs)[0] / 3)])
            bvecs_new[0, :] = bvecs[:int(np.shape(bvecs)[0] / 3)]
            bvecs_new[1, :] = bvecs[int(np.shape(bvecs)[0] / 3):int(2 * np.shape(bvecs)[0] / 3)]
            bvecs_new[2, :] = bvecs[int(2 * np.shape(bvecs)[0] / 3):]
            bvecs = bvecs_new
        else:
            raise IOError('bvec file should be saved as a two dimensional array')
    if bvecs.shape[1] > bvecs.shape[0]:
        bvecs = bvecs.T

    if bvecs.shape[1] == 4:
        if np.max(bvecs[:,0]) > b0_threshold:
            if bvals is None:
                bvals = bvec[0,:]
            bvecs = np.delete(bvecs,0,1)

    # If bvals is None, you don't need to check that they have the same shape:
    if bvals is None:
        return bvals, bvecs

    if len(bvals.shape) > 1:
        raise IOError('bval file should have one row')

    if max(bvals.shape) != max(bvecs.shape):
            raise IOError('b-values and b-vectors shapes do not correspond')

    from dipy.core.geometry import vector_norm

    bvecs_close_to_1 = abs(vector_norm(bvecs) - 1) <= atol

    if bvecs.shape[1] != 3:
        raise ValueError("bvecs should be (N, 3)")
    dwi_mask = bvals > b0_threshold

    correctvals = [i for i, val in enumerate(bvecs_close_to_1) if val and dwi_mask[i]]
    incorrectvals = [i for i, val in enumerate(bvecs_close_to_1) if not val and dwi_mask[i]]
    if np.size(correctvals) == 0:
        warnings.warn('Bvalues are wrong, will try to rewrite to appropriate values')
        vector_norm(bvecs[dwi_mask])[0]
        bvals_new = copy.copy(bvals)
        bvals_new[dwi_mask] = bvals[dwi_mask] * vector_norm(bvecs[dwi_mask])[0] * vector_norm(bvecs[dwi_mask])[0]
        #bvals = bvals_new
        #baseline_bval = bvals[dwi_mask][0]
        for i in incorrectvals:
            if dwi_mask[i]:
                bvecs[i,:] = bvecs[i,:] / np.sqrt(bvals_new[i]/bvals[i])

        bvecs_close_to_1 = abs(vector_norm(bvecs) - 1) <= atol
        bvals = bvals_new

    if not np.all(bvecs_close_to_1[dwi_mask]):
        correctvals = [i for i,val in enumerate(bvecs_close_to_1) if val and dwi_mask[i]]
        incorrectvals = [i for i,val in enumerate(bvecs_close_to_1) if not val and dwi_mask[i]]
        baseline_bval = bvals[correctvals[0]]
        if np.any(bvals[incorrectvals]==baseline_bval):
            warnings.warn('Bvalues are wrong, will try to rewrite to appropriate values')
            bvals_new = bvals
            for i in incorrectvals:
                if dwi_mask[i]:
                    bvals_new[i] = round(bvals[i] * np.power(vector_norm(bvecs[i,:]),2),1)
            bvals = bvals_new
        for i in incorrectvals:
            if dwi_mask[i]:
                bvecs[i,:] = bvecs[i,:] / np.sqrt(bvals[i]/baseline_bval)
        bvecs_close_to_1 = abs(vector_norm(bvecs) - 1) <= atol
        if not np.all(bvecs_close_to_1[dwi_mask]):
            incorrectvals = [i for i, val in enumerate(bvecs_close_to_1) if not val and dwi_mask[i]]
            raise ValueError("The vectors in bvecs should be unit (The tolerance "
                             "can be modified as an input parameter)")


    if outpath is None:
        base, ext = splitext(fbvals)
    else:
        base=os.path.join(outpath,os.path.basename(fbvals).replace(".txt",""))
        ext=".txt"
    if writeover==True:
        txt = f'copying over the bval file {fbvals} and bvec file {fbvecs}'
        warnings.warn(txt)
    else:
        fbvals = base + identifier + ext
    if writeformat == "classic":
        if sftp is None:
            np.savetxt(fbvals, bvals)
        else:
            np.savetxt(make_temppath(fbvals),bvals)
            sftp.put(make_temppath(fbvals),fbvals)
            os.remove(make_temppath(fbvals))
    if writeformat=="dsi":
        with open(fbvals, 'w') as File_object:
            for bval in bvals:
                if bval>10:
                    bval = int(round(bval))
                else:
                    bval=0
                File_object.write(str(bval) + "\t")
    #base, ext = splitext(fbvecs)
    basevecs = base.replace("bvals","bvecs")
    if not writeover:
        fbvecs = basevecs + identifier + ext
    if writeformat=="classic":
        if sftp is None:
            np.savetxt(fbvecs, bvecs)
        else:
            np.savetxt(make_temppath(fbvecs),bvecs)
            sftp.put(make_temppath(fbvecs),fbvecs)
            os.remove(make_temppath(fbvecs))
            #    with open(fbvecs, 'w') as f:
    #        f.write(str(bvec))
    if writeformat=="dsi":
        with open(fbvecs, 'w') as File_object:
            for i in [0,1,2]:
                for j in np.arange(np.shape(bvecs)[0]):
                    if bvecs[j,i]==0:
                        bvec=0
                    else:
                        bvec=round(bvecs[j,i],3)
                    File_object.write(str(bvec)+"\t")
                File_object.write("\n")
            File_object.close()

    return fbvals, fbvecs

#def extract_bxh_bval_bvec(filepath):

def dist(vals):
    result = 0
    for val in vals:
        result += val*val
    result = np.sqrt(result)
    return(result)

def normalize(vals,tostr=True):
    distance = dist(vals)
    vals_new = []
    for val in vals:
        if tostr:
            vals_new.append(str(val/(distance)))
        else:
            vals_new.append(val / (distance))
    return(vals_new)

def extractbvals_vectortxt(source_file,fileoutpath=None,verbose=False):

    with open(source_file, 'rb') as source:
        if verbose: print('INFO    : Extracting acquisition parameters')
        bvecs = []
        i=0
        for line in source:
            pattern1 = f'Vector\[{str(i)}\]'
            rx1 = re.compile(pattern1, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for a in rx1.findall(str(line)):
                bvec = str(line).split('=')[1].split('\\')[0]
                bvec = bvec.split(')')[0]
                bvec = bvec.split('(')[1]
                bvecs.append([eval(i) for i in (bvec.split(','))])
                i += 1

    return np.array(bvecs)


def extractbvals_fromgrads(source_file,fileoutpath=None,tonorm=True,verbose=False):

    bvals = dsl = dpe = dro = None

    filename = os.path.split(source_file)[1]
    if fileoutpath is None:
        basepath = os.path.split(source_file)[0]
        fileoutpath = basepath + filename.split('.')[0] + "_"
    with open(source_file, 'rb') as source:
        if verbose: print('INFO    : Extracting acquisition parameters')
        bvals = []
        bvecs = []
        i=0
        for line in source:

            pattern1 = str(i)+':'
            rx1 = re.compile(pattern1, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if not len(rx1.findall(str(line)))>0:
                i+=1
                pattern1 = str(i) + ':'
                rx1 = re.compile(pattern1, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for a in rx1.findall(str(line)):
                bvals_all = str(line).split(pattern1)[1].split('\\')[0]
                bvalues_list = bvals_all.split(',')
                bvalues_list = [float(x) for x in bvalues_list]
                bvals.append(str(bvalues_list[-1]))
                if tonorm:
                    bvecs.append(normalize(bvalues_list[:3],tostr=True))
                else:
                    bvecs.append(bvalues_list[:3])

            i += 1
        bvals = "\n".join(bvals)

    if fileoutpath is not None:
        bval_file = fileoutpath + "_bvals.txt"
        print(bval_file)
        File_object = open(bval_file, "w")
        File_object.write(bvals)
        File_object.close()

        if 'bvecs' in locals() and np.size(bvecs) > 0:
            bvecs_file = fileoutpath + "_bvecs.txt"
            File_object = open(bvecs_file, "w")
            for bvec in bvecs:
                File_object.write(str(bvec[0]) + " " + str(bvec[1]) + " " + str(bvec[2]) + "\n")
            File_object.close()
            dsl = []
            dpe = []
            dro = []
            for bvec in bvecs:
                dsl.append(bvec[0])
                dpe.append(bvec[1])
                dro.append(bvec[2])
            dsl = "\n".join(dsl)
            dpe = "\n".join(dpe)
            dro = "\n".join(dro)

        elif dsl and dpe and dro:
            dsl_file = fileoutpath + "_dsl.txt"
            File_object = open(dsl_file, "w")
            File_object.write(dsl)
            File_object.close()

            dpe_file = fileoutpath + "_dpe.txt"
            File_object = open(dpe_file, "w")
            File_object.write(dpe)
            File_object.close()

            dro_file = fileoutpath + "_dro.txt"
            File_object = open(dro_file, "w")
            File_object.write(dro)
            File_object.close()

            bvecs_file = fileoutpath + "_bvecs.txt"
            File_object = open(bvecs_file, "w")
            dpe = dpe.split(" ")
            dsl = dsl.split(" ")
            dro = dro.split(" ")
            print(dpe)
            print(np.shape(dsl))
            for i in range(np.size(dsl)):
                File_object.write(str(dro[i]) + " " + str(dpe[i]) + " " + str(dsl[i]) + "\n")
            File_object.close()
        return bval_file, bvecs_file, bvals, dsl, dpe, dro


def extractbvals_from_method(source_file,fileoutpath=None,tonorm=True,verbose=False):

    bvals = bvecs = None

    filename = os.path.split(source_file)[1]
    if fileoutpath is None:
        basepath = os.path.split(source_file)[0]
        fileoutpath = basepath + filename.split('.')[0] + "_"
    with open(source_file, 'rb') as source:
        if verbose: print('INFO    : Extracting acquisition parameters')
        bvals = []
        bvecs = []
        i=0
        num_bvec_found = 0
        num_bval_found = 0

        bvec_start = False
        bval_start = False
        for line in source:

            pattern1 = 'PVM_DwDir='
            rx1 = re.compile(pattern1, re.IGNORECASE|re.MULTILINE|re.DOTALL)

            pattern2 = 'PVM_DwEffBval'
            rx2 = re.compile(pattern2, re.IGNORECASE|re.MULTILINE|re.DOTALL)

            if bvec_start:
                if num_bvec_found < num_bvecs:
                    vals = str(line).split("\'")[1].split(' \\')[0].split('\\n')[0].split(' ')
                    for val in vals:
                        bvecs.append(val)
                        num_bvec_found = np.size(bvecs)
                else:
                    bvec_start = False
                if num_bvec_found == num_bvecs:
                    bvecs = np.reshape(bvecs,bvec_shape)
                """
                pattern_end = '$$'
                rxend = re.compile(pattern_end, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for a in rxend.findall(str(line)):
                    bvec_start = False
                """
            if bval_start:
                if num_bval_found < num_bvals:
                    vals = str(line).split("\'")[1].split(' \\')[0].split('\\n')[0].split(' ')
                    for val in vals:
                        bvals.append(val)
                        num_bval_found = np.size(bvals)
                else:
                    bval_start = False

            for a in rx1.findall(str(line)):
                bvec_start = True
                shape = str(line).split('(')[1]
                shape = str(shape).split(')')[0]
                bvec_shape = shape.split(',')
                bvec_shape = [int(i) for i in bvec_shape]
                num_bvecs = bvec_shape[0] * bvec_shape[1]

            for a in rx2.findall(str(line)):
                if 'num_bvals' not in locals():
                    bval_start = True
                    shape = str(line).split('(')[1]
                    shape = str(shape).split(')')[0]
                    num_bvals = int(shape)

    if fileoutpath is not None:
        """
        bval_file = fileoutpath + "_bvals.txt"
        print(bval_file)
        File_object = open(bval_file, "w")
        File_object.write(bvals)
        File_object.close()
        """
        while np.shape(bvecs)[0] < np.size(bvals):
            bvecs = np.insert(bvecs, 0, 0, axis=0)
        if 'bvecs' in locals() and np.size(bvecs) > 0:
            bvecs_file = os.path.join(basepath, "methodJS_bvecs.txt")
            File_object = open(bvecs_file, "w")
            for bvec in bvecs:
                File_object.write(str(bvec[0]) + " " + str(bvec[1]) + " " + str(bvec[2]) + "\n")
            File_object.close()

        return bvecs_file


def extractbvals_fromheader(source_file,fileoutpath=None,save=None,writeformat= 'classic', verbose=True):

    bvals = dsl = dpe = dro = None
    if save is not None:
        """
        if basepath==None:
            basepath=os.path.split(source_file)[0]+"/"
        if os.path.isdir(basepath):
            basepath=basepath+"/"
        else:
            if os.path.isdir(os.path.split(basepath)[0]):
                basepath=basepath
            else:
                basepath=os.path.join(sourcepath,basepath)
                basepath=basepath
        """
    filename = os.path.split(source_file)[1]
    if fileoutpath is None:
        basepath = os.path.split(source_file)[0]
        fileoutpath=basepath+filename.split('.')[0]+"_"
    with open(source_file, 'rb') as source:
        if verbose: print('INFO    : Extracting acquisition parameters')
        header_size=source.read(4)
        header_size=struct.unpack('I', header_size)
        if verbose: print('INFO    : Header size = ',int(header_size[0]))
        i=0
        stopsign=200
        bvec_start = False
        bval_start = False
        bvecs = []
        for line in source: 
        
            # pattern1 = '<ParamLong."BaseResolution">  {*'
            # rx1 = re.compile(pattern1, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            
            #pattern1 = 'z_Agilent_bvalue_m00='
            pattern1 = 'z_Agilent_bvalue'
            rx1 = re.compile(pattern1, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern2 = 'z_Agilent_dsl'
            rx2 = re.compile(pattern2, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern3 = 'z_Agilent_dpe'
            rx3 = re.compile(pattern3, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern4 = 'z_Agilent_dro'
            rx4 = re.compile(pattern4, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern5 = 'diffusiondirection'
            rx5 = re.compile(pattern5, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern6 = 'bvalues'
            rx6 = re.compile(pattern6, re.IGNORECASE|re.MULTILINE|re.DOTALL)
            pattern7 = '<value>'
            i+=1
            if i==stopsign:
                print("hi")

            if bvec_start:
                rx7 = re.compile(pattern7, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                bvec_start = False
                for a in rx7.findall(str(line)):
                    bvec_start = True
                    bvec_all = str(line).split('<value>')[1]
                    bvec = bvec_all.split('</value>')[0]
                    bvec = bvec.split(' ')
                    bvecs.append(bvec)

            for a in rx1.findall(str(line)):
                bvals_all = str(line).split(',')[1]
                bvals = bvals_all.split('\\')[0]
            for a in rx2.findall(str(line)):
                dsl_all = str(line).split(',')[1]
                dsl = dsl_all.split('\\')[0]
                #dsl=([float(s) for s in dsl_all.split() if s.isnumeric()])
            for a in rx3.findall(str(line)):
                dpe_all = str(line).split(',')[1]
                dpe = dpe_all.split('\\')[0]
            for a in rx4.findall(str(line)):
                dro_all = str(line).split(',')[1]
                dro = dro_all.split('\\')[0]
            for a in rx5.findall(str(line)):
                bvec_start = True
            for a in rx6.findall(str(line)):
                if not 'bvals_all' in locals():
                    bvals_all = str(line).split('"bvalues">')[1]
                    bvals_all = str(bvals_all).split('</datapoints>')[0]
                    bvals = bvals_all.split(' ')
                    bvals = "\n".join(bvals)

    if save == "all":
        bval_file=fileoutpath+"_bvals.txt"
        print(bval_file)

        if writeformat == "classic":
            File_object = open(bval_file, "w")
            try:
                File_object.write(bvals)
            except:
                print('hi')
            File_object.close()
        if writeformat == "dsi":
            bvals = bvals.split('\n')
            with open(bval_file, 'w') as File_object:
                for bval in bvals:
                    if int(bval) > 10:
                        bval = int(round(float(bval)))
                    else:
                        bval = 0
                    File_object.write(str(bval) + "\t")

        if 'bvecs' in locals() and np.size(bvecs)>0:
            bvecs_file=fileoutpath+"_bvecs.txt"
            if writeformat == "classic":
                File_object = open(bvecs_file,"w")
                for bvec in bvecs:
                    File_object.write(str(bvec[0]) + " " + str(bvec[1]) + " " + str(bvec[2]) + "\n")
                File_object.close()

            if writeformat == "dsi":
                with open(bvecs_file, 'w') as File_object:
                    for i in [0, 1, 2]:
                        for j in np.arange(np.shape(bvecs)[0]):
                            if float(bvecs[j][i]) == 0:
                                bvec = 0
                            else:
                                bvec = round(float(bvecs[j][i]), 3)
                            File_object.write(str(bvec) + "\t")
                        File_object.write("\n")
                    File_object.close()


            dsl = []
            dpe = []
            dro = []
            for bvec in bvecs:
                dsl.append(bvec[0])
                dpe.append(bvec[1])
                dro.append(bvec[2])
            dsl = "\n".join(dsl)
            dpe = "\n".join(dpe)
            dro = "\n".join(dro)

        elif dsl and dpe and dro:
            dsl_file=fileoutpath+"_dsl.txt"
            File_object = open(dsl_file,"w")
            File_object.write(dsl)
            File_object.close()

            dpe_file=fileoutpath+"_dpe.txt"
            File_object = open(dpe_file,"w")
            File_object.write(dpe)
            File_object.close()

            dro_file=fileoutpath+"_dro.txt"
            File_object = open(dro_file,"w")
            File_object.write(dro)
            File_object.close()
                         
            bvecs_file=fileoutpath+"_bvecs.txt"
            File_object = open(bvecs_file,"w")
            dpe=dpe.split(" ")
            dsl=dsl.split(" ")
            dro=dro.split(" ")
            print(dpe)
            print(np.shape(dsl))
            for i in range(np.size(dsl)):
                File_object.write(str(dro[i]) + " " + str(dpe[i]) + " " + str(dsl[i]) + "\n")
            File_object.close()
        
        return bval_file, bvecs_file, bvals, dsl, dpe, dro

import shutil


def read_bval_bvec(fbvals, fbvecs):

    vals=[]
    for this_fname in [fbvals, fbvecs]:
        # If the input was None or empty string, we don't read anything and
        # move on:
        if this_fname is None or not this_fname:
            vals.append(None)
        else:
            if isinstance(this_fname, str):
                base, ext = splitext(this_fname)
                if ext in ['.bvals', '.bval', '.bvecs', '.bvec', '.txt', '.eddy_rotated_bvecs', '']:
                    with open(this_fname, 'r') as f:
                        content = f.read()
                    # We replace coma and tab delimiter by space
                    with InTemporaryDirectory():
                        tmp_fname = "tmp_bvals_bvecs.txt"
                        with open(tmp_fname, 'w') as f:
                            f.write(re.sub(r'(\t|,)', ' ', content))
                        vals.append(np.squeeze(np.loadtxt(tmp_fname)))
                elif ext == '.npy':
                    vals.append(np.squeeze(np.load(this_fname)))
                else:
                    e_s = "File type %s is not recognized" % ext
                    raise ValueError(e_s)
            else:
                raise ValueError('String with full path to file is required')
    bvals, bvecs = vals[0], vals[1]

    return bvals, bvecs


def read_bvecs(fbvecs):
    bvecs=[]
    if fbvecs is None or not fbvecs:
        bvecs.append(None)
    else:
        if isinstance(fbvecs, str):
            base, ext = splitext(fbvecs)
            if ext in ['.bvals', '.bval', '.bvecs', '.bvec', '.txt', '.eddy_rotated_bvecs', '']:
                with open(fbvecs, 'r') as f:
                    content = f.read()
                # We replace coma and tab delimiter by space
                with InTemporaryDirectory():
                    tmp_fname = "tmp_bvals_bvecs.txt"
                    with open(tmp_fname, 'w') as f:
                        f.write(re.sub(r'(\t|,)', ' ', content))
                    bvecs.append(np.squeeze(np.loadtxt(tmp_fname)))
            elif ext == '.npy':
                bvecs.append(np.squeeze(np.load(fbvecs)))
            else:
                e_s = "File type %s is not recognized" % ext
                raise ValueError(e_s)
        else:
            raise ValueError('String with full path to file is required')
    if np.shape(bvecs)[0]==1:
        bvecs=bvecs[0]
    return bvecs


def find_bval_bvecs(subjectpath, subject="",outpath=None):

    if outpath is None:
        outpath=subjectpath
    fbtable = glob.glob(os.path.join(subjectpath,"b_table.txt"))
    finputbvals=glob.glob(os.path.join(subjectpath,"input_bvals.txt"))
    finputbvecs=glob.glob(os.path.join(subjectpath, "*input_gradient_matrix*"))
    bxhs=glob.glob(os.path.join(subjectpath, "*.bxh*"))
    fbvals_txt = glob.glob(os.path.join(subjectpath,"*bvals.txt"))
    grads_txt = glob.glob(os.path.join(subjectpath,"*grads.txt"))
    headfile = glob.glob(os.path.join(subjectpath,"*studio.headfile"))

    if np.size(fbtable)>0:
        bvals_all=[]
        bvecs_all=[]
        fbtable=fbtable[0]
        with open(fbtable, 'rb') as source:
            for line in source:
                bvals = str(line).split("'")[1]
                bvals = bvals.split("\\n")[0]
                bvals = bvals.split("\\t")
                bvals_all.append(float(bvals[0]))
                bvecs_all.append([float(bvals[1]), float(bvals[2]), float(bvals[3])])
        #return np.array(bvals), np.array(bvecs)
        bvals_all = np.array(bvals_all)
        bvecs_all = np.array(bvecs_all)
        fbvals = os.path.join(outpath,f'{subject}_bvals.txt')
        fbvecs = os.path.join(outpath,f'{subject}_bvecs.txt')
        writebval(bvals_all, fbvals, subject=subject, writeformat = "line", overwrite=False)
        writebvec(bvecs_all, fbvecs, subject=subject, writeformat = "classic", overwrite=False)
    elif np.size(headfile)>0:
        fbvals, fbvecs, _, _, _, _ = extractbvals_fromheader(headfile[0],
                                                            fileoutpath=os.path.join(outpath, subject),
                                                            save="all")
    elif np.size(fbtable)>0:
        bvals_all=[]
        bvecs_all=[]
        fbtable=fbtable[0]
        with open(fbtable, 'rb') as source:
            for line in source:
                bvals = str(line).split("'")[1]
                bvals = bvals.split("\\n")[0]
                bvals = bvals.split("\\t")
                bvals_all.append(float(bvals[0]))
                bvecs_all.append([float(bvals[1]), float(bvals[2]), float(bvals[3])])
        #return np.array(bvals), np.array(bvecs)
        bvals_all = np.array(bvals_all)
        bvecs_all = np.array(bvecs_all)
        fbvals = os.path.join(outpath,f'{subject}_bvals.txt')
        fbvecs = os.path.join(outpath,f'{subject}_bvecs.txt')
        writebval(bvals_all, fbvals, subject=subject, writeformat = "line", overwrite=False)
        writebvec(bvecs_all, fbvecs, subject=subject, writeformat = "classic", overwrite=False)
    elif np.size(finputbvals) > 0 and np.size(finputbvecs) > 0:
        fbvals = finputbvals[0]
        fbvecs = finputbvecs[0]
    elif np.size(bxhs) > 0:
        dwipath = largerfile(subjectpath,identifier=".nii") #This just catches the LARGEST file, which should be a dwi file. This is obviously an unstable method and the best way to handle it would be to go through every bxh file and go through them individualls
        bxhpath = dwipath.replace(".nii.gz", ".bxh")
        bxhpath = bxhpath.replace(".nii", ".bxh")
        fbvals, fbvecs, _, _, _, _ = extractbvals_fromheader(bxhpath,
                                                            fileoutpath=os.path.join(outpath, subject),
                                                            save="all")
    elif np.size(fbvals_txt) > 0:
        fbvecs_txt = glob.glob(os.path.join(subjectpath, "*bvec*.txt"))
        if np.size(fbvals_txt)==1 and np.size(fbvecs_txt)==1:
            #fbvals, fbvecs = read_bval_bvec(fbvals_txt[0], fbvecs_txt[0])
            fbvals = fbvals_txt[0]
            fbvecs = fbvecs_txt[0]
        else:
            raise Exception('Too many possible bvalue files in folder')
    elif np.size(grads_txt) > 0:
        fbvals, fbvecs, _, _, _, _ = extractbvals_fromgrads(grads_txt[0],
                                                            fileoutpath=os.path.join(outpath, subject))
    else:
        raise Exception("Sorry, nothing here looks like it could serve as a way to extract bvalues")
    return fbvals, fbvecs


def writebval(bvals, outpath, subject=None, writeformat = "line", overwrite=False):
    
    if os.path.isdir(outpath):
        if subject is not None:
            bval_file = os.path.join(outpath, subject+"_bvals.txt")
        else:
            bval_file = os.path.join(outpath, "bvals.txt")
    else:
        bval_file = outpath
    
    if os.path.exists(bval_file):
        if overwrite:
            os.remove(bval_file)
        else:
            print(f'already wrote {bval_file}')
            return bval_file
    File_object = open(bval_file, "w")
    for bval in bvals:
        if writeformat == "line" or writeformat == 'classic':
            File_object.write(str(bval) + "\n")
        if writeformat == "tab":
            File_object.write(str(bval) + "\t")
        if writeformat == "dsi":
            bval = int(round(int(bval)))
            File_object.write(str(bval) + "\t")
        if writeformat == 'mrtrix':
            bval = int(round(int(bval)))
            File_object.write(str(bval) + " ")
    File_object.close()
    return bval_file


def writebvec(bvecs, outpath, subject=None, writeformat = "line", overwrite=False):
    
    if os.path.isdir(outpath) and subject is not None:
        bvec_file = os.path.join(outpath, subject+"_bvecs.txt")
    else:
        bvec_file = outpath
    if np.size(np.shape(bvecs))==1:
        bvecs = np.resize(bvecs,[3,int(np.size(bvecs)/3)]).transpose()
    if np.shape(bvecs)[0] == 3:
        bvecs = bvecs.transpose()
    if os.path.exists(bvec_file):
        if overwrite:
            os.remove(bvec_file)
        else:
            print(f'already wrote {bvec_file}')
            return bvec_file
    if writeformat=="dsi":
        with open(bvec_file, 'w') as File_object:
            for i in [0,1,2]:
                for j in np.arange(np.shape(bvecs)[0]):
                    bvec=round(float(bvecs[j,i]),5)
                    File_object.write(str(bvec)+"\t")
                File_object.write("\n")
            File_object.close()
    elif writeformat=="line":
        with open(bvec_file, 'w') as File_object:
            for i in [0,1,2]:
                for j in np.arange(np.shape(bvecs)[0]):
                    if bvecs[j,i]==0:
                        bvec=0
                    elif bvecs[j,i]==1:
                        bvec=1
                    else:
                        bvec=bvecs[j,i]
                    File_object.write(str(bvec)+" ")
            File_object.close()
        #shutil.copyfile(bvecs[0], bvec_file)
    elif writeformat=="classic":
        File_object = open(bvec_file, "w")
        for bvec in bvecs:
            File_object.write(str(bvec[0]) + " " + str(bvec[1]) + " " + str(bvec[2]) + "\n")
        File_object.close()
    elif writeformat=='BRUKER':
        File_object = open(bvec_file, "w")
        num_dirs = np.shape(bvecs)[0]
        File_object.write(f'[directions={num_dirs}]\n')
        for i,bvec in enumerate(bvecs):
            if i+1!=num_dirs:
                File_object.write(f'Vector[{i}]= ({str(bvec[0])}, {str(bvec[1])}, {str(bvec[2])})\n')
            else:
                File_object.write(f'Vector[{i}]= ({str(bvec[0])}, {str(bvec[1])}, {str(bvec[2])})')
    return bvec_file


def writebfiles(bvals, bvecs, outpath, subject, writeformat = "line", overwrite=False):

    bval_file = writebval(bvals, outpath, subject, writeformat = 'tab', overwrite=overwrite)
    bvec_file = writebvec(bvecs, outpath, subject, writeformat = 'classic', overwrite=overwrite)
    """
    bvec_file = os.path.join(outpath, subject+"_bvecs.txt")
    bval_file = os.path.join(outpath, subject+"_bvals.txt")

    if (os.path.exists(bvec_file) or os.path.exists(bval_file)) and not overwrite:
        print(f'Already written files at {bvec_file} or {bval_file}')
        return bval_file, bvec_file

    if os.path.exists(bvec_file) and overwrite:
        os.remove(bvec_file)

    if writeformat=="dsi":
        with open(bvec_file, 'w') as File_object:
            for i in [0,1,2]:
                for j in np.arange(np.shape(bvecs)[0]):
                    if bvecs[j,i]==0:
                        bvec=0
                    else:
                        bvec=round(bvecs[j,i],3)
                    File_object.write(str(bvec)+"\t")
                File_object.write("\n")
            File_object.close()
    else:
        shutil.copyfile(bvecs[0], bvec_file)

    if os.path.exists(bval_file) and overwrite:
        os.remove(bval_file)
    File_object = open(bval_file, "w")
    for bval in bvals:
        if writeformat == "line":
            File_object.write(str(bval) + "\n")
        if writeformat == "tab":
            File_object.write(str(bval) + "\t")
        if writeformat == "dsi":
            bval = int(round(bval))
            File_object.write(str(bval) + "\t")
    File_object.close()
    """
    return bval_file, bvec_file


def writebfiles_old(subjectpath, subject, outpath = None, writeformat = "line", fbvals=None, fbvecs=None, overwrite=False):
    if outpath is None:
        outpath = subjectpath
    if fbvals is None or fbvecs is None:
        """
        bval_input = glob.glob(os.path.join(subjectpath, "input_bvals.txt"))
        if np.size(bval_input) > 0:
            with open(bval_input[0], 'rb') as source:
                pattern6 = 'b-value'
                rx1 = re.compile(pattern6, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for line in source:
                    for a in rx1.findall(str(line)):
                        bval_all = str(line).split('=')[1]
                        bval = bval_all.split('\\')[0]
                        bval = float(bval)
                        bval = int(round(bval))
                        pass
        """
        bvals, bvecs = find_bval_bvecs(subjectpath, subject=subject)
    else:
        bvals, bvecs = read_bval_bvec(fbvals, fbvecs)
    #bvecs = glob.glob(os.path.join(subjectpath,"*input_gradient_matrix*"))

    bvec_file = os.path.join(outpath, subject+"_bvecs.txt")
    if os.path.exists(bvec_file) and overwrite:
        os.remove(bvec_file)
    if writeformat=="dsi":
        with open(bvec_file, 'w') as File_object:
            for i in [0,1,2]:
                for j in np.arange(np.shape(bvecs)[0]):
                    if bvecs[j,i]==0:
                        bvec=0
                    else:
                        bvec=round(bvecs[j,i],3)
                    File_object.write(str(bvec)+"\t")
                File_object.write("\n")
            File_object.close()
    else:
        shutil.copyfile(bvecs[0], bvec_file)
    """
        bval_input = glob.glob(os.path.join(subjectpath,"input_bvals.txt"))
        if np.size(bval_input)>0:
            with open(bval_input[0], 'rb') as source:
                pattern6 = 'b-value'
                rx1 = re.compile(pattern6, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for line in source:
                    for a in rx1.findall(str(line)):
                        bval_all = str(line).split('=')[1]
                        bval = bval_all.split('\\')[0]
                        bval = float(bval)
                        bval = int(round(bval))
                        pass
    bvals = []
    with open(bvec_file) as source:
        for line in source:
            if "0, 0, 0" in line:
                bvals.append(0)
            else:
                bvals.append(bval)
    """
    bval_file = os.path.join(outpath, subject+"_bvals.txt")
    if os.path.exists(bval_file) and overwrite:
        os.remove(bval_file)
    File_object = open(bval_file, "w")
    for bval in bvals:
        if writeformat == "line":
            File_object.write(str(bval) + "\n")
        if writeformat == "tab":
            File_object.write(str(bval) + "\t")
        if writeformat == "dsi":
            bval = int(round(bval))
            File_object.write(str(bval) + "\t")
    File_object.close()
    return bval_file, bvec_file


def extractbvals_research(dwipath, subject, outpath=None, writeformat="tab", fix=True, overwrite=False):

    if os.path.isdir(dwipath):
        #subjectpath = os.path.join(dwipath, subject)
        subjectpath = glob.glob(os.path.join(os.path.join(dwipath, "diffusion*"+subject+"*")))
        subjectpath = subjectpath[0]
        if outpath is None:
            outpath = subjectpath
        fbvals = np.size(glob.glob(os.path.join(outpath + '*_bval*fix*')))
        fbvecs = np.size(glob.glob(os.path.join(outpath + '*_bvec*fix*')))
        if (fbvals == 0 and fbvecs == 0) or overwrite:
            #fbvals = (glob.glob(subjectpath + '*_bval*'))
            #fbvecs = (glob.glob(subjectpath + '*_bvec*'))
            fbvals=(glob.glob(os.path.join(outpath, '*' + subject + '*_bvals.txt')))
            fbvecs=(glob.glob(os.path.join(outpath, '*' + subject + '*_bvecs.txt')))
            if ((np.size(fbvals) > 0 and np.size(fbvecs) > 0) and not overwrite):
                fbvals = fbvals[0]
                fbvecs = fbvecs[0]
                if fix:
                    fix_bvals_bvecs(fbvals, fbvecs)
            else:
                bvals, bvecs = find_bval_bvecs(subjectpath)
                bval_file, bvec_file = writebfiles(bvals, bvecs, outpath, subject, writeformat=writeformat,
                                                   overwrite=overwrite)
                if fix:
                    fbvals, fbvecs = fix_bvals_bvecs(bval_file, bvec_file)
        return fbvals, fbvecs

    elif os.path.isfile(dwipath):
        dwifolder = os.path.dirname(os.path.abspath(dwipath))
        subjectpath = os.path.join(dwifolder, "*" + subject)
        if outpath is None:
            outpath = subjectpath
        fbvals = np.size(glob.glob(subjectpath + '*_bval*fix*'))
        fbvecs = np.size(glob.glob(subjectpath + '*_bvec*fix*'))
        if fbvals == 0 and fbvecs == 0:
            fbvals = np.size(glob.glob(subjectpath + '*_bval*'))
            fbvecs = np.size(glob.glob(subjectpath + '*_bvec*'))
            if (fbvals) == 0 or (fbvecs) == 0:
                bxhpath = dwipath.replace(".nii.gz", ".bxh")
                bxhpath = bxhpath.replace(".nii", ".bxh")
                fbvals, fbvecs, _, _, _, _ = extractbvals_fromheader(bxhpath,
                                                                    fileoutpath=os.path.join(dwifolder, subject),
                                                                    save="all")
                if fix:
                    fix_bvals_bvecs(fbvals, fbvecs)

import shutil

def extractbvals(subjectpath, subject, outpath=None, writeformat="tab", fix=True, overwrite=False):

    if os.path.isdir(subjectpath):
        #subjectpath = os.path.join(dwipath, subject)
        if outpath is None:
            outpath = subjectpath
        fbvals = (glob.glob(os.path.join(outpath,'*_bvals*fix*')))
        fbvecs = (glob.glob(os.path.join(outpath,'*_bvecs*fix*')))
        if (np.size(fbvals) == 0 and np.size(fbvecs) == 0) or overwrite:
            #fbvals = (glob.glob(subjectpath + '*_bval*'))
            #fbvecs = (glob.glob(subjectpath + '*_bvec*'))
            fbvals=(glob.glob(os.path.join(outpath, '*' + subject + '*_bvals.txt')))
            fbvecs=(glob.glob(os.path.join(outpath, '*' + subject + '*_bvecs.txt')))
            if (np.size(fbvals) > 0 and np.size(fbvecs) > 0) and not overwrite and fix:
                if (np.size(fbvals) ==1 and np.size(fbvecs) ==1):
                    fbvals = fbvals[0]
                    fbvecs = fbvecs[0]
                else:
                    raise Exception
                if fix:
                    fbvals, fbvecs = fix_bvals_bvecs(fbvals, fbvecs, outpath=outpath, writeformat=writeformat)
            else:
                fbvals, fbvecs = find_bval_bvecs(subjectpath, subject = subject, outpath=outpath)
                if fix:
                    fbvals, fbvecs = fix_bvals_bvecs(fbvals, fbvecs,outpath=outpath, writeformat=writeformat)
        else:
            if (np.size(fbvals) == 1 and np.size(fbvecs) == 1):
                fbvals = fbvals[0]
                fbvecs = fbvecs[0]
            else:
                raise Exception('too many bvalue files')
        return fbvals, fbvecs

    elif os.path.isfile(subjectpath):
        dwifolder = os.path.dirname(os.path.abspath(subjectpath))
        subjectpath = os.path.join(dwifolder, "*" + subject)
        if outpath is None:
            outpath = subjectpath
        fbvals = np.size(glob.glob(subjectpath + '*_bval*fix*'))
        fbvecs = np.size(glob.glob(subjectpath + '*_bvec*fix*'))
        if fbvals == 0 and fbvecs == 0:
            fbvals = np.size(glob.glob(subjectpath + '*_bval*'))
            fbvecs = np.size(glob.glob(subjectpath + '*_bvec*'))
            if (fbvals) == 0 or (fbvecs) == 0:
                #bxhpath = subjectpath.replace(".nii.gz", ".bxh")
                bxhpath = subjectpath.replace(".nii", ".bxh")
                fbvals, fbvecs, _, _, _, _ = extractbvals_fromheader(bxhpath,
                                                                    fileoutpath=os.path.join(dwifolder, subject),
                                                                    save="all")
                if fix:
                    fix_bvals_bvecs(fbvals, fbvecs)


def rewrite_subject_bvalues(dwipath, subject, outpath=None, writeformat="tab", overwrite=False):

    if os.path.isdir(dwipath):
        #subjectpath = os.path.join(dwipath, subject)
        subjectpath = glob.glob(os.path.join(os.path.join(dwipath, "*"+subject+"*")))
        subjectpath = subjectpath[0]
        if outpath is None:
            outpath = subjectpath
        fbvals = np.size(glob.glob(subjectpath + '*_bval*fix*'))
        fbvecs = np.size(glob.glob(subjectpath + '*_bvec*fix*'))
        if (fbvals == 0 and fbvecs == 0) or overwrite:
            #fbvals = (glob.glob(subjectpath + '*_bval*'))
            #fbvecs = (glob.glob(subjectpath + '*_bvec*'))
            fbvals=(glob.glob(os.path.join(subjectpath, '*' + subject + '*_bvals.txt')))
            fbvecs=(glob.glob(os.path.join(subjectpath, '*' + subject + '*_bvecs.txt')))
            if (np.size(fbvals) > 0 and np.size(fbvecs) > 0) and not overwrite:
                fbvals = fbvals[0]
                fbvecs = fbvecs[0]
                #fix_bvals_bvecs(fbvals, fbvecs)
            else:
                bvals, bvecs = find_bval_bvecs(subjectpath)
                bval_file, bvec_file = writebfiles(bvals, bvecs, outpath, subject, writeformat = writeformat, overwrite=overwrite)
                #bval_file, bvec_file = writebfiles(subjectpath, subject, outpath, writeformat=writeformat, overwrite=overwrite)
                #fbvals, fbvecs = fix_bvals_bvecs(bval_file, bvec_file)
        return fbvals, fbvecs

    elif os.path.isfile(dwipath):
        dwifolder = os.path.dirname(os.path.abspath(dwipath))
        subjectpath = os.path.join(dwifolder, "*" + subject)
        if outpath is None:
            outpath = subjectpath
        fbvals = np.size(glob.glob(subjectpath + '*_bval*fix*'))
        fbvecs = np.size(glob.glob(subjectpath + '*_bvec*fix*'))
        if fbvals == 0 and fbvecs == 0:
            fbvals = np.size(glob.glob(subjectpath + '*_bval*'))
            fbvecs = np.size(glob.glob(subjectpath + '*_bvec*'))
            if (fbvals) == 0 or (fbvecs) == 0:
                bxhpath = dwipath.replace(".nii.gz", ".bxh")
                bxhpath = bxhpath.replace(".nii", ".bxh")
                fbvals, fbvecs, _, _, _, _ = extractbvals_fromheader(bxhpath,
                                                                    fileoutpath=os.path.join(dwifolder, subject),
                                                                    save="all")
                fix_bvals_bvecs(fbvals, fbvecs)


def checkbxh(source_file, verbose = False):
    bxhtype = None
    with open(source_file, 'rb') as source:
        for line in source:

            pattern1 = "psdname"
            rx1 = re.compile(pattern1, re.IGNORECASE | re.MULTILINE | re.DOTALL)

            for a in rx1.findall(str(line)):
                sequencetype = str(line).split('<psdname>')[1]
                sequencetype = str(sequencetype).split('</psdname>')[0]
                break
    if sequencetype == "epi2muse":
        bxhtype = "dwi"
    elif sequencetype == "BRAVO":
        bxhtype = "T1"

    return bxhtype


def same_axis(first,second):
    if first==second:
        return 1
    if first=="A" and second=="P" or first=="P" and second=="A" or first==" ":
        print('hi')

"""
def bvec_reorient(bvecs,orig_orient="ARI",new_orient="RAS"):

    for i in range(3):
        #if new_orient[i]
        echo('jo')

    new_bvecs = np.c_[bvecs[:, 0], bvecs[:, 1], -bvecs[:, 2]]
"""