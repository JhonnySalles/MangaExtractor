import os
originalWorkingPath = os.getcwd()
import sys
sys.path.append("./lib_/SickZil-Machine/src/")

import tensorflow as tf
import core
import imgio
import utils.fp as fp
import cv2
import tensorflow as tf

import defaults
import limpeza as clean
import util
import alisamento as als
import scipy.ndimage
import math
import tensorflow as tf
import numpy as np
from furigana import RemoveFurigana


class TextSegmenation():
    def __init__(self, operation):
        pass
        self.operation = operation
        print("\n" + "Numbers of GPUs available: " + str(len(tf.config.list_physical_devices('GPU'))))
        # tf.reset_default_graph
        #core.load_model(defaults.SNETPATH, '0.1.0')
        #core.load_model(defaults.CNETPATH, '0.1.0')

    def imgpath2mask(self, imgpath):
        return fp.go(imgpath, lambda path: imgio.load(path, imgio.NDARR), core.segmap, imgio.segmap2mask)

    def resize(self, imgPath):
        # text resize by 1000px height
        img = cv2.imread(imgPath)
        size = 1000

        if img.shape[0] > size:
            img = cv2.resize(img, (int(size*img.shape[1]/img.shape[0]), size), interpolation=cv2.INTER_AREA)
            cv2.imwrite(imgPath, img)

    def segmentPage(self, imgPath, outputInpaintedPath, outputTextOnlyPath):
        with tf.device('/gpu:0'):  # Força a utilização da gpu
            # self.resize(imgPath)        #because of sickzil has poor quality on high resolution image

            # Processamento do Sickzil
            fileName = os.path.basename(imgPath)
            oriImage = imgio.load(imgPath, imgio.IMAGE)  # ori image
            maskImage = imgio.mask2segmap(self.imgpath2mask(imgPath))  # mask image
            # inpaintedImage = core.inpainted(oriImage, maskImage)        #notext image
            textOnlyImage = cv2.bitwise_and(
                oriImage, maskImage)  # text only image
            textOnlyImage[maskImage == 0] = 255
            #imgio.save(outputInpaintedPath+fileName, inpaintedImage)
            imgio.save(outputTextOnlyPath+fileName, textOnlyImage)

