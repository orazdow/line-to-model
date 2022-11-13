## line-to-model

Line drawing to 3D model

This is an application to create 3D wireframes from images. It uses OpenCV to approximate centerline tracing and for edge detection. 

The process is to use the [Dear PyGui](https://dearpygui.readthedocs.io) gui to prepare the image. Applying Gaussian blur, Canny edge detection, and dilation is the preprocessing step. The model can be generated after this, but will be 2D unless and additional image is loaded to provide Z values using either hue or lightness. 

The resulting model is saved to the ```/dist``` folder as a javascript file where an included renderer is ready to serve to a browser. The format is the same as a .OBJ but it consists of line and vertex elements only. Using convex hull or some other process during or after the generation step might be a good option at add. 
