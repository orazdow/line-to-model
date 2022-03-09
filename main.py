import numpy as np
import cv2 as cv
import math as m
import json

def normalize(coord, res):
		w, h = res[0], res[1]
		return [(2.*coord[0]-w)/h, (2.*coord[1]-h)/h]+coord[2:]	

def truncate(f, n):
	return m.floor((f) * 10**n) / 10**n

def get_channel(vec, hsvimg, v=False):
	if type(hsvimg) != np.ndarray: return vec
	c = 0 if not v else 2
	vec[2] = hsvimg[vec[1]][vec[0]][c]/255.
	return vec

def make_indices(lines):
	_v, _e, idx = [], [], 0
	for el in lines:
		e = []
		for v in el:
			_v.append(v)
			e.append(idx)
			idx += 1
		if(len(e) > 0): _e.append(e)
	return {'v':_v, 'e':_e}

img = cv.imread('lines.jpg', cv.IMREAD_GRAYSCALE)
if(img.shape[0] > 800):
	img = cv.resize(img,  (int(.7*img.shape[1]), int(.7*img.shape[0])))
img = cv.threshold(img, 127, 255, cv.THRESH_BINARY)[1]
contours, h = cv.findContours(img, cv.RETR_LIST, 3)
mat = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)

zpath = 'lines-z.jpg'
zimg = cv.imread(zpath)
zimg = cv.resize(zimg,  (img.shape[1], img.shape[0]))
cv.imshow('zimg', zimg)
zhsv = cv.cvtColor(zimg, cv.COLOR_BGR2HSV)

lines = []

for c in contours:
	poly = cv.approxPolyDP(c, 3, False)
	poly = poly[:int(len(poly)/1.5)]
	arr = [normalize(get_channel(e[0].tolist()+[0, 1], zhsv),img.shape) for e in poly]
	arr = [[truncate(el, 6) for el in a] for a in arr]
	lines.append(arr)
	cv.polylines(mat, [poly], False, (0,0, 255), 1)

obj = json.dumps(make_indices(lines), indent = 4)
obj = 'const lines = '+obj+'\nexport default lines;'
with open("lines.js", "w") as outfile:
    outfile.write(obj)

cv.imshow('img', mat)
cv.waitKey(0)
cv.destroyAllWindows()