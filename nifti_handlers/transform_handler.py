"""
Created by Jacques Stout
"""


from DTC.nifti_handlers.nifti_handler import *
from DTC.tract_manager.streamline_nocheck import load_trk
from DTC.file_manager.computer_nav import splitpath, make_temppath
import shutil
import os
import numpy as np
import nibabel as nib
import warnings
from dipy.align.reslice import reslice

from dipy.align.imaffine import (transform_centers_of_mass,
                                 MutualInformationMetric,
                                 AffineRegistration)
from dipy.align.transforms import (TranslationTransform3D,
                                   RigidTransform3D,
                                   AffineTransform3D)

def affine_reg(static, static_grid2world,
               moving, moving_grid2world):
    # https://gist.github.com/Garyfallidis/42dd1ab04371272050221275c6ab9bd6

    c_of_mass = transform_centers_of_mass(static,
                                          static_grid2world,
                                          moving,
                                          moving_grid2world)

    nbins = 32
    sampling_prop = None
    metric = MutualInformationMetric(nbins, sampling_prop)

    level_iters = [500, 100, 10]

    sigmas = [3.0, 1.0, 0.0]

    factors = [4, 2, 1]

    affreg = AffineRegistration(metric=metric,
                                level_iters=level_iters,
                                sigmas=sigmas,
                                factors=factors)

    transform = TranslationTransform3D()
    params0 = None
    starting_affine = c_of_mass.affine
    translation = affreg.optimize(static, moving, transform, params0,
                                  static_grid2world, moving_grid2world,
                                  starting_affine=starting_affine)

    transformed = translation.transform(moving)

    transform = RigidTransform3D()
    params0 = None
    starting_affine = translation.affine
    rigid = affreg.optimize(static, moving, transform, params0,
                            static_grid2world, moving_grid2world,
                            starting_affine=starting_affine)
    transformed = rigid.transform(moving)

    transform = AffineTransform3D()
    params0 = None
    starting_affine = rigid.affine
    affine = affreg.optimize(static, moving, transform, params0,
                             static_grid2world, moving_grid2world,
                             starting_affine=starting_affine)

    transformed = affine.transform(moving)

    return transformed, affine.affine


def trans_reg(static, static_grid2world,
              moving, moving_grid2world):
    c_of_mass = transform_centers_of_mass(static,
                                          static_grid2world,
                                          moving,
                                          moving_grid2world)

    nbins = 32
    sampling_prop = None
    metric = MutualInformationMetric(nbins, sampling_prop)

    level_iters = [500, 100, 10]

    sigmas = [3.0, 1.0, 0.0]

    factors = [4, 2, 1]

    affreg = AffineRegistration(metric=metric,
                                level_iters=level_iters,
                                sigmas=sigmas,
                                factors=factors)

    transform = TranslationTransform3D()
    params0 = None
    starting_affine = c_of_mass.affine
    translation = affreg.optimize(static, moving, transform, params0,
                                  static_grid2world, moving_grid2world,
                                  starting_affine=starting_affine)

    transformed = translation.transform(moving)

    return transformed, translation.affine


def translation_reg(static, static_grid2world,
              moving, moving_grid2world, return_trans=False):

    if np.size(np.shape(moving))>3:
        moving = moving[...,0]

    if np.isnan(np.min(static)):
        static[np.isnan(static)] = 0

    if np.isnan(np.min(moving)):
        moving[np.isnan(moving)] = 0

    c_of_mass = transform_centers_of_mass(static,
                                          static_grid2world,
                                          moving,
                                          moving_grid2world)

    nbins = 32
    sampling_prop = None
    metric = MutualInformationMetric(nbins, sampling_prop)

    level_iters = [500, 100, 10]

    sigmas = [3.0, 1.0, 0.0]

    factors = [4, 2, 1]

    affreg = AffineRegistration(metric=metric,
                                level_iters=level_iters,
                                sigmas=sigmas,
                                factors=factors)

    transform = TranslationTransform3D()
    params0 = None
    starting_affine = c_of_mass.affine
    translation = affreg.optimize(static, moving, transform, params0,
                                  static_grid2world, moving_grid2world,
                                  starting_affine=starting_affine)

    transformed = translation.transform(moving)

    if return_trans:
        return transformed, translation.affine, translation
    return transformed, translation.affine


def rigid_reg(static, static_grid2world,
              moving, moving_grid2world, return_rigid=False):

    moving_orig = moving
    if np.size(np.shape(moving))>3:
        moving_orig = moving
        moving = moving[...,0]

    c_of_mass = transform_centers_of_mass(static,
                                          static_grid2world,
                                          moving,
                                          moving_grid2world)

    nbins = 32
    sampling_prop = None
    metric = MutualInformationMetric(nbins, sampling_prop)

    level_iters = [500, 100, 10]

    sigmas = [3.0, 1.0, 0.0]

    factors = [4, 2, 1]

    affreg = AffineRegistration(metric=metric,
                                level_iters=level_iters,
                                sigmas=sigmas,
                                factors=factors)

    transform = TranslationTransform3D()
    params0 = None
    starting_affine = c_of_mass.affine
    translation = affreg.optimize(static, moving, transform, params0,
                                  static_grid2world, moving_grid2world,
                                  starting_affine=starting_affine)

    transformed = translation.transform(moving)

    transform = RigidTransform3D()
    params0 = None
    starting_affine = translation.affine
    rigid = affreg.optimize(static, moving, transform, params0,
                            static_grid2world, moving_grid2world,
                            starting_affine=starting_affine)
    #transformed = np.zeros(list(np.shape(rigid.transform(moving_orig[...,0])))+[np.shape(moving_orig)[3]])
    #transformed = np.zeros(np.shape(moving_orig))
    #transformed = np.zeros(list(np.shape(reslice(rigid.transform(moving_orig[...,0]), moving_grid2world, [0.1,0.1,0.1], [0.3,0.3,0.3])[0]))+[np.shape(moving_orig)[3]])
    if np.size(np.shape(moving_orig))>3:
        transformed = np.zeros(list(np.shape(rigid.transform(moving_orig[..., 0]))) + [np.shape(moving_orig)[3]])
        #if reslice:
            #transformed, reslice_affine = reslice(rigid.transform(moving_orig), moving_grid2world,
            #                                             [0.1, 0.1, 0.1], [0.3, 0.3, 0.3])
        #for i in np.arange(np.shape(moving_orig)[3]):
        #transformed[..., i], reslice_affine = reslice(rigid.transform(moving_orig[..., i]), moving_grid2world,
         #                                             [0.1, 0.1, 0.1], [0.3, 0.3, 0.3])

        for i in np.arange(np.shape(moving_orig)[3]):
            transformed[..., i] = rigid.transform(moving_orig[..., i])
    else:
        transformed = rigid.transform(moving_orig)

    if return_rigid:
        return transformed, rigid.affine, rigid
    return transformed, rigid.affine


