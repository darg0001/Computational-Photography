#Based on Debevec and Malik (SIGGRAPH 1997), 
#"Recovering High Dynamic Range Radiance Maps from Photographs"
#we use this for calculating radiance maps for entire images
#using the response function we calculate based on a smaller subsample of the image

import numpy as np
import math as math

#minimum, maximum RGB color values
Zmin = 0
Zmax = 255

n = 256

#arguments:
#Z[i,j]: pixel values of of pixel location number i in image j
#B[j]: log delta t, or log shutter speed, for image j
#w[Z[i,j]]: weights for different pixel values
#g[Z[i,j]]: response function (vector of function values for all pixel values between Zmin and Zmax)

#returns:
#E(i) a HDR radiance map

#note: each "image" is one RGB channel of an image, as in the paper

def create_map(rFunc,images,exposures,weights,numRowsInImage,numColsInImage):
	numPixels = images.shape[0]
	numImages = images.shape[1]
	#High dynamic range radiance map
	#hdrMap is an array of with as many entries as there are pixels in any of our images
	#one entry corresponds to the HDR value of a given pixel in the radiance map
	hdrMap = list()
	
	#fill in each entry of the HDR radiance map
	for pixel in range(0,numPixels):
		num = 0
		denom = 0
		
		#use pixel values for a given pixel from all the images
		#difference between response function and exposure, weighted appropriately(?)
		for image in range(0,numImages):
			num += weights[imagesl[pixel,image]]*(rFunc[images[pixel,image]] - exposures[image])
			denom += weights[images[pixel,image]]
		
		lnEi = num/denom
		hdrMap.append(math.exp(lnEi))
	hdrMap = np.reshape(hdrMap, (numRowsInImage, numColsInImage))
	return hdrMap
	


	