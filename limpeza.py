import numpy as np
import cv2
import scipy.ndimage
import util
import defaults


def clean_page(img, max_scale=defaults.CC_SCALE_MAX, min_scale=defaults.CC_SCALE_MIN):
  #img = cv2.imread(sys.argv[1])
  (h,w,d)=img.shape

  gray = grayscale(img)

  #create gaussian filtered and unfiltered binary images
  gaussian_filtered = scipy.ndimage.gaussian_filter(gray, sigma=defaults.GAUSSIAN_FILTER_SIGMA)
  gaussian_binary = binarize(gaussian_filtered, threshold=defaults.BINARY_THRESHOLD)
  binary = binarize(gray, threshold=defaults.BINARY_THRESHOLD)

  #Draw out statistics on average connected component size in the rescaled, binary image
  average_size = util.average_size(gaussian_binary)
  #print('Initial mask average size is ' + str(average_size))
  max_size = average_size*max_scale
  min_size = average_size*min_scale

  #primary mask is connected components filtered by size
  mask = util.form_mask(gaussian_binary, max_size, min_size)

  #secondary mask is formed from canny edges
  canny_mask = form_canny_mask(gaussian_filtered, mask=mask)

  #final mask is size filtered connected components on canny mask
  final_mask = util.form_mask(canny_mask, max_size, min_size)

  #apply mask and return images
  cleaned = cv2.bitwise_not(final_mask * binary)
  return (cv2.bitwise_not(binary), final_mask, cleaned)

def grayscale(img):
  gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  #adjust histogram to maximize black/white range (increase contrast, decrease brightness)??
  #gray = cv2.equalizeHist(gray)
  return gray

def binarize(img, threshold=190, white=255):
  (t,binary) = cv2.threshold(img, threshold, white, cv2.THRESH_BINARY_INV )
  return binary

def form_canny_mask(img, mask=None):
  edges = cv2.Canny(img, 128, 255, apertureSize=3)
  if mask is not None:
    mask = mask*edges
  else:
    mask = edges
  contours,hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

  temp_mask = np.zeros(img.shape,np.uint8)
  for c in contours:
    #also draw detected contours into the original image in green
    #cv2.drawContours(img,[c],0,(0,255,0),1)
    hull = cv2.convexHull(c)
    cv2.drawContours(temp_mask,[hull],0,255,-1)
    #cv2.drawContours(temp_mask,[c],0,255,-1)
    #polygon = cv2.approxPolyDP(c,0.1*cv2.arcLength(c,True),True)
    #cv2.drawContours(temp_mask,[polygon],0,255,-1)
  return temp_mask