def header_superpose(target_path, origin_path, outpath=None, verbose=False):

    target_nii=nib.load(target_path)
    origin_nii=nib.load(origin_path)
    if np.shape(target_nii._data)[0:3] != np.shape(origin_nii._data)[0:3]:
        raise TypeError('not implemented')
    else:
        target_affine=target_nii._affine
        target_header = target_nii._header
        if np.any(target_affine != origin_nii._affine) or np.any(target_header != origin_nii._header):
            new_nii = nib.Nifti1Image(origin_nii._data, target_affine, target_header)
            if outpath is None:
                outpath = origin_path
                txt= (f'Overwriting original file {origin_path}')
                warnings.warn(txt)
            if verbose:
                print(f'Saving nifti file to {outpath}')
            nib.save(new_nii, outpath)
            if verbose:
                print(f'Saved')
        else:
            print('Same header for target_path and origin_path, skipping')


def affine_superpose(target_path, origin_path, outpath=None, verbose=False):
    target_nii=nib.load(target_path)
    origin_nii=nib.load(origin_path)
    if np.shape(target_nii._data)[0:3] != np.shape(origin_nii._data)[0:3]:
        raise TypeError('not implemented')
    else:
        target_affine=target_nii._affine
        origin_header = origin_nii._header
        if np.any(target_affine != origin_nii._affine):
            new_nii = nib.Nifti1Image(origin_nii._data, target_affine, origin_header)
            if outpath is None:
                outpath = origin_path
                txt= (f'Overwriting original file {origin_path}')
                warnings.warn(txt)
            if verbose:
                print(f'Saving nifti file to {outpath}')
            nib.save(new_nii, outpath)
            if verbose:
                print(f'Saved')
        else:
            print('Same header for target_path and origin_path, skipping')


def get_affine_transform_nii(target_path, origin_path, verbose=False):

    target_nii=nib.load(target_path)
    origin_nii=nib.load(origin_path)
    if np.shape(target_nii._data)[0:3] != np.shape(origin_nii._data)[0:3]:
        raise TypeError('not implemented')
    else:
        target_affine=target_nii._affine
        origin_affine=origin_nii._affine
        return get_affine_transform(origin_affine,target_affine)


def get_affine_transform(origin_affine, target_affine):

    transform_affine = np.eye(4)
    transform_affine[:3,:3] = np.dot(np.linalg.inv(origin_affine[:3,:3]), target_affine[:3,:3])
    transform_affine[:3,3] = origin_affine[:3,3]-target_affine[:3,3]
    return transform_affine

def get_affine_transform_test(origin_affine, target_affine):

    transform_affine = np.dot(np.linalg.inv(origin_affine), target_affine)
    return transform_affine


def transform_image(target_path, origin_path, outpath=None):
    target_nii=nib.load(target_path)
    origin_nii=nib.load(origin_path)
    if np.shape(target_nii._data)[0:3] != np.shape(origin_nii._data)[0:3]:
        raise TypeError('not implemented')
    else:
        target_affine=target_nii._affine
        target_header = target_nii._header
        if np.any(target_affine != origin_nii._affine) or np.any(target_header != origin_nii._header):
            new_nii = nib.Nifti1Image(origin_nii._data, target_affine, target_header)
            if outpath is None:
                outpath = origin_path
            nib.save(new_nii, outpath)


def read_affine_txt(path, dimension = 3):
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
        rows = content.split('\n')
        rows.remove('')
        array=[]
        i=0
        for row in rows:
            array.append(row.split(' '))
        array = np.array(array)
        return(array)
    else:
        raise Exception(f'Unrecognized path {path}')


