'''
Created on 13.01.2017
Updated to 2.8 on 11.11.2018

@author: r.trummer
'''

bl_info = {
	"name": "Calculate FStop Range",
	"author": "Rainer Trummer, based on Troy James Sobotka's work",
	"version": (0, 3, 0),
	"blender": (2, 80, 0),
	"description": "calculates the dynamic range of an image by comparing darkest and brightest scene referred value",
	"category": "Image"
}

if 'bpy' in locals():
	import importlib as imp
	imp.reload(image_calculate_fstop_range)    #    @UndefinedVariable
else:
	import bpy
	from . import image_calculate_fstop_range as mod


def register():
	#    add a FloatProperty to the image type to store the fstop range
	bpy.types.Image.fstop_range = bpy.props.FloatProperty()
	bpy.types.Image.pixel_min = bpy.props.FloatProperty()
	bpy.types.Image.pixel_max = bpy.props.FloatProperty()

	bpy.utils.register_module(__name__)


def unregister():
	del bpy.types.Image.fstop_range
	del bpy.types.Image.pixel_min
	del bpy.types.Image.pixel_max
	bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
	register()
