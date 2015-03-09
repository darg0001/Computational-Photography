from scipy import ndimage
import numpy as np
import poissonBlending

if __name__=="__main__":
	src=ndimage.imread('samples/penguin_aligned.jpg')
	tgt=ndimage.imread('samples/im2_small.JPG')
	mask_img=ndimage.imread('samples/penguin_mask.jpg')

	mask=np.zeros(mask_img.shape,dtype=bool)
	for i in range(mask_img.shape[0]):
		for j in range(mask_img.shape[1]):
			if mask_img[i,j]>0:
				mask[i,j]=True
			else:
				mask[i,j]=False

	#Calculate Poisson Blend in 3 color channels
	vRed=poissonBlending.poissonBlend(src[:,:,0],tgt[:,:,0],mask)
	vGreen=poissonBlending.poissonBlend(src[:,:,1],tgt[:,:,1],mask)
	vBlue=poissonBlending.poissonBlend(src[:,:,2],tgt[:,:,2],mask)

	finalImage=np.dstack([vRed,vGreen,vBlue])