def header_superpose_trk(target_path, origin_path, outpath=None):

    if not isinstance(origin_path, str):
        origin_trk = origin_path
    else:
        origin_trk = load_trk(origin_path, 'same')

    target_data, target_affine, vox_size, target_header, target_ref_info = extract_nii_info(target_path)

    if outpath is None:
        if isinstance(origin_path, str):
            warnings.warn("Will copy over old trkfile, if this what you want?")
            permission = input("enter yes or y if you are ok with this")
            if permission.lower() == "yes" or permission.lower() == "y":
                outpath = origin_trk
            else:
                raise Exception("Will not copy over old trk file")
        else:
            raise Exception("Need to specify a output path of some kind")

    trk_header = origin_trk.space_attributes
    trk_affine = origin_trk._affine
    trkstreamlines = origin_trk.streamlines
    if np.any(trk_header[1][0:3] != np.shape(target_data)[0:3]):
        raise TypeError('Size of the originating matrix are difference, recalculation not implemented')
    if np.any(trk_affine != target_affine):
        test=3
        if test==1:
            trk_header = list(trk_header)
            trk_header[0] = target_affine
            trk_header = tuple(trk_header)
            myheader = create_tractogram_header(outpath, *trk_header)
            trk_sl = lambda: (s for s in trkstreamlines)
            save_trk_heavy_duty(outpath, streamlines=trk_sl,
                                           affine=target_affine, header=myheader)
        elif test==2:
            transform_matrix = (np.inverse(np.transpose(trk_affine)*trk_affine)*np.transpose(trk_affine))* target_affine
            from dipy.tracking.streamline import transform_streamlines
            myheader = create_tractogram_header(outpath, *trk_header)
            new_streamlines = transform_streamlines(trkstreamlines, transform_matrix)
            trk_sl = lambda: (s for s in new_streamlines)
            save_trk_heavy_duty(outpath, streamlines=trkstreamlines,
                                           affine=trk_affine, header=myheader)
        elif test==3:
            myheader = create_tractogram_header(outpath, *target_ref_info)
            trk_sl = lambda: (s for s in trkstreamlines)
            save_trk_heavy_duty(outpath, streamlines=trk_sl,
                                           affine=target_affine, header=myheader)
    else:
        print("No need to change affine, bring to new path")
        if isinstance(origin_path, str):
            copyfile(origin_path, outpath)
        else:
            myheader = create_tractogram_header(outpath, *trk_header)
            save_trk_heavy_duty(outpath, streamlines=trkstreamlines,
                                affine=target_affine, header=myheader)


def affine_superpose(target_path, origin_path, outpath=None, transpose=None, verbose=False):
    target_nii=nib.load(target_path)
    origin_nii=nib.load(origin_path)
    if np.shape(target_nii._data)[0:3] != np.shape(origin_nii._data)[0:3]:
        raise TypeError('not implemented')
    else:
        target_affine=target_nii._affine
        #added this to add a little translocation onto the atlas whenever necessary (like space_transpose). A bit convoluted
        # but didnt want to save a nifti file over itself multiple times.
        if transpose is not None:
            target_affine[:3,3] = transpose
        if np.any(target_affine != origin_nii._affine):
            new_nii = nib.Nifti1Image(origin_nii._data, target_affine, origin_nii._header)
            if outpath is None:
                outpath = origin_path
            nib.save(new_nii, outpath)
            if verbose:
                print(f'Used affine of {target_path} for data in {origin_path} to create {outpath}')
            return 1 #returns 1 if it saved a new file
        else:
            shutil.copy(origin_path,outpath)
            return 0

def affine_recenter(origin_path, outpath=None, fullrecenter = False, verbose=False):
    origin_nii=nib.load(origin_path)

    origin_affine=origin_nii._affine
    #added this to add a little translocation onto the atlas whenever necessary (like space_transpose). A bit convoluted
    # but didnt want to save a nifti file over itself multiple times.
    new_affine = np.eye(4)
    if not fullrecenter:
        new_affine[:3,:3] = origin_affine[:3,:3]

    if np.any(new_affine != origin_nii._affine):
        new_nii = nib.Nifti1Image(origin_nii._data, new_affine, origin_nii._header)
        if outpath is None:
            outpath = origin_path
        nib.save(new_nii, outpath)
        if verbose:
            print(f'Used recentered affine for data in {origin_path} to create {outpath}')
        return 1 #returns 1 if it saved a new file
    else:
        shutil.copy(origin_path,outpath)
        return 0


def space_transpose(origin_path, transpose=[0,0,0], outpath=None):
    if outpath is None:
        outpath = origin_path
    origin_nii=nib.load(origin_path)
    newaffine = origin_nii._affine
    newaffine[:3,3] = transpose


def get_transpose(img):
    from nibabel import load
    chass_sym_nii = load(img)
    transpose = chass_sym_nii[:3, 3]
    return transpose


def recenter_affine(shape, affine, return_translation = False):

    origin=np.round([val/2 for val in shape])
    origin=origin[0:3]
    trueorigin=-origin + [1,1,1]

    newaffine=np.zeros([4,4])

    newaffine[0:3,0:3]=affine[0:3,0:3]
    newaffine[3,:]=affine[3,:]

    trueorigin = np.matmul(newaffine[0:3,0:3],trueorigin)
    newaffine[:3,3]=trueorigin

    if return_translation:
        translation = trueorigin - affine[3,0:3]
        translation_mat = np.eye(4)
        translation_mat[:3, 3] = translation
        return newaffine, translation, translation_mat
    else:
        return newaffine


def recenter_affine_test(shape, affine, return_translation = False):

    newaffine=np.zeros([4,4])

    newaffine[0:3,0:3]=affine[0:3,0:3]
    newaffine[3,:]=affine[3,:]

    #trueorigin = np.matmul(newaffine[0:3,0:3],trueorigin)

    signs = np.sign([newaffine[0, 0], newaffine[1, 1], newaffine[2, 2]])

    newaffine = np.eye(4)
    #axis_ratios = [np.abs(np.round(affine[0,0])), np.abs(np.round(affine[1,1])), np.abs(np.round(affine[2,2]))]
    axis_ratios = [np.abs(affine[0, 0]), np.abs(affine[1, 1]), np.abs(affine[2, 2])]
    newaffine[0,0] = signs[0] * axis_ratios[0]
    newaffine[1,1] = signs[1] * axis_ratios[1]
    newaffine[2,2] = signs[2] * axis_ratios[2]
    dct = {-1: 0, 1: 1}

    origin=np.round([val/2 for val in shape])
    origin = np.round([(val*axis_ratio) / (2) - axis_ratio+1 for val, axis_ratio in zip(shape, axis_ratios)])
    origin=origin[0:3]
    trueorigin=-origin
    trueorigin = signs * trueorigin
    trueorigin = trueorigin+[*map(dct.get, signs)]

    newaffine[:3,3]=trueorigin

    if return_translation:
        translation = trueorigin - affine[3,0:3]
        translation_mat = np.eye(4)
        translation_mat[:3, 3] = translation
        return newaffine, translation, translation_mat
    else:
        return newaffine


