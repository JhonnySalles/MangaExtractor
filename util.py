import numpy as np
import scipy.ndimage
from pylab import zeros, amax, median
import cv2


def area_bb(a):
    return np.prod([max(x.stop-x.start, 0) for x in a[:2]])


def width_bb(a):
    return a[1].stop-a[1].start


def height_bb(a):
    return a[0].stop-a[0].start


def area_nz(slice, image):
    return np.count_nonzero(image[slice])


def get_connected_components(image):
    s = scipy.ndimage.morphology.generate_binary_structure(2, 2)
    labels, n = scipy.ndimage.measurements.label(image)  # ,structure=s)
    objects = scipy.ndimage.measurements.find_objects(labels)
    return objects


def bounding_boxes(image, connected_components, max_size, min_size):
    mask = np.zeros(image.shape, 'B')  # np.uint8)#'B')
    for component in connected_components:
        if area_bb(component)**.5 < min_size:
            continue
        if area_bb(component)**.5 > max_size:
            continue
        #a = area_nz(component,image)
        # if a<min_size: continue
        # if a>max_size: continue
        mask[component] = 1  # 255
    return mask


def masks(image, connected_components, max_size, min_size):
    mask = zeros(image.shape, np.uint8)  # ,'B')
    for component in connected_components:
        if area_bb(component)**.5 < min_size:
            continue
        if area_bb(component)**.5 > max_size:
            continue
        #a = area_nz(component,image)
        # if a<min_size: continue
        # if a>max_size: continue
        # print str(image[component])
        mask[component] = image[component] > 0
        # print str(mask[component])
    return mask


def draw_bounding_boxes(img, connected_components, max_size=0, min_size=0, color=(0, 0, 255), line_size=2):
    for component in connected_components:
        if min_size > 0 and area_bb(component)**0.5 < min_size:
            continue
        if max_size > 0 and area_bb(component)**0.5 > max_size:
            continue
        #a = area_nz(component,img)
        # if a<min_size: continue
        # if a>max_size: continue
        (ys, xs) = component[:2]
        cv2.rectangle(img, (xs.start, ys.start),
                      (xs.stop, ys.stop), color, line_size)


def filter_by_size(image, connected_components, max_size, min_size):
    filtered = []
    for cc in connected_components:
        if area_bb(cc)**0.5 < min_size:
            continue
        if area_bb(cc)**0.5 > max_size:
            continue
        filtered.append(cc)
    return filtered


def filter_by_black_white_ratio(img, connected_components, maximum=1.0, minimum=0.0):
    filtered = []
    for component in connected_components:
        black = area_nz(component, img)
        a = area_bb(component)
        percent_black = float(black)/float(a)
        if percent_black < minimum or percent_black > maximum:
            # print 'component removed for percent ' + str(percent_black)
            continue
        filtered.append(component)
    return filtered


def average_size(img, minimum_area=3, maximum_area=100):
    components = get_connected_components(img)
    sorted_components = sorted(components, key=area_bb)
    #sorted_components = sorted(components,key=lambda x:area_nz(x,binary))
    areas = zeros(img.shape)
    for component in sorted_components:
        # As the input components are sorted, we don't overwrite
        # a given area again (it will already have our max value)
        if amax(areas[component]) > 0:
            continue
        # take the sqrt of the area of the bounding box
        areas[component] = area_bb(component)**0.5
        # alternate implementation where we just use area of black pixels in cc
        # areas[component]=area_nz(component,binary)
    # we lastly take the median (middle value of sorted array) within the region of interest
    # region of interest is defaulted to those ccs between 3 and 100 pixels on a side (text sized)
    aoi = areas[(areas > minimum_area) & (areas < maximum_area)]
    if len(aoi) == 0:
        return 0
    return np.median(aoi)


def mean_width(img, minimum=3, maximum=100):
    components = get_connected_components(img)
    sorted_components = sorted(components, key=area_bb)
    widths = zeros(img.shape)
    for c in sorted_components:
        if amax(widths[c]) > 0:
            continue
        widths[c] = width_bb(c)
    aoi = widths[(widths > minimum) & (widths < maximum)]
    if len(aoi) > 0:
        return np.mean(aoi)
    return 0


def mean_height(img, minimum=3, maximum=100):
    components = get_connected_components(img)
    sorted_components = sorted(components, key=area_bb)
    heights = zeros(img.shape)
    for c in sorted_components:
        if amax(heights[c]) > 0:
            continue
        heights[c] = height_bb(c)
    aoi = heights[(heights > minimum) & (heights < maximum)]
    if len(aoi) > 0:
        return np.mean(aoi)
    return 0


def form_mask(img, max_size, min_size):
    components = get_connected_components(img)
    sorted_components = sorted(components, key=area_bb)
    #mask = bounding_boxes(img,sorted_components,max_size,min_size)
    mask = masks(img, sorted_components, max_size, min_size)
    return mask


def segment_into_lines(img, component, min_segment_threshold=1):
    (ys, xs) = component[:2]
    w = xs.stop-xs.start
    h = ys.stop-ys.start
    x = xs.start
    y = ys.start
    aspect = float(w)/float(h)

    vertical = []
    start_col = xs.start
    for col in range(xs.start, xs.stop):
        count = np.count_nonzero(img[ys.start:ys.stop, col])
        if count <= min_segment_threshold or col == (xs.stop):
            if start_col >= 0:
                vertical.append((slice(ys.start, ys.stop), slice(start_col, col)))
                start_col = -1
        elif start_col < 0:
            start_col = col

    # detect horizontal rows of non-zero pixels
    horizontal = []
    start_row = ys.start
    for row in range(ys.start, ys.stop):
        count = np.count_nonzero(img[row, xs.start:xs.stop])
        if count <= min_segment_threshold or row == (ys.stop):
            if start_row >= 0:
                horizontal.append((slice(start_row, row), slice(xs.start, xs.stop)))
                start_row = -1
        elif start_row < 0:
            start_row = row

    # we've now broken up the original bounding box into possible vertical
    # and horizontal lines.
    # We now wish to:
    # 1) Determine if the original bounding box contains text running V or H
    # 2) Eliminate all bounding boxes (don't return them in our output lists) that
    #   we can't explicitly say have some "regularity" in their line width/heights
    # 3) Eliminate all bounding boxes that can't be divided into v/h lines at all(???)
    # also we will give possible vertical text runs preference as they're more common
    # if len(vertical)<2 and len(horizontal)<2:continue
    return (aspect, vertical, horizontal)

def draw_2d_slices(img, slices, color=(0, 0, 255), line_size=1):
    for entry in slices:
        vert = entry[0]
        horiz = entry[1]
        cv2.rectangle(img, (horiz.start, vert.start),(horiz.stop, vert.stop), color, line_size)