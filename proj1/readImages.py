#Based on Debevec and Malik (SIGGRAPH 1997), 
#"Recovering High Dynamic Range Radiance Maps from Photographs"
from scipy import ndimage
import numpy as np
import math
import random
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors
from rfsolver import rfsolve
from estimateNoise import *
from imageMatricesToHDR import *

numNoiseSamples = 100 #how many samples to take from each RGB channel of each image to estimate noise
n = 256 #number of possible RGB values
Zmin = 0 #minimum possible RGB value
Zmax = 255 #maximum possible RGB value
Zmid = (Zmin+Zmax)/2 #halfway between min and max possible values
samplingMethod = "intensity" #which method to sample pixels for construction of response curve

#returns red,green,blue pixel values from images files at different exposure times
#also generates the ln(delta_t) array and the weight array
#pixel values are sampled at random points in the image
#dirName: directory containing the images
#txtFile: text file stating the image file names and the exposure times
#numSamples: number of pixels to sample from each image
#returns the tuple (zRed,zGreen,zBlue,B,w,finalRed,finalGreen,finalBlue,imHeight,imWidth,meanNoiseValue)
#zRed: red channel sampled pixel values with dimensions (numSamples,numImages)
#zGreen: green channel sampled pixel values with dimensions (numSamples,numImages)
#zBlue: blue channel sampled pixel values with dimensions (numSamples,numImages)
#B: array of log of exposure time
#w: array of weights
#finalRed: red channel original pixel values with dimensions (numPixels,numImages)
#finalGreen: green channel original pixel values with dimensions (numPixels,numImages)
#finalBlue: blue channel original pixel values with dimensions (numPixels,numImages)
#imHeight: height of image
#imWidth: width of image
#meanNoiseValue: mean noise value in image
def getPixelArrayFromFiles(dirName,txtFile,numSamples):
	f=open(dirName+'/'+txtFile)
	f.readline()
	f.readline()
	f.readline()
	numImages=0
	numPixels=0
	B=[]
	zRed=[]
	zGreen=[]
	zBlue=[]
	finalRed=[]
	finalGreen=[]
	finalBlue=[]
	imWidth=0
	imHeight=0
	pixelSamples=set()
	
	#noise values of all channels of all images
	noiseValues = []
	
	#for each image in the file
	for s in f:
		sArray=s.split(' ')
		imFile=sArray[0].replace('.ppm','.png')
		exposureTime=math.log(1/float(sArray[1]))
		B.append(exposureTime)
		imArr=ndimage.imread(dirName+'/'+imFile)
		
		#get channels of each image
		imRed=imArr[:,:,0]
		imGreen=imArr[:,:,1]
		imBlue=imArr[:,:,2]
		
		#estimate noisiness of the channel
		meanRedNoise = estimateNoise(imRed,numNoiseSamples)
		meanGreenNoise = estimateNoise(imGreen,numNoiseSamples)
		meanBlueNoise = estimateNoise(imBlue,numNoiseSamples)
		
		noiseValues.append(meanRedNoise)
		noiseValues.append(meanGreenNoise)
		noiseValues.append(meanBlueNoise)
		
		if len(pixelSamples)==0:
			imWidth=imRed.shape[1]
			imHeight=imRed.shape[0]
			imSize=imRed.shape[0]*imRed.shape[1]
			imIntensity=matplotlib.colors.rgb_to_hsv(np.dstack((1.0*imRed/255,1.0*imGreen/255,1.0*imBlue/255)))[:,:,2]
			pixelSamples=getSamplingDomain(imIntensity,numSamples,imSize)
		imRed1D=[]
		imGreen1D=[]
		imBlue1D=[]
		for i in pixelSamples:
			imRed1D.append(imRed[i%imRed.shape[0],i/imRed.shape[0]])
			imGreen1D.append(imGreen[i%imGreen.shape[0],i/imGreen.shape[0]])
			imBlue1D.append(imBlue[i%imBlue.shape[0],i/imBlue.shape[0]])
		finalRed.append(np.mat(imRed).A1)
		finalGreen.append(np.mat(imGreen).A1)
		finalBlue.append(np.mat(imBlue).A1)
		zRed.append(imRed1D)
		zGreen.append(imGreen1D)
		zBlue.append(imBlue1D)
		numImages+=1
		numPixels+=numSamples
		
	f.close()
	
	B=np.array(B)
	zRed=np.transpose(np.array(zRed))
	zGreen=np.transpose(np.array(zGreen))
	zBlue=np.transpose(np.array(zBlue))
	finalRed=np.transpose(np.array(finalRed))
	finalGreen=np.transpose(np.array(finalGreen))
	finalBlue=np.transpose(np.array(finalBlue))
	
	#calculate average noise value across all images and all channels
	#use to see how large we want smoothness parameter lambda to be
	#(idea: more noise: want more emphasis on smoothness)
	meanNoiseValue = sum(noiseValues)/float(len(noiseValues))