def recenter_nii_affine(img, return_translation = False):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    if return_translation:
        newaffine, translation, translation_mat = recenter_affine(np.shape(nii_data),affine, return_translation=True)
        return newaffine, translation, translation_mat
    else:
        newaffine = recenter_affine(np.shape(nii_data),affine, return_translation=False)
        return newaffine


def convert_ants_vals_to_affine(ants_vals):
    if np.size(ants_vals)==12:
        affine_mat = np.eye(4)
        affine_mat[:3,:3] = ants_vals[:9].reshape(3,3)
        affine_mat[:3,3] = np.squeeze(ants_vals[9:])
        negative_mat = np.ones([4,4])
        negative_mat[0:2,2:] = -1
        negative_mat[2,:2] = -1
        affine_mat = np.multiply(affine_mat, negative_mat) ## WHY THE F DO WE NEED TO DO THAT!!! WHAT IS ANTS DOOIIIING XD
    return(affine_mat)


def recenter_nii_save(img, output_path, return_translation = False, verbose=False):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = recenter_affine(np.shape(nii_data),affine)
    new_nii=nib.Nifti1Image(nii_data, newaffine)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')


def recenter_nii_save_pure(img, output_path, return_translation = False, verbose=False):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = np.eye(4)

    new_nii=nib.Nifti1Image(nii_data, newaffine)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')


def recenter_nii_save_test(img, output_path, return_translation = False, verbose=False):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = recenter_affine_test(np.shape(nii_data),affine)
    new_nii=nib.Nifti1Image(nii_data, newaffine)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')

def recenter_nii_save_test(img, output_path, return_translation = False, verbose=False):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = recenter_affine_test(np.shape(nii_data),affine)
    new_nii=nib.Nifti1Image(nii_data, newaffine)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')

"""
def recenter_nii_save_test(img, output_path, return_translation=False, verbose=False):

    if not os.path.exists(img):
        raise ('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise ('Could not load img at ' + img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = recenter_affine(np.shape(nii_data), affine)
    test_affine = np.eye(4)
    test_affine[:3, 3] = newaffine[:3, 3]
    xform = np.eye(4) * 1
    xform[:3, :3] = affine[:3, :3]
    signs = np.sign([newaffine[0, 0], newaffine[1, 1], newaffine[2, 2]])
    dct = {1: 0, -1: -2}
    signs = [*map(dct.get, signs)]
    neworigin = signs * newaffine[:3, 3] + [1,1,0]
    xform[:3, 3] = neworigin
    xform[:3, :3] = np.eye(3)
    xform[0,0] = -1
    xform[1,1] = -1
    new_nii = nib.Nifti1Image(nii_data, xform)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')
"""


def add_translation(img, output_path, translation, verbose):

    if not os.path.exists(img):
        raise('Nifti img file does not exists')

    try:
        nii = nib.load(img)
    except:
        raise('Could not load img at '+img)

    nii_data = nii.get_data()
    affine = nii._affine

    newaffine = affine
    newaffine[:3,3] = newaffine[:3,3] + translation
    new_nii=nib.Nifti1Image(nii_data, newaffine, nii.header)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')


def recenter_to_eye(nii,output_path,verbose=False):

    if isinstance(nii,str):
        nii=nib.load(nii)
    newaffine = np.eye(4)
    d = np.einsum('ii->i', newaffine)
    d[0:3] *= nii.header['pixdim'][1:4]
    # newaffine = recenter_affine(np.shape(new_data),newaffine)
    newaffine = recenter_affine_test(np.shape(nii.get_data()), newaffine)
    newaffine[:3, 3] += 0.1

    new_nii=nib.Nifti1Image(nii.get_data(), newaffine, nii.header)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)


def sameSigns(x, y):
    return ((float(x) * float(y)) > 0);


def img_transform_affreset(orig_path, affine_dwi, output_path=None):
    if output_path is None:
        output_path = orig_path.replace('.nii','reset.nii')
    affine_orig = nib.load(orig_path).affine
    orientation_out = 'RAS'
    orientation_in = ''
    if sameSigns(float(np.sum(affine_orig[0,:3])), np.sum(affine_dwi[0,:3])):
        orientation_in += 'R'
    else:
        orientation_in += 'L'
    if sameSigns(np.sum(affine_orig[1,:3]), np.sum(affine_dwi[1,:3])):
        orientation_in += 'A'
    else:
        orientation_in += 'P'
    if sameSigns(np.sum(affine_orig[2,:3]), np.sum(affine_dwi[2,:3])):
        orientation_in += 'S'
    else:
        orientation_in += 'I'
    img_transform_exec(orig_path, orientation_in, orientation_out, output_path = output_path)