# Tratamentos de segmentação para remoção do furigana
##############################################################################
    def dimensions_2d_slice(self, s):
        x = s[1].start
        y = s[0].start
        w = s[1].stop-x
        h = s[0].stop-y
        return (x, y, w, h)

    def segment_image(self, img, max_scale=defaults.CC_SCALE_MAX, min_scale=defaults.CC_SCALE_MIN):
        (h, w) = img.shape[:2]

        binary = clean.binarize(img, threshold=defaults.BINARY_THRESHOLD)

        '''
      The necessary sigma needed for Gaussian filtering (to remove screentones and other noise) seems
      to be a function of the resolution the manga was scanned at (or original page size, I'm not sure).
      Assuming 'normal' page size for a phonebook style Manga is 17.5cmx11.5cm (6.8x4.5in).
      A scan of 300dpi will result in an image about 1900x1350, which requires a sigma of 1.5 to 1.8.
      I'm encountering many smaller images that may be nonstandard scanning dpi values or just smaller
      magazines. Haven't found hard info on this yet. They require sigma values of about 0.5 to 0.7.
      I'll therefore (for now) just calculate required (nonspecified) sigma as a linear function of vertical
      image resolution.
      '''
        sigma = (0.8/676.0)*float(h)-0.9
        gaussian_filtered = scipy.ndimage.gaussian_filter(img, sigma=sigma)
        gaussian_binary = clean.binarize(gaussian_filtered, threshold=defaults.BINARY_THRESHOLD)

        # Draw out statistics on average connected component size in the rescaled, binary image
        average_size = util.average_size(gaussian_binary)
        max_size = average_size*max_scale
        min_size = average_size*min_scale

        # primary mask is connected components filtered by size
        mask = util.form_mask(gaussian_binary, max_size, min_size)

        # secondary mask is formed from canny edges
        canny_mask = clean.form_canny_mask(gaussian_filtered, mask=mask)

        # final mask is size filtered connected components on canny mask
        final_mask = util.form_mask(canny_mask, max_size, min_size)

        # apply mask and return images
        cleaned = cv2.bitwise_not(final_mask * binary)
        text_only = self.cleaned2segmented(cleaned, average_size)

        if self.operation.furigana:
            furigana = RemoveFurigana(self.operation)
            furigana_mask = furigana.estimate_furigana(cleaned, text_only)
            furigana_mask = np.array(furigana_mask == 0, 'B')
            cleaned = cv2.bitwise_not(cleaned)*furigana_mask
            cleaned = cv2.bitwise_not(cleaned)
            text_only = self.cleaned2segmented(cleaned, average_size)

        (text_like_areas, nontext_like_areas) = self.filter_text_like_areas(
            img, segmentation=text_only, average_size=average_size)
        text_only = np.zeros(img.shape)
        util.draw_bounding_boxes(
            text_only, text_like_areas, color=(255), line_size=-1)

        segmented_image = np.zeros((h, w, 3), np.uint8)
        segmented_image[:, :, 0] = img
        segmented_image[:, :, 1] = text_only
        segmented_image[:, :, 2] = text_only
        return segmented_image

    def cleaned2segmented(self, cleaned, average_size):
        vertical_smoothing_threshold = defaults.VERTICAL_SMOOTHING_MULTIPLIER*average_size
        horizontal_smoothing_threshold = defaults.HORIZONTAL_SMOOTHING_MULTIPLIER*average_size
        (h, w) = cleaned.shape[:2]

        run_length_smoothed = als.RLSO(cv2.bitwise_not(cleaned), vertical_smoothing_threshold, horizontal_smoothing_threshold)
        components = util.get_connected_components(run_length_smoothed)
        text = np.zeros((h, w), np.uint8)
        #return text
        # ao que parece as linhas abaixo faz o desenho do contorno da imagem
        # verificar a real necessidade
        #text_columns = np.zeros((h,w),np.uint8)
        #text_rows = np.zeros((h,w),np.uint8)
        for component in components:
            default_value = 1  # Será necessário veririficar e adicionar um campo na tela para o valor do limiar de segmento
            seg_thresh = default_value
            (aspect, v_lines, h_lines) = util.segment_into_lines(cv2.bitwise_not(cleaned), component, min_segment_threshold=seg_thresh)
            if len(v_lines) < 2 and len(h_lines) < 2:
                continue

            util.draw_2d_slices(text, [component], color=255, line_size=-1)
            # ocr.draw_2d_slices(text_columns,v_lines,color=255,line_size=-1)
            # ocr.draw_2d_slices(text_rows,h_lines,color=255,line_size=-1)
        return text

    def filter_text_like_areas(self, img, segmentation, average_size):
        # see if a given rectangular area (2d slice) is very text like
        # First step is to estimate furigana like elements so they can be masked
        furigana = RemoveFurigana(self.operation)
        furigana_areas = furigana.estimate_furigana(img, segmentation)
        furigana_mask = np.array(furigana_areas == 0, 'B')

        # binarize the image, clean it via the segmentation and remove furigana too
        binary = clean.binarize(img, threshold=defaults.BINARY_THRESHOLD)

        segmentation_mask = np.array(segmentation != 0, 'B')
        cleaned = binary * segmentation_mask * furigana_mask
        inv_cleaned = cv2.bitwise_not(cleaned)

        areas = util.get_connected_components(segmentation)
        text_like_areas = []
        nontext_like_areas = []
        for area in areas:
            # if area_is_text_like(cleaned, area, average_size):
            if self.text_like_histogram(cleaned, area, average_size):
                text_like_areas.append(area)
            else:
                nontext_like_areas.append(area)

        return (text_like_areas, nontext_like_areas)

    def text_like_histogram(self, img, area, average_size):
        if not self.operation.furiganaFilter:
            return True
        (x, y, w, h) = self.dimensions_2d_slice(area)
        x_subimage = np.copy(img)
        x_histogram = np.zeros(w, int)
        y_subimage = np.copy(img)
        y_histogram = np.zeros(h, int)

        aoi = img[area]

        ccs = util.get_connected_components(aoi)
        if(len(ccs) < 2):
            return False

        #avg = average_size
        avg = util.average_size(aoi)
        mean_width = util.mean_width(aoi)
        mean_height = util.mean_height(aoi)

        # in a text area, the average size of a blob (cc) will reflect
        # that of the used characters/typeface. Thus if there simply aren't
        # enough pixels per character, we can drop this as a text candidate
        # note the following is failing in odd situations, probably due to incorrect
        # calculation of 'avg size'
        # TODO: replace testing against "average size" with testing against
        # hard thresholds for connected component width and height. i.e.
        # if they're all thin small ccs, we can drop this area

        # if avg < defaults.MINIMUM_TEXT_SIZE_THRESHOLD:
        if mean_width < defaults.MINIMUM_TEXT_SIZE_THRESHOLD or mean_height < defaults.MINIMUM_TEXT_SIZE_THRESHOLD:
            return False

        # check the basic aspect ratio of the ccs
        if mean_width/mean_height < 0.5 or mean_width/mean_height > 2:
            return False

        width_multiplier = float(avg)
        height_multiplier = float(avg)

        # gaussian filter the subimages in x,y directions to emphasise peaks and troughs
        x_subimage = scipy.ndimage.filters.gaussian_filter(x_subimage, (0.01*width_multiplier, 0))
        y_subimage = scipy.ndimage.filters.gaussian_filter(y_subimage, (0, 0.01*height_multiplier))

        # put together the histogram for black pixels over the x directon (along columns) of the component
        for i, col in enumerate(range(x, x+w)):
            black_pixel_count = np.count_nonzero(y_subimage[y:y+h, col])
            x_histogram[i] = black_pixel_count

        # and along the y direction (along rows)
        for i, row in enumerate(range(y, y+h)):
            black_pixel_count = np.count_nonzero(x_subimage[row, x:x+w])
            y_histogram[i] = black_pixel_count

        h_white_runs = self.get_white_runs(x_histogram)
        num_h_white_runs = len(h_white_runs)
        h_black_runs = self.get_black_runs(x_histogram)
        num_h_black_runs = len(h_black_runs)
        (h_spacing_mean, h_spacing_variance) = self.slicing_list_stats(h_white_runs)
        (h_character_mean, h_character_variance) = self.slicing_list_stats(h_black_runs)
        v_white_runs = self.get_white_runs(y_histogram)
        num_v_white_runs = len(v_white_runs)
        v_black_runs = self.get_black_runs(y_histogram)
        num_v_black_runs = len(v_black_runs)
        (v_spacing_mean, v_spacing_variance) = self.slicing_list_stats(v_white_runs)
        (v_character_mean, v_character_variance) = self.slicing_list_stats(v_black_runs)

        if num_h_white_runs < 2 and num_v_white_runs < 2:
            return False

        if v_spacing_variance > defaults.MAXIMUM_VERTICAL_SPACE_VARIANCE:
            return False

        if v_character_mean < avg*0.5 or v_character_mean > avg*2.0:
            pass
            # return False
        if h_character_mean < avg*0.5 or h_character_mean > avg*2.0:
            pass
            # return False

        return True

    def get_black_runs(self, histogram):
        (labeled_array, num_features) = scipy.ndimage.measurements.label(histogram)
        return scipy.ndimage.measurements.find_objects(labeled_array)

    def get_white_runs(self, histogram):
        inverse_histogram = np.zeros(histogram.shape)
        inverse_histogram = np.where(histogram != 0, inverse_histogram, 1)
        return self.get_black_runs(inverse_histogram)

    def slicing_list_stats(self, slicings):
        widths = []
        for slicing in slicings:
            widths.append(slicing[0].stop-slicing[0].start)
        mean = 0
        variance = 0
        if len(widths) > 0:
            mean = np.mean(widths)
            variance = np.std(widths)
        return (mean, variance)

