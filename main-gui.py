import dearpygui.dearpygui as dpg
import easygui
import cv2 as cv
import numpy as np
from types import SimpleNamespace
import os

g = SimpleNamespace(
	fname = './test.jpg',
	fnames = (),
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

def init(g):
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
	if (dimensions[0] <= dimensions[1]):
		scale = dimensions[0]/img_dim[1]
	else: scale = dimensions[1]/img_dim[0]
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

def handle_edit(tag=""):
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
	update_preview(mat)	

def afteredit_cb(sender, data):
	handle_edit(data)

def box_cb(sender, data):
	if(sender == "gbox"):
		g.gbool = data
	elif(sender == "cbox"):
		g.cbool = data
	elif(sender == "mbox"):
		g.mbool = data
	elif(sender == "hbox"):
		g.hbool = data
	handle_edit(sender)

def viewport_resize_cb(sender, data):
	win_dimensions[0] = data[2:][0]
	win_dimensions[1] = data[2:][1]
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
	except Exception as e:
		print(e)
	else:
		print(file, 'saved')
	
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
		handle_edit()
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

init(g)
dpg.create_context()
dpg.create_viewport(title='img gui', width=win_dimensions[0], height=win_dimensions[1])

with dpg.item_handler_registry(tag="edit_handler") as handler:
	dpg.add_item_deactivated_after_edit_handler(callback=afteredit_cb)

with dpg.texture_registry(show=False):	
	dpg.add_raw_texture(g.img.shape[1], g.img.shape[0], g.imgdata, tag="tex_tag", format=dpg.mvFormat_Float_rgb)

with dpg.window(tag="img_window"):
	dpg.add_image("tex_tag")
	dpg.set_primary_window("img_window", True)

with dpg.window(tag="ctlwindow", label="", no_close=True, min_size=(250,250)):
	with dpg.collapsing_header(label="gaussian blur", tag="gmenu", default_open=True):
		dpg.add_checkbox(label="on", tag="gbox", callback=box_cb)
		dpg.add_slider_int(label="ksize", tag="gbar_k", default_value=0,  max_value=21)
		dpg.add_slider_float(label="sigma", tag="gbar_s", default_value=0.,  max_value=6)

	with dpg.collapsing_header(label="canny", tag="cmenu", default_open=True):
		dpg.add_checkbox(label="on", tag="cbox", callback=box_cb)
		dpg.add_slider_float(label="thresh_l", tag="cbar1", default_value=50.,  max_value=200)
		dpg.add_slider_float(label="thresh_h", tag="cbar2", default_value=100.,  max_value=200)

	with dpg.collapsing_header(label="dilate", tag="mmenu", default_open=True):
		with dpg.group(horizontal=True):
			dpg.add_checkbox(label="on", tag="mbox", callback=box_cb)
		dpg.add_slider_int(label="kernel", tag="mbark", min_value=2, max_value=9)
		dpg.add_slider_int(label="iterations", tag="mbari", min_value=1, max_value=8)

	with dpg.collapsing_header(label="tone", tag="hmenu", default_open=True):
		with dpg.group(horizontal=True):
			dpg.add_checkbox(label="on", tag="hbox", callback=box_cb)
			dpg.add_checkbox(label="invert", tag="ibox")
		dpg.add_slider_float(label="hue", tag="hbar", default_value=0., max_value=1)
		dpg.add_slider_float(label="sat", tag="sbar", default_value=1., max_value=1)

	dpg.add_separator()
	with dpg.group(horizontal=True):
		dpg.add_button(label="apply", tag="apply", callback=apply_rev_cb)
		dpg.add_button(label="revert", tag="revert", callback=apply_rev_cb)

	dpg.add_separator()
	with dpg.group(horizontal=True):
		dpg.add_button(label="file", tag="loadfilebutton", callback=file_callback)
		dpg.add_button(label="dir", tag="loaddirbutton", callback=dir_callback)
		with dpg.group(horizontal=True, tag="dirnav", show=False):
			dpg.add_button(label="<<", tag="lfile", callback=load_dirfile)
			dpg.add_button(label=">>", tag="rfile", callback=load_dirfile)
		dpg.add_text("", tag="file_text")
		dpg.set_value("file_text",os.path.basename(g.fname))
	dpg.add_button(label="save", tag="savebutton", callback=save_cb)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.bind_item_handler_registry("gbar_k", "edit_handler")
dpg.bind_item_handler_registry("gbar_s", "edit_handler")
dpg.bind_item_handler_registry("hbar", "edit_handler")
dpg.bind_item_handler_registry("sbar", "edit_handler")
dpg.bind_item_handler_registry("ibox", "edit_handler")
dpg.bind_item_handler_registry("cbar1", "edit_handler")
dpg.bind_item_handler_registry("cbar2", "edit_handler")
dpg.bind_item_handler_registry("mbark", "edit_handler")
dpg.bind_item_handler_registry("mbari", "edit_handler")
dpg.set_viewport_resize_callback(viewport_resize_cb)
dpg.start_dearpygui()
dpg.destroy_context()