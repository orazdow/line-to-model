import numpy as np
import cv2 as cv
import math as m
import json

def normalize(coord, res=None):
	if res is None:
		return coord
	else:
		w, h = res[0], res[1]
		return [(2.*coord[0]-w)/h, (2.*coord[1]-h)/h]	

def truncate(f, n):
	return m.floor((f) * 10**n) / 10**n

img = cv.imread('lines.jpg', cv.IMREAD_GRAYSCALE)
img = cv.resize(img,  (int(.7*img.shape[0]), int(.7*img.shape[1])))
img = cv.threshold(img, 127, 255, cv.THRESH_BINARY)[1]
contours, h = cv.findContours(img, cv.RETR_LIST, 3)
mat = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)

lines = []

for c in contours:
	poly = cv.approxPolyDP(c, 3, False)
	poly = poly[:int(len(poly)/1.5)]
	arr = [normalize(e[0].tolist(), img.shape) for e in poly]
	arr = [[truncate(el, 6) for el in a]+[0,1] for a in arr]
	lines.append(arr)
	cv.polylines(mat, [poly], False, (0,0, 255), 1)

# obj = json.dumps({ "lines": lines}, indent = 4)
# obj = 'const lines = '+obj+'\nexport default lines;'
# with open("lines.js", "w") as outfile:
#     outfile.write(obj)

cv.imshow('img', mat)
cv.waitKey(0)
cv.destroyAllWindows()