def img_transform_exec(img, current_vorder, desired_vorder, output_path=None, write_transform=0, rename = True, recenter=False, recenter_test= False, recenter_eye=False, recenter_flipaffine=False, verbose=False):

    is_RGB = 0;
    is_vector = 0;
    is_tensor = 0;

    if not os.path.exists(img):
        raise('Nifti img file does not exists')
    for char in current_vorder:
        if char.islower():
            warnings.warn("Use uppercase for current order")
            current_vorder=current_vorder.upper()
    for char in desired_vorder:
        if char.islower():
            warnings.warn("Use uppercase for desired order")
            current_vorder=desired_vorder.upper()

    ordervals='RLAPSI'
    if not ordervals.find(current_vorder[0]) and not ordervals.find(current_vorder[1]) and not ordervals.find(current_vorder[2]):
        raise TypeError('Please use only R L A P S or I for current voxel order')

    if not ordervals.find(desired_vorder[0]) and not ordervals.find(desired_vorder[1]) and not ordervals.find(desired_vorder[2]):
        raise TypeError('Please use only R L A P S or I for desired voxel order')

    dirname, filename, ext = splitpath(img)
    if ext=='.nii.gz':
        filename = filename + ext
    else:
        filename = filename + "." + ext

    if rename:
        output_name = filename.replace('.nii', '_' + desired_vorder + '.nii')
    else:
        output_name = filename

    if output_path is None:
        output_path = os.path.join(dirname,output_name)
    if output_path.find('.')==-1:
        mkcdir(output_path)
        output_path = os.path.join(output_path,output_name)

    out_dir, _, _ = splitpath(output_path)
    affine_out = os.path.join(out_dir, current_vorder + '_to_' + desired_vorder + '_affine.pickle')

    overwrite = True;
    if os.path.isfile(output_path) and not overwrite and (not write_transform or (write_transform and os.path.exists(affine_out))):
        warnings.warn('Existing output:%s, not regenerating', output_path);

    orig_string = 'RLAPSI';
    flip_string = 'LRPAIS';
    orig_current_vorder = current_vorder;

    nii = nib.load(img)

    nii_data = nii.get_data()
    hdr = nii.header

    dims = nii.shape
    if np.size(dims) > 6:
        raise('Image has > 5 dimensions')
    elif np.size(dims) < 3:
        raise('Image has < 3 dimensions')

    new_data = nii_data
    affine = nii._affine
    vox_size = nii.header.get_zooms()[:3]

    if desired_vorder!=orig_current_vorder:
        if ((np.size(dims) > 4) and (dims(5) == 3)):
            is_vector = 1;
        elif ((np.size(dims) > 5) and (dims(5) == 6)):
            is_tensor = 1;

        #x_row = [1, 0, 0];
        #y_row = [0, 1, 0];
        #z_row = [0, 0, 1];
        x_row = affine[0,:]
        y_row = affine[1,:]
        z_row = affine[2,:]
        flipping = [1,1,1]
        xpos=desired_vorder.find(current_vorder[0])
        if xpos == -1:
            if verbose:
                print('Flipping first dimension')
            val=0
            new_data = np.flip(new_data, 0)
            orig_ind=orig_string.find(current_vorder[0])
            current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
            if is_vector:
                new_data[:,:,:,0,1]=-new_data[:,:,:,0,1]
            x_row = [-1 * val for val in x_row]
            flipping[0] = -1

        ypos=desired_vorder.find(current_vorder[1])
        if ypos == -1:
            if verbose:
                print('Flipping second dimension')
            val=1
            new_data = np.flip(new_data, 1)
            orig_ind=orig_string.find(current_vorder[1])
            current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
            if is_vector:
                new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
            y_row = [-1 * val for val in y_row]
            flipping[1] = -1


        zpos=desired_vorder.find(current_vorder[2])
        if zpos == -1:
            if verbose:
                print('Flipping third dimension')
            val=2
            new_data = np.flip(new_data, 2)
            orig_ind=orig_string.find(current_vorder[2])
            current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
            if is_vector:
                new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
            z_row = [-1 * val for val in z_row]
            flipping[2] = -1


        xpos = current_vorder.find(desired_vorder[0])
        ypos = current_vorder.find(desired_vorder[1])
        zpos = current_vorder.find(desired_vorder[2])


        if verbose:
            print(['Dimension order is:' + str(xpos) + ' ' + str(ypos) + ' ' + str(zpos)] )
        if not os.path.isfile(output_path) or overwrite:
            if np.size(dims) == 5:
                if is_tensor:
                    new_data = new_data.tranpose(xpos, ypos, zpos, 3, 4)
                else:
                    if is_vector:# =>> honestly looking at the original code, this doesnt really make sense to me, so deactivated for now. Will raise warning in case it happens
                        warnings.warn('is vector not properly implemented')
                        #    new[:,:,:,1,:] = new[:,:,:,1].transpose(xpos, ypos, zpos)
                        #new=new(:,:,:,[xpos, ypos, zpos]);
                    new_data.transpose(xpos, ypos, zpos, 3, 4)
            elif np.size(dims) == 4:
                if is_RGB:
                    ('is rgb not properly implemented')
                    #new=new(:,:,:,[xpos, ypos, zpos]);
                new_data = new_data.transpose(xpos, ypos, zpos, 3)
                new_vox_size = [0] * len(vox_size)
                new_vox_size = [vox_size[[xpos, ypos, zpos].index(x)] for x in sorted([xpos, ypos, zpos])]
            elif np.size(dims) == 3:
                new_data = new_data.transpose(xpos, ypos, zpos)
                new_vox_size = [0] * len(vox_size)
                new_vox_size = [vox_size[[xpos, ypos, zpos].index(x)] for x in sorted([xpos, ypos, zpos])]

        if not os.path.isfile(affine_out) and write_transform:
            intermediate_affine_matrix = [x_row , y_row, z_row];
            iam = intermediate_affine_matrix;
            affine_matrix_for_points = [iam[xpos,:], iam[ypos,:], iam[zpos,:]]
            affine_matrix_for_images = np.inv(affine_matrix_for_points)
            am4i = affine_matrix_for_images
            affine_matrix_string = [am4i[1,:] + am4i[2,:] + am4i[3,:] + '0 0 0']
            affine_fixed_string = ['0', '0', '0',];
            try:
                #write_affine_xform_for_ants(affine_out,affine_matrix_string,affine_fixed_string);
                #needs to be implemented if this is a desired functionality
                print("nope, not implemented")
            except:
                print("nope, not implemented")

    """
    if test is not None:
        newaffine = np.array([[0.045,      0., 0., 0.42525001],[0., 0.045, 0., 0.25920002],
        [0., 0.,0.045, 0.25920002], [0., 0., 0., 1.]])
        new_nii = nib.Nifti1Image(new_data, newaffine, hdr)
        test = str(test)
        nib.save(new_nii, test)
    """

    origin=affine[0:3,3]
    if desired_vorder != orig_current_vorder:
        trueorigin=origin*[x_row[0],y_row[1],z_row[2]]
        trueorigin[2]=trueorigin[2]*(-1)
    else:
        trueorigin = origin

    newaffine=np.zeros([4,4])

    newaffine[0:3,0:3]=affine[0:3,0:3]
    newaffine[3,:]=[0,0,0,1]
    newaffine[:3,3]=trueorigin

    #affine_transform = np.array([x_row, y_row, z_row, affine[3, :]])
    #affine_transform.transpose(xpos, ypos, zpos)
    if recenter:
        """
        newdims = np.shape(new_data)
        newaffine[0,3] = -(newdims[0] * newaffine[0,0]* 0.5)+0.045
        newaffine[1,3] = -(newdims[1] * newaffine[1,1]* 0.5)+0.045#+1
        newaffine[2,3] = -(newdims[2] * newaffine[2,2]* 0.5)+0.045
        """
        newaffine = recenter_affine(np.shape(new_data),newaffine)
    elif recenter_test:
        newaffine[:3,3] = origin * flipping
    elif recenter_eye:
        newaffine = np.eye(4)
        d = np.einsum('ii->i', newaffine)
        d[0:3] *= nii.header['pixdim'][1:4]
        #newaffine = recenter_affine(np.shape(new_data),newaffine)
        newaffine = recenter_affine_test(np.shape(new_data), newaffine)
        newaffine[:3,3] += 0.1
        #newaffine[0,:]=x_row
        #newaffine[1,:]=y_row
        #newaffine[2,:]=z_row
        #newhdr.srow_x=[newaffine[0,0:3]]
        #newhdr.srow_y=[newaffine[1,0:3]]
        #newhdr.srow_z=[newaffine[2,0:3]]
        #newhdr.pixdim=hdr.pixdim
    elif recenter_flipaffine:
        newaffine = affine_transform

    else:
        ## ADDED THIS ELSE OPTION FOR CONSISTENCY, MIGHT NEED TO SWITCH BACK AFTERWARDS IF OTHER STUFF BREAKS!!!!!
        newaffine = affine

    if new_vox_size!=vox_size:
        newaffine[:3,:3] = new_vox_size*(newaffine[:3,:3]/vox_size)

    new_nii=nib.Nifti1Image(new_data, newaffine, hdr)
    output_path = str(output_path)
    if verbose:
        print(f'Saving nifti file to {output_path}')
    nib.save(new_nii, output_path)
    if verbose:
        print(f'Saved')
    """
    #newnii.hdr.dime.intent_code = nii.hdr.dime.intent_code
    new_nii=nib.Nifti1Image(new, newaffine, newhdr)
    output_pathold=output_path
    output_path = str(output_path)
    output_path=output_path.replace('.nii', '_test.nii')
    nib.save(new_nii, output_path)
    output_path2=output_path.replace('.nii','_2.nii')
    new_nii_oldaffine=nib.Nifti1Image(new, affine, hdr)
    nib.save(new_nii_oldaffine,output_path2)
    #newnii.hdr.dime.intent_code = nii.hdr.dime.intent_code
    nib_test=nib.load(output_path)
    nib_test2=nib.load(output_path)
    nib_test_target=nib.load(output_pathold)
    hdr_test=nib_test._header
    hdr_test2=nib_test2._header
    hdr_target = nib_test_target._header
    print('hi')
    """


