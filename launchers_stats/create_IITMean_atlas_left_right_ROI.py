import os
import numpy as np
import nibabel as nib

base_folder ='/Volumes/Data/Badea/Lab/atlases/IITmean_RPI/'
output_folder = '/Volumes/Data/Badea/Lab/atlases/IITmean_RPI/'

#fa_masked = '/Volumes/Data/Badea/Lab/atlases/IITmean_RPI/IITmean_RPI_fa.nii.gz'

#mask_left = '/Volumes/Data/Badea/Lab/atlases/IITmean_RPI/IITmean_RPI_mask_left.nii.gz'
#mask_right = '/Volumes/Data/Badea/Lab/atlases/IITmean_RPI/IITmean_RPI_mask_right.nii.gz'

base_image = '/Volumes/Data/Badea/Lab/mouse/VBM_21ADDecode03_IITmean_RPI_fullrun-work/dwi/SyN_0p5_3_0p5_fa/faMDT_NoNameYet_n37_i6/median_images/MDT_fa.nii.gz'
output_folder = '/Volumes/Data/Badea/Lab/mouse/VBM_21ADDecode03_IITmean_RPI_fullrun-results/atlas_to_MDT'

full_mask_path = os.path.join(output_folder, 'IITmean_RPI_MDT_mask.nii.gz')
right_mask_path = os.path.join(output_folder, 'IITmean_RPI_MDT_mask_right.nii.gz')
left_mask_path = os.path.join(output_folder, 'IITmean_RPI_MDT_mask_left.nii.gz')

base_nii = nib.load(base_image)
base_affine = base_nii.affine
base_data = base_nii.get_fdata()

mask = np.zeros(np.shape(base_data))
mask_right = np.zeros(np.shape(base_data))
mask_left = np.zeros(np.shape(base_data))

mask[base_data>0] = 1
mask_right[base_data>0] = 1
mask_left[base_data>0] = 1

mask_right[0:(base_data.shape[0] // 2),:,:] = 0
mask_left[(base_data.shape[0] // 2):,:,:] = 0

mask_nii = nib.Nifti1Image(mask, base_affine)
nib.save(mask_nii, full_mask_path)

maskl_nii = nib.Nifti1Image(mask_left, base_affine)
nib.save(maskl_nii, left_mask_path)

maskr_nii = nib.Nifti1Image(mask_right, base_affine)
nib.save(maskr_nii, right_mask_path)