# Comentado a chamada, verificar se irá ser necessário
    def area_is_text_like(self, img, area, average_size):
        # use basic 'ladder' building technique to see if area features somewhat
        # regularly spaced vertical japanese characters
        # this is done by attempting to draw a regular grid in the area, and converging on
        # the grid dimension (cells are square) that minimizes the number of back pixels at the boundaries
        # We should also count X black pixels at multiple boundaries as worse than X black pixels at one
        (image_h, image_w) = img.shape[:2]
        (x, y, w, h) = self.dimensions_2d_slice(area)

        # get the average size (width, height?) of connected components in the area of interest
        aoi = img[area]
        #ccs = cc.get_connected_components(aoi)
        aoi_average_size = util.average_size(aoi)
        if math.isnan(aoi_average_size):
            return False

        # if possible,expand the area by one pixel in all directions, which should be white pixels
        if(x > 0 and x+w < image_w-1):
            x = x-1
            w = w+2
        if(y > 0 and y+h < image_h-1):
            y = y-1
            h = h+2

        # TODO: get the average connected component WIDTH and HEIGHT (not just size) of just
        # elements within this area. Use THAT to form ranges over which we'll try to create ladders

        # if w<average_size and h<average_size:
        #  return False

        initial_height = int(aoi_average_size/2)
        final_height = int(aoi_average_size * 1.5)
        initial_width = int(aoi_average_size/2)
        final_width = int(aoi_average_size * 2.0)
        #if w<h:final_height=w
        minimum_black_pixel_count_height = w*h
        minimum_height = initial_height
        minimum_black_pixel_count_width = w*h
        minimum_width = initial_width

        # TODO: vary width and height independently. Only way we'll find decent correct segmentation
        # TODO: start the ladder (grid) outside the area so it wont' always 'hit' black pixels for the
        # zeroeth row and column

        for s in range(initial_height, final_height):
            black_pixel_count = 0
            #horizontal_steps = int(w/s)+1
            #vertical_steps = int(h/s)+1
            num_steps = int(h/s)+1
            for vertical_step in range(0, num_steps):
                # cound black pixels along horizontal, vertically stepped lines
                # we can count black pixels with "nonzero" because we're using an inverse image
                black_pixel_count = black_pixel_count + np.count_nonzero(img[y+vertical_step*s, x:x+w])
            if black_pixel_count < minimum_black_pixel_count_height:
                minimum_black_pixel_count_height = black_pixel_count
                minimum_height = s

        for s in range(initial_width, final_width):
            black_pixel_count = 0
            #horizontal_steps = w/s+1
            #vertical_steps = h/s+1
            num_steps = int(w/s)+1
            for horizontal_step in range(0, num_steps):
                # count black pixels along vertical, horizontally stepped lines
                #height = vertical_steps*s
                black_pixel_count = black_pixel_count + np.count_nonzero(img[y:y+h, x+horizontal_step*s])
            if black_pixel_count < minimum_black_pixel_count_width:
                minimum_black_pixel_count_width = black_pixel_count
                minimum_width = s
        # print 'at location ' + str(x) + ' ' + str(y) + ' ' + str(w) + ' ' + str(h)
        # print 'found minimum cell height ' + str(minimum_height) + ' with black pixel count ' + str(minimum_black_pixel_count)

        # draw the finalized grid on our img
        num_horizontal_steps = int(w/minimum_width)+1
        if (num_horizontal_steps-1) * minimum_width < (w-minimum_width/4):
            # print 'increading width steps count by one'
            num_horizontal_steps = num_horizontal_steps + 1
        total_width = (num_horizontal_steps-1) * minimum_width
        num_vertical_steps = int(h/minimum_height)+1
        if (num_vertical_steps-1) * minimum_height < (h-minimum_height/4):
            # print 'increasing height steps count by one'
            num_vertical_steps = num_vertical_steps + 1
        total_height = (num_vertical_steps-1) * minimum_height
        # print 'height is ' + str(h) + ' and total line height is ' + str(total_height)
        # print 'number of steps is ' + str(num_vertical_steps) + ' and num_cells*min height ' + str(num_vertical_steps*minimum_height)
        for vertical_step in range(0, num_vertical_steps):
            # pass
            img[y+vertical_step*minimum_height, x:x+total_width] = 255
        for horizontal_step in range(0, num_horizontal_steps):
            # pass
            img[y:y+total_height, x+horizontal_step*minimum_width] = 255
        '''
      img[y,x:x+w]=255
      img[y+h,x:x+w]=255
      img[y:y+h,x]=255
      img[y:y+h,x+w]=255

      img[y,x:x+total_width]=255
      img[y+total_height,x:x+total_width]=255
      img[y:y+total_height,x]=255
      img[y:y+total_height,x+total_width]=255
      '''

        return True

    def segmentFurigana(self, imgPath, outputFuriganaPath):
        fileName = os.path.basename(imgPath)
        img = cv2.imread(imgPath)
        gray = clean.grayscale(img)

        binary = clean.binarize(gray, threshold=defaults.BINARY_THRESHOLD)

        segmented_image = self.segment_image(gray)
        cv2.imwrite(outputFuriganaPath + fileName + '_segmentacao.png', segmented_image)
        segmented_image = segmented_image[:, :, 2]
        segmentation_mask = np.array(segmented_image != 0, 'B')
        cleaned = cv2.bitwise_not(binary*segmentation_mask)
        
        return gray, cleaned, segmented_image