def recenter_file(input,output_path):
    if isinstance(input, str):
        image = nib.load(input)
    elif isinstance(input, nib.nifti1.Nifti1Image):
        image = input
    new_affine = recenter_affine(image.shape,image.affine)
    new_nii = nib.Nifti1Image(image._data,new_affine)
    nib.save(new_nii,output_path)

def recenter_affine(dims, affine):
    #newdims = np.shape(new_data)
    affine[0,3] = -(dims[0] * affine[0,0]* 0.5)+0.045
    affine[1,3] = -(dims[1] * affine[1,1]* 0.5)+0.045#+1
    affine[2,3] = -(dims[2] * affine[2,2]* 0.5)+0.045
    return affine


def new_voxels_filename(filename, current_vorder, desired_vorder):

    dirname, filename, ext = splitpath(output_path)
    filename=filename+"."+ext
    if output_path is None:
        output_name=filename.replace('.trk','_'+desired_vorder+'.trk')
        output_path = os.path.join(dirname,output_name)
    if not output_path.find('.'):
        mkcdir(output_path)
        output_name=filename.replace('.nii','_'+desired_vorder+'.nii')
        output_path = os.path.join(output_path,output_name)


def get_flip_affine(current_vorder, desired_vorder):

    for char in current_vorder:
        if char.islower():
            warnings.warn("Use uppercase for current order")
            current_vorder=current_vorder.upper()
    for char in desired_vorder:
        if char.islower():
            warnings.warn("Use uppercase for desired order")
            current_vorder=desired_vorder.upper()

    ordervals='RLAPSI'
    if not ordervals.find(current_vorder[0]) and not ordervals.find(current_vorder[1]) and not ordervals.find(current_vorder[2]):
        raise TypeError('Please use only R L A P S or I for current voxel order')

    if not ordervals.find(desired_vorder[0]) and not ordervals.find(desired_vorder[1]) and not ordervals.find(desired_vorder[2]):
        raise TypeError('Please use only R L A P S or I for desired voxel order')

    orig_string = 'RLAPSI';
    flip_string = 'LRPAIS';
    orig_current_vorder = current_vorder;

    #x_row = [1, 0, 0];
    #y_row = [0, 1, 0];
    #z_row = [0, 0, 1];
    affine = np.eye(4)
    x_row = affine[0,:]
    y_row = affine[1,:]
    z_row = affine[2,:]

    affine_temp = np.eye(4)

    xpos=desired_vorder.find(current_vorder[0])
    if xpos == -1:
        print('Flipping first dimension')
        val=0
        #new_data = np.flip(new_data, 0)
        orig_ind=orig_string.find(current_vorder[0])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,1]=-new_data[:,:,:,0,1]
        x_row = [-1 * val for val in x_row]
        affine_temp[0,:] = x_row

    ypos=desired_vorder.find(current_vorder[1])
    if ypos == -1:
        print('Flipping second dimension')
        val=1
        #new_data = np.flip(new_data, 1)
        orig_ind=orig_string.find(current_vorder[1])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        y_row = [-1 * val for val in y_row]
        affine_temp[1,:] = y_row


    zpos=desired_vorder.find(current_vorder[2])
    if zpos == -1:
        print('Flipping third dimension')
        val=2
        #new_data = np.flip(new_data, 2)
        orig_ind=orig_string.find(current_vorder[2])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        z_row = [-1 * val for val in z_row]
        affine_temp[2,:] = z_row

    xpos=current_vorder.find(desired_vorder[0])
    ypos=current_vorder.find(desired_vorder[1])
    zpos=current_vorder.find(desired_vorder[2])

    print(['Dimension order is:' + str(xpos) + ' ' + str(ypos) + ' ' + str(zpos)] )

    origin=affine[0:3,3]
    trueorigin=origin*[x_row[0],y_row[1],z_row[2]]
    #trueorigin[2]=trueorigin[2]*(-1)

    #affine_transform = np.array([x_row,y_row,z_row,affine[3,:]])
    affine_transform = np.array([affine_temp[xpos,:], affine_temp[ypos,:], affine_temp[zpos,:], affine[3, :]])

    newaffine=np.zeros([4,4])
    if not desired_vorder==orig_current_vorder:

        newaffine[0:3,0:3]=affine[0:3,0:3]
        newaffine[3,:]=[0,0,0,1]
        newaffine[:3,3]=trueorigin
        #newaffine[0,:]=x_row
        #newaffine[1,:]=y_row
        #newaffine[2,:]=z_row
        #newhdr.srow_x=[newaffine[0,0:3]]
        #newhdr.srow_y=[newaffine[1,0:3]]
        #newhdr.srow_z=[newaffine[2,0:3]]
        #newhdr.pixdim=hdr.pixdim
    else:
        newaffine=affine

    return affine_transform#, newaffine