#	print "mean sum of squared noise value in our set of images: ", meanNoiseValue
	
	#calculate weights
	w=np.ones((n,1))
	for i in range(0,n):
		if i<=Zmid:
			w[i]=i-Zmin
		else:
			w[i]=Zmax-i
	return zRed,zGreen,zBlue,B,w,finalRed,finalGreen,finalBlue,imHeight,imWidth,meanNoiseValue

#returns an array of sample locations for sampling pixels
#imIntensity: intensity of each pixel in the each
#numSamples: number of samples to take
#imSize: number of pixels in the image
#the method used is based on the variable 'samplingMethod'
def getSamplingDomain(imIntensity,numSamples,imSize):
	x=[]
	y=[]
	intensityDict={}
	for i in range(0,imIntensity.shape[0]):
		for j in range(0,imIntensity.shape[1]):
			if imIntensity[i,j] not in intensityDict:
				intensityDict[imIntensity[i,j]]=(i,j)
			elif imIntensity[i,j] in intensityDict:
				if random.randint(0,100)==0:
					intensityDict[imIntensity[i,j]]=(i,j)
	pixelSamples=[]
	if samplingMethod=="random":
		while len(pixelSamples)<numSamples:
			i=random.randint(0,imSize-1)
			pixelSamples.append(i)
			x.append(i/imIntensity.shape[0])
			y.append(i%imIntensity.shape[0])
	elif samplingMethod=="intensity":
		for i in intensityDict:
			x.append(intensityDict[i][1])
			y.append(intensityDict[i][0])
			pixelSamples.append(intensityDict[i][0]+intensityDict[i][1]*imIntensity.shape[0])
	elif samplingMethod=="location":
		increment=imIntensity.shape[0]*imIntensity.shape[1]/numSamples
		for i in range(0,numSamples):
			x.append(i*increment/imIntensity.shape[0])
			y.append((i*increment)%imIntensity.shape[0])
			pixelSamples.append(i*increment)
	if __name__=="__main__":
		plt.imshow(imIntensity,cmap=cm.Greys_r)
		plt.plot(x,y,'r.')
		plt.title('Sample Locations')
		plt.figure()
	return pixelSamples

#generates a plot of pixel value, z against the function g(z)
#color: determines the color of the plot
def plotZandG(z,g,color):
	xx=np.zeros(z.shape[0]*z.shape[1])
	yy=np.zeros(z.shape[0]*z.shape[1])
	k=0
	for i in range(0,z.shape[0]):
		for j in range(0,z.shape[1]):
			xx[k]=g[z[i,j]]
			yy[k]=z[i,j]
			k=k+1
	plt.plot(xx,yy,color)


if __name__=="__main__":
	zRed,zGreen,zBlue,B,w,finalRed,finalGreen,finalBlue,imHeight,imWidth,meanNoiseValue = getPixelArrayFromFiles('images','Canal.txt',100)
	l = smoothness(meanNoiseValue,imHeight,imWidth)
	gRed,eRed=rfsolve(zRed,B,l,w,16)
	gGreen,eGreen=rfsolve(zGreen,B,l,w,16)
	gBlue,eBlue=rfsolve(zBlue,B,l,w,16)
	plotZandG(zRed,gRed,'rx')
	plotZandG(zGreen,gGreen,'gx')
	plotZandG(zBlue,gBlue,'bx')
	plt.axis([-10,5,0,260])
	plt.xlabel('log exposure X')
	plt.ylabel('pixel value Z')
	plt.title('Response curve')
	plt.show()
