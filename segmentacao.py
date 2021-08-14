import os
originalWorkingPath=os.getcwd()
import sys
sys.path.append("./lib_/SickZil-Machine/src/")
#Dentro do arquivo consts core está com o caminho fixo para SNETPATH e CNETPATH
import core
import imgio
import utils.fp as fp
import numpy as np
import cv2
from tqdm import tqdm
import consts
import tensorflow as tf

class TextSegmenation():
    def __init__(self, ):
        pass
        print("Números de GPUs disponíveis: ", len(tf.config.list_physical_devices('GPU')))
        #tf.reset_default_graph
        #core.load_model(consts.SNETPATH, '0.1.0')
        #core.load_model(consts.CNETPATH, '0.1.0')
    
    def imgpath2mask(self, imgpath):
        return fp.go(
            imgpath,
            lambda path: imgio.load(path, imgio.NDARR),     
            core.segmap,
            imgio.segmap2mask)

    def resize(self,imgPath):
        #text resize by 1000px height 
        img = cv2.imread(imgPath)
        size=1000
        if img.shape[0]>size:
            img = cv2.resize(img, (int(size*img.shape[1]/img.shape[0]),size), interpolation = cv2.INTER_AREA)
            cv2.imwrite(imgPath, img) 

    def segmentPage(self,imgPath,outputInpaintedPath,outputTextOnlyPath):
        with tf.device('/gpu:0'): #Força a utilização da gpu
            #self.resize(imgPath)        #because of sickzil has poor quality on high resolution image

            #Processamento do Sickzil
            fileName=os.path.basename(imgPath)
            oriImage = imgio.load(imgPath, imgio.IMAGE)                      #ori image
            maskImage  = imgio.mask2segmap(self.imgpath2mask(imgPath))        #mask image
            #inpaintedImage = core.inpainted(oriImage, maskImage)        #notext image
            textOnlyImage= cv2.bitwise_and(oriImage,maskImage)         #text only image
            textOnlyImage[maskImage==0] = 255                     
            #imgio.save(outputInpaintedPath+fileName, inpaintedImage)
            imgio.save(outputTextOnlyPath+fileName, textOnlyImage)