def get_flip_bvecs(bvecs, current_vorder, desired_vorder, output_file=None, writeformat = 'line'):

    if isinstance(bvecs,str):
        from DTC.diff_handlers.bvec_handler import read_bvecs
        bvecs = read_bvecs(bvecs)

    for char in current_vorder:
        if char.islower():
            warnings.warn("Use uppercase for current order")
            current_vorder=current_vorder.upper()
    for char in desired_vorder:
        if char.islower():
            warnings.warn("Use uppercase for desired order")
            current_vorder=desired_vorder.upper()

    ordervals='RLAPSI'
    if not ordervals.find(current_vorder[0]) and not ordervals.find(current_vorder[1]) and not ordervals.find(current_vorder[2]):
        raise TypeError('Please use only R L A P S or I for current voxel order')

    if not ordervals.find(desired_vorder[0]) and not ordervals.find(desired_vorder[1]) and not ordervals.find(desired_vorder[2]):
        raise TypeError('Please use only R L A P S or I for desired voxel order')

    orig_string = 'RLAPSI';
    flip_string = 'LRPAIS';
    orig_current_vorder = current_vorder;

    x_row = bvecs[0,:]
    y_row = bvecs[1,:]
    z_row = bvecs[2,:]

    xpos=desired_vorder.find(current_vorder[0])
    if xpos == -1:
        print('Flipping first dimension')
        val=0
        #new_data = np.flip(new_data, 0)
        orig_ind=orig_string.find(current_vorder[0])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,1]=-new_data[:,:,:,0,1]
        x_row = [-1 * val for val in x_row]

    ypos=desired_vorder.find(current_vorder[1])
    if ypos == -1:
        print('Flipping second dimension')
        val=1
        #new_data = np.flip(new_data, 1)
        orig_ind=orig_string.find(current_vorder[1])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        y_row = [-1 * val for val in y_row]

    zpos=desired_vorder.find(current_vorder[2])
    if zpos == -1:
        print('Flipping third dimension')
        val=2
        #new_data = np.flip(new_data, 2)
        orig_ind=orig_string.find(current_vorder[2])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        z_row = [-1 * val for val in z_row]

    xpos=current_vorder.find(desired_vorder[0])
    ypos=current_vorder.find(desired_vorder[1])
    zpos=current_vorder.find(desired_vorder[2])

    bvecs_new = np.array([bvecs[xpos], bvecs[ypos], bvecs[zpos]])
    print(['Dimension order is:' + str(xpos) + ' ' + str(ypos) + ' ' + str(zpos)] )

    """
    origin=affine[0:3,3]
    trueorigin=origin*[x_row[0],y_row[1],z_row[2]]
    #trueorigin[2]=trueorigin[2]*(-1)

    affine_transform = np.array([x_row,y_row,z_row,affine[3,:]])

    newaffine=np.zeros([4,4])
    if not desired_vorder==orig_current_vorder:

        newaffine[0:3,0:3]=affine[0:3,0:3]
        newaffine[3,:]=[0,0,0,1]
        newaffine[:3,3]=trueorigin
        #newaffine[0,:]=x_row
        #newaffine[1,:]=y_row
        #newaffine[2,:]=z_row
        #newhdr.srow_x=[newaffine[0,0:3]]
        #newhdr.srow_y=[newaffine[1,0:3]]
        #newhdr.srow_z=[newaffine[2,0:3]]
        #newhdr.pixdim=hdr.pixdim
    else:
        newaffine=affine
    """
    if output_file is not None:
        from diff_handlers.bvec_handler import writebvec
        writebvec(bvecs_new, output_file, writeformat=writeformat, overwrite=True)
    return bvecs_new

