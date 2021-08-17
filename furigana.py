import numpy as np
import cv2
import scipy.ndimage
import os
import util
import limpeza as clean
import defaults

class RemoveFurigana():
  def __init__(self, operacao):
      pass
      self.operacao = operacao

  def binary_mask(self, mask):
      return np.array(mask!=0,'B')

  def cc_center(self, component):
      x_center = component[1].start+(component[1].stop-component[1].start)/2
      y_center = component[0].start+(component[0].stop-component[0].start)/2
      return (x_center, y_center)

  def is_in_component(self, row, col, component):
      return (row >= component[0].start and row <= component[0].stop
        and col >= component[1].start and col <= component[1].stop)

  def cc_width(self, component):
      return component[1].stop-component[1].start

  def intersects_other_component(self, row, col, component, components):
      for c in components:
        if c is component: continue
        if self.is_in_component(row, col, c):return c
      return None

  def find_cc_to_left(self, component, components, max_dist=20):
      (c_col, c_row) = self.cc_center(component)
      left_col = c_col-int(max_dist)
      if left_col<0:left_col=0
      for col in reversed(range(int(left_col),int(c_col))):
        c = self.intersects_other_component(c_row, col, component, components)
        if c is not None:
          #print 'got hit from center ' + str(c_col) + ','+str(c_row) + 'at ' + str(col) + ',' + str(c_row)
          return c
      return None

  def estimate_furigana(self, img, segmentation):
      (w,h)=img.shape[:2]

      text_areas = segmentation

      #form binary image from grayscale
      binary = clean.binarize(img,threshold=defaults.BINARY_THRESHOLD)

      binary_average_size = util.average_size(binary)

      #apply mask and return images
      text_mask = self.binary_mask(text_areas)
      cleaned = cv2.bitwise_not(text_mask*binary)
      cleaned_average_size = util.average_size(cleaned)

      columns = scipy.ndimage.filters.gaussian_filter(cleaned,(defaults.FURIGANA_VERTICAL_SIGMA_MULTIPLIER*binary_average_size,defaults.FURIGANA_HORIZONTAL_SIGMA_MULTIPLIER*binary_average_size))
      columns = clean.binarize(columns,threshold=defaults.FURIGANA_BINARY_THRESHOLD)
      furigana = columns*text_mask

      #go through the columns in each text area, and:
      #1) Estimate the standard column width (it should be similar to the average connected component width)
      #2) Separate out those columns which are significantly thinner (>75%) than the standard width
      boxes = util.get_connected_components(furigana)
      furigana_lines = []
      non_furigana_lines = []
      lines_general = []
      for box in boxes:
        line_width = self.cc_width(box)
        line_to_left = self.find_cc_to_left(box, boxes, max_dist=line_width*defaults.FURIGANA_DISTANCE_MULTIPLIER)
        if line_to_left is None:
          non_furigana_lines.append(box)
          continue

        left_line_width = self.cc_width(line_to_left)
        if line_width < left_line_width * defaults.FURIGANA_WIDTH_THRESHOLD:
          furigana_lines.append(box)
        else:
          non_furigana_lines.append(box)

      furigana_mask = np.zeros(furigana.shape)
      for f in furigana_lines:
        furigana_mask[f[0].start:f[0].stop,f[1].start:f[1].stop]=255
        #furigana_mask[f]=1

      furigana = furigana_mask #furigana * furigana_mask

      #if arg.boolean_value('debug'):
      #  furigana = 0.25*(columns*text_mask) + 0.25*img + 0.5*furigana

      return furigana

  def removeFurigana(self, imgPath, imgSegment, outputTextOnlyPath, outputFuriganaPath):
      fileName=os.path.basename(imgPath)
      img = cv2.imread(imgPath)
      gray = clean.grayscale(img)

      furigana_areas = self.estimate_furigana(gray,imgSegment)
      furigana_mask = np.array(furigana_areas==0,'B')
      cleaned = cv2.bitwise_not(cv2.bitwise_not(img)*furigana_mask)

      cv2.imwrite(outputFuriganaPath + fileName + 'furigana.png', furigana_mask)
      cv2.imwrite(outputTextOnlyPath + fileName, cleaned)


