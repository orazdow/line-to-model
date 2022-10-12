import dearpygui.dearpygui as dpg
import easygui
import cv2 as cv
import numpy as np
import math as m
import json, os, re
from threading import Thread
from types import SimpleNamespace
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from glob import glob

g = SimpleNamespace(
	fname = '',
	img = None,
	lmat = None,
	zimg = None,
	zhsv = False,
	zinv = False,
	lines = None,
	threads = [],
	server = None
)

def normalize(coord, res):
		w, h = res[0], res[1]
		return [(2.*coord[0]-w)/h, (2.*coord[1]-h)/h]+coord[2:]	

def truncate(f, n):
	return m.floor((f) * 10**n) / 10**n

def get_channel(vec, hsvimg, v=False):
	if type(hsvimg) != np.ndarray: return vec
	c = 0 if not v else 2
	val = hsvimg[vec[1]][vec[0]][c]/255.
	vec[2] = 1.-val if g.zinv else val
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

def display(mat):
	cv.imshow('img', mat)
	cv.waitKey(0)

def write_js(path, lines, fname=None):
	obj = json.dumps(make_indices(lines), indent = 4)
	obj = 'const lines = '+obj+'\nexport default lines;'
	if fname:
		obj = ('/*@ %s */\n\n' % fname) + obj
	with open(path, "w") as outfile:
		outfile.write(obj)

def check_file(path):
	try:
		with open(path, 'r') as f:
			fs = f.read().replace(' ', '')
			m = re.search(r'(?<=/\*@)(.*)(?=\*/)', fs)
			s = (m.group(0) or '').rsplit('/', 1)[-1]
			return s	
	except Exception as e: print(e)	
	return None

def confirm_save():
	try:
		if(g.lines is not None):
			write_js('dist/lines.js', g.lines, glob['g'].fname or None)
			dpg.set_value("line_model_text", 'wrote dist/lines.js')
		else: print('error: line array not present')
	except Exception as e: print(e)	

def save_model():
	st = check_file('dist/lines.js')
	if st:
		dpg.configure_item("overwrite_win", show=True)
		dpg.set_value("overwrite_text", 'model from: %s exists' % st)
	else:	
		confirm_save()

def save_img():
	try:
		file = easygui.filesavebox()
		if(file and g.lmat is not None):
			cv.imwrite(file, g.lmat)
			print(file, 'saved')
	except Exception as e:
		print(e)

def serve():
	dpg.set_value("serve_text", 'serving at port 8080')
	g.server = HTTPServer(('localhost', 8080), partial(SimpleHTTPRequestHandler, directory='dist/'))
	thread = Thread(target=g.server.serve_forever, daemon = True)
	g.threads.append(thread)
	thread.start()

def proc_contours():
	g.img = cvt_img(glob['g'].timg)
	lines = []
	img = cv.threshold(g.img, 127, 255, cv.THRESH_BINARY)[1]
	contours, h = cv.findContours(img, cv.RETR_LIST, 3)
	mat = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
	for c in contours:
		poly = cv.approxPolyDP(c, 3, False)
		poly = poly[:int(len(poly)/1.5)]
		arr = [normalize(get_channel(e[0].tolist()+[0, 1], g.zimg, g.zhsv), img.shape) for e in poly]
		arr = [[truncate(el, 6) for el in a] for a in arr]
		lines.append(arr)
		cv.polylines(mat, [poly], False, (0,0, 255), 1)
	g.lines = lines	
	g.lmat = mat
	dpg.show_item('savelines')
	dpg.show_item('savelineimg')
	dpg.set_value("lines_text", str(len(lines)))
	thread = Thread(target=display, args=[g.lmat])
	g.threads.append(thread)
	thread.start()

def cvt_img(_img):
	if(_img is not None):
		img = cv.cvtColor(_img, cv.COLOR_BGR2GRAY)
		if(img.shape[0] > 800):
			img = cv.resize(img, (int(.7*img.shape[1]), int(.7*img.shape[0])))
	return img

def load_file(path):
	img = cv.imread(path, cv.IMREAD_GRAYSCALE)
	if img is None:
		print('load error', path)
	else:
		if(img.shape[0] > 800):
			img = cv.resize(img, (int(.7*img.shape[1]), int(.7*img.shape[0])))
		g.img = img
		fname = os.path.basename(path)
		dpg.set_value("m_file_text", fname)
		dpg.show_item('serve')
		dpg.show_item('zbutton')
		dpg.show_item('pbutton')

def z_select():
	g.zhsv = (dpg.get_value("zradio") == 'value')
	g.zinv = dpg.get_value("zinv")
	
def load_zfile(path):
	zimg = cv.imread(path)
	if zimg is None:
		print('load error', path)
	else:
		if(g.img is None): 
			g.img = cvt_img(glob['g'].timg)
		zimg = cv.resize(zimg,  (g.img.shape[1], g.img.shape[0]))
		g.zimg = cv.cvtColor(zimg, cv.COLOR_BGR2HSV)
		fname = os.path.basename(path)
		dpg.set_value("m_zfile_text", fname)
		dpg.show_item('z_select')

def file_callback(sender, data):
	try:
		file = easygui.fileopenbox()
		if(file.endswith(('.jpg', '.jpeg', '.jfif', '.png'))):
			if sender == 'm_loadfilebutton':
				load_file(file)
			elif sender == 'm_zloadfilebutton':
				load_zfile(file)
	except Exception as e: print(e)	