def img_transform_exec_streamlines_defunct(trk_data, current_vorder, desired_vorder, output_path=None, write_transform=0, recenter=0):


    if isinstance(trk_data,str):
        trkpath = trk_data
        if os.path.exists(trk_data):
            trk_data = load_trk(trkpath)
        else:
            raise(f'Cannot find trk file at {trkpath}')
        if output_path is None:
            warnings.warn(f'Will overwrite previous trk file at {output_path}')
            output_path = trkpath
    else:
        if output_path is None:
            raise Exception("Output path for new trk file is not defined, abort")

    for char in current_vorder:
        if char.islower():
            warnings.warn("Use uppercase for current order")
            current_vorder=current_vorder.upper()
    for char in desired_vorder:
        if char.islower():
            warnings.warn("Use uppercase for desired order")
            current_vorder=desired_vorder.upper()

    ordervals='RLAPSI'
    if not ordervals.find(current_vorder[0]) and not ordervals.find(current_vorder[1]) and not ordervals.find(current_vorder[2]):
        raise TypeError('Please use only R L A P S or I for current voxel order')

    if not ordervals.find(desired_vorder[0]) and not ordervals.find(desired_vorder[1]) and not ordervals.find(desired_vorder[2]):
        raise TypeError('Please use only R L A P S or I for desired voxel order')

    out_dir, _, _ = splitpath(output_path)
    affine_out = os.path.join(out_dir, current_vorder + '_to_' + desired_vorder + '_affine.pickle')

    overwrite = True;
    if os.path.isfile(output_path) and not overwrite and (not write_transform or (write_transform and os.path.exists(affine_out))):
        warnings.warn('Existing output:%s, not regenerating', output_path);

    orig_string = 'RLAPSI';
    flip_string = 'LRPAIS';
    orig_current_vorder = current_vorder;

    if hasattr(trk_data, 'space_attribute'):
        header = trk_data.space_attribute
    elif hasattr(trk_data, 'space_attributes'):
        header = trk_data.space_attributes

    dims = trk_data.dimensions
    if np.size(dims) > 6:
        raise('Image has > 5 dimensions')
    elif np.size(dims) < 3:
        raise('Image has < 3 dimensions')

    streamlines = trk_data.streamlines

    if desired_vorder!=current_vorder:
        if ((np.size(dims) > 4) and (dims(5) == 3)):
            is_vector = 1;
        elif ((np.size(dims) > 5) and (dims(5) == 6)):
            is_tensor = 1;

    #x_row = [1, 0, 0];
    #y_row = [0, 1, 0];
    #z_row = [0, 0, 1];
    affine = trk_data.affine
    x_row = affine[0,:]
    y_row = affine[1,:]
    z_row = affine[2,:]

    xpos=desired_vorder.find(current_vorder[0])
    if xpos == -1:
        print('Flipping first dimension')
        val=0
        #new_data = np.flip(new_data, 0)
        orig_ind=orig_string.find(current_vorder[0])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,1]=-new_data[:,:,:,0,1]
        x_row = [-1 * val for val in x_row]

    ypos=desired_vorder.find(current_vorder[1])
    if ypos == -1:
        print('Flipping second dimension')
        val=1
        #new_data = np.flip(new_data, 1)
        orig_ind=orig_string.find(current_vorder[1])
        current_vorder = current_vorder[0:val] + flip_string[orig_ind] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        y_row = [-1 * val for val in y_row]

    zpos=desired_vorder.find(current_vorder[2])
    if zpos == -1:
        print('Flipping third dimension')
        val=2
        #new_data = np.flip(new_data, 2)
        orig_ind=orig_string.find(current_vorder[2])
        current_vorder = current_vorder[0:val] + flip_string[val] + current_vorder[val+1:]
        #if is_vector:
        #    new_data[:,:,:,0,2]=-new_data[:,:,:,0,2]
        z_row = [-1 * val for val in z_row]

    xpos=current_vorder.find(desired_vorder[0])
    ypos=current_vorder.find(desired_vorder[1])
    zpos=current_vorder.find(desired_vorder[2])

    print(['Dimension order is:' + str(xpos) + ' ' + str(ypos) + ' ' + str(zpos)] )

    if recenter:
        origin=np.round([val/2 for val in dims])
        origin=origin[0:3]
        trueorigin=origin*[x_row[0],y_row[1],z_row[2]]
        trueorigin[2]=trueorigin[2]*(-1)
    else:
        origin=affine[0:3,3]
        trueorigin=origin*[x_row[0],y_row[1],z_row[2]]
        #trueorigin[2]=trueorigin[2]*(-1)


    affine_transform = np.array([x_row,y_row,z_row,affine[3,:]])

    newaffine=np.zeros([4,4])
    newheader=header
    if not desired_vorder==orig_current_vorder:

        newaffine[0:3,0:3]=affine[0:3,0:3]
        newaffine[3,:]=[0,0,0,1]
        newaffine[:3,3]=trueorigin
        #newaffine[0,:]=x_row
        #newaffine[1,:]=y_row
        #newaffine[2,:]=z_row
        #newhdr.srow_x=[newaffine[0,0:3]]
        #newhdr.srow_y=[newaffine[1,0:3]]
        #newhdr.srow_z=[newaffine[2,0:3]]
        #newhdr.pixdim=hdr.pixdim
    else:
        newaffine=affine

    #newheader = list(newheader)
    #newheader[0] = newaffine
    #newheader = tuple(newheader)

    return affine_transform, newaffine
    """
    new_streamlines = transform_streamlines(streamlines, np.linalg.inv(affine_transform))

    if not os.path.isfile(output_path) or overwrite:
        newheader = create_tractogram_header(output_path, *newheader)
        trk_sl = lambda: (s for s in new_streamlines)
        save_trk_heavy_duty(output_path, streamlines=trk_sl,
                            affine=newaffine, header=newheader, return_tractogram=False)
    """