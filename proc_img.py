import dearpygui.dearpygui as dpg
import easygui
import cv2 as cv
import numpy as np
from types import SimpleNamespace
import os


g = SimpleNamespace(
	fname = './test.jpg',
	fnames = [],
	img = None,
	imgdata = None,
	timg = None,
	rimg = None,
	dir_idx = 0,
	gbool = False,
	cbool = False,
	hbool = False,
	mbool = False,
)

win_dimensions = [600, 600]

def init():
	g.img = cv.imread(g.fname)
	if g.img is None:
		g.img = np.zeros((20, 20, 3), np.uint8)
		print('load error:', g.fname, 'using empty image')
	g.imgdata = flat_img(g.img)
	g.timg = g.img.copy()
	g.rimg = g.img.copy()

def fit_image(img, dimensions):
	img_dim = np.flip(img.shape[:2])
	scale = 1
	if(dimensions[0] <= dimensions[1]):
		scale = dimensions[0]/img_dim[0]
	else: scale = dimensions[1]/img_dim[1]
	img_dim[0]*=scale
	img_dim[1]*=scale
	return cv.resize(img, img_dim)	

# update texture with new dimension using cv2
# configure_item on add_image to scale causes crashes
def resize_window_img(wintag, textag, dimensions, mat):
	img = fit_image(mat, dimensions)
	imgdata = flat_img(img)
	# delete texture/image, re-add
	dpg.delete_item(wintag, children_only=True)
	dpg.delete_item(textag)
	with dpg.texture_registry(show=False):		
		dpg.add_raw_texture(img.shape[1], img.shape[0], imgdata, tag=textag, format=dpg.mvFormat_Float_rgb)
		dpg.add_image(textag, parent=wintag)

def flat_img(mat):
	return np.true_divide(np.asfarray(np.ravel(np.flip(mat,2)), dtype='f'), 255.0)

def update_preview(mat):
	img = fit_image(mat, win_dimensions)
	imgdata = flat_img(img)
	dpg.set_value("tex_tag", imgdata)

def gaussian(img, k, s):
	k = int(k)
	k = k if (k%2 != 0) else k+1	
	return cv.GaussianBlur(img, (k,k), s, 0, cv.BORDER_DEFAULT)

def diff_gaussian(img, k1, k2, s1, s2):
	k1 = int(k1)
	k2 = int(k2)
	k1 = k1 if (k1%2 != 0) else k1+1		
	k2 = k2 if (k2%2 != 0) else k2+1
	m1 = cv.GaussianBlur(img, (k1,k1), s1, 0, cv.BORDER_DEFAULT)	
	m2 = cv.GaussianBlur(img, (k2,k2), s2, 0, cv.BORDER_DEFAULT)
	return (m1-m2)	

def proc_tone(mat, hue, sat, gamma, invert):
	hsv = cv.cvtColor(mat, cv.COLOR_BGR2HSV)
	h, s, v = cv.split(hsv)
	shift_h = (h+int(hue*180))%255
	s = np.multiply(s, sat).astype(np.uint8)
	shift_hsv = cv.merge([shift_h, s, v])
	mat = cv.cvtColor(shift_hsv, cv.COLOR_HSV2BGR)
	return mat if not invert else (255-mat)

def dilate(mat, k, i):
	if i < 1: i = 1
	if k < 2: k = 2
	kernel = np.ones((k, k), np.uint8)
	return cv.dilate(mat, kernel, iterations=i)

def proc_canny(mat, t1, t2):
	return cv.cvtColor(cv.Canny(mat, int(t1), int(t2)), cv.COLOR_GRAY2BGR)

def handle_edit(resize=False):
	mat = g.img.copy()
	if(g.gbool):
		mat = gaussian(mat, dpg.get_value("gbar_k"), dpg.get_value("gbar_s"))
	if(g.cbool):
		mat = proc_canny(mat,  dpg.get_value("cbar1"), dpg.get_value("cbar2"))
	if(g.mbool):
		mat = dilate(mat, dpg.get_value("mbark"), dpg.get_value("mbari"))
	if(g.hbool):
		mat = proc_tone(mat, dpg.get_value("hbar"), dpg.get_value("sbar"), 0, dpg.get_value("ibox")) 
	g.timg = mat
	if not resize:
		update_preview(mat)
	else:
		resize_window_img("img_window", "tex_tag", win_dimensions, g.timg)	

def afteredit_cb(sender, data):
	handle_edit()

def box_cb(sender, data):
	if(sender == "gbox"):
		g.gbool = data
	elif(sender == "cbox"):
		g.cbool = data
	elif(sender == "mbox"):
		g.mbool = data
	elif(sender == "hbox"):
		g.hbool = data
	handle_edit()

def viewport_resize_cb(sender, data):
	d = dpg.get_item_configuration("img_window")
	win_dimensions[0] = d['width']
	win_dimensions[1] = d['height']
	resize_window_img("img_window", "tex_tag", win_dimensions, g.timg)

def apply_rev_cb(sender, data):
	if sender == "apply":
		g.img = g.timg.copy()
	elif sender == "revert":
		g.img = g.rimg.copy()
		g.timg = g.rimg.copy()
	dpg.set_value("gbox", False)
	dpg.set_value("cbox", False)
	dpg.set_value("mbox", False)
	dpg.set_value("hbox", False)
	g.gbool = False
	g.dbool = False
	g.cbool = False
	g.hbool = False
	g.mbool = False
	update_preview(g.img)

def save_cb():
	try:
		file = easygui.filesavebox()
		if(file):
			cv.imwrite(file, g.timg)
			print(file, 'saved')
	except Exception as e:
		print(e)
	
def load_file(path):
	img = cv.imread(path)
	if img is None:
		print('load error', path)
	else:
		g.fname = path
		g.img = img
		g.imgdata = flat_img(g.img)
		g.timg = g.img.copy()
		g.rimg = g.img.copy()
		handle_edit(True)
		dpg.set_value("file_text", os.path.basename(g.fname))
		print(g.fname, 'loaded')

def dir_callback(sender, data):
	try:
		dir = easygui.diropenbox()
		ls = os.listdir(dir)
		ls = [os.path.join(dir, f) for f in ls if f.endswith(('.jpg', '.jpeg', '.jfif', '.png'))]
		if(len(ls) > 0):
			g.fnames = ls
			dpg.show_item("dirnav")	
			load_file(g.fnames[g.dir_idx])
	except Exception as e:
		print(e)

def file_callback(sender, data):
	try:
		file = easygui.fileopenbox()
		if(file.endswith(('.jpg', '.jpeg', '.jfif', '.png'))):
			load_file(file)
			dpg.hide_item("dirnav")	
	except Exception as e:
		print(e)	

def load_dirfile(sender, data):
	if(len(g.fnames) == 0):
		print('no files in dir list')
		return
	inc = -1 if sender == "lfile" else 1
	g.dir_idx = (g.dir_idx+inc)%len(g.fnames)
	g.fname = g.fnames[g.dir_idx]
	load_file(g.fname)
