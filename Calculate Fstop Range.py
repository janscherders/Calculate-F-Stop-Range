bl_info = {
	"name": "Calculate FStop Range",
	"author": "Rainer Trummer, based on Troy James Sobotka's work",
	"version": (0, 1, 1),
	"blender": (2, 77, 0),
	"description": "calculates the dynamic range of an image by comparing darkest and brightest scene referred value",
	"category": "Image"
}

import bpy
from math import log
import numpy

def calc_fstop(operator, context):
	#	get currently active image in the image editor
	img = context.edit_image
	render_result = None
	_numpyImg = numpy.array(img.pixels)

	#	the render result image unfortunately does not expose its pixels
	#	save the rendering first to be able to read them
	if len(_numpyImg) == 0:
		#	try to hookup a Viewer Node insted, its pixels can be accessed
		_numpyImg = numpy.array(render_result_workaround(operator, context).pixels)
		render_result = bpy.data.images.get('Render Result')

		#	check if still no pixels are found. If so, return (warning has been printed already)
		if len(_numpyImg) == 0:
			#	for Render Result or other image types that do not expose pixels, display an error message
			#	operator.report({'ERROR'}, 'Image does not expose its pixels.\nNote that this operator cannot work on the Render Result directly,\nit only works on images loaded from disk!')
			return

	#	magic formula to calculate the fstop range
	try:
		_max = numpy.max(_numpyImg[numpy.nonzero(_numpyImg)])
		_min = numpy.min(_numpyImg[numpy.nonzero(_numpyImg)])
	except ValueError:
		operator.report({'ERROR'}, 'image is completely black, cannot measure a range')
		return

	img.fstop_range = (log(_max) / log(2)) - (log(_min) / log(2))
	img.pixel_min = _min
	img.pixel_max = _max

	#	workaround to display the value which is stored on the Viewer Node on the Render Result as well
	if render_result:
		render_result.fstop_range = img.fstop_range
		render_result.pixel_min = img.pixel_min
		render_result.pixel_max = img.pixel_max

	print('max: %f' % _max)
	print('min: %f' % _min)

def render_result_workaround(operator, context):
	context.scene.use_nodes = True
	tree = context.scene.node_tree
	result = context.edit_image

	_comp = tree.nodes.get('Composite')
	if _comp:
		#	There is a composition set up, its input is the thing we want to measure
		#	let's step up one node and try to hookup a Viewer to this
		try:
			print('searching source of comp')
			_from_node = _comp.inputs.get('Image').links[0].from_node

			print('hooking up a viewer')
			result = tree.nodes.get('Viewer')
			if not result:
				result = tree.nodes.new('CompositorNodeViewer')

			tree.links.new(_comp.inputs.get('Image').links[0].from_socket, result.inputs['Image'])

		except Exception as _exc:
			operator.report({'ERROR'}, 'tried to find valid composition, but failed\nTry switching to and measuring a Viewer Node manually\n%s' % _exc)
			return result

	return bpy.data.images.get('Viewer Node')


#	fstop calculation operator
class CalcFStopOperator(bpy.types.Operator):
	bl_idname = "image.calc_fstop"
	bl_label = "calculate fstop range"
	bl_description = 'Calculates the fstop range of the currently visible image'

	@classmethod
	def poll(cls, context):
		#	only run if we're in the image editor window, and there is an image displayed
		return context.space_data.type == 'IMAGE_EDITOR' and context.edit_image

	def execute(self, context):
		calc_fstop(self, context)
		return {'FINISHED'}


#	UI function
class IMAGE_PT_fstop_range(bpy.types.Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'TOOLS'
	bl_label = "FStop Range"
	bl_category = "Scopes"

	@classmethod
	def poll(cls, context):
		return context.edit_image

	def draw(self, context):
		layout = self.layout

		col = layout.column()
		col.operator(CalcFStopOperator.bl_idname)

		if context.edit_image.fstop_range:
			col.label(text = 'FStop range: %f' % context.edit_image.fstop_range)
			col.label(text = 'Scene referred min pixel: %f' % context.edit_image.pixel_min)
			col.label(text = 'Scene referred max pixel: %f' % context.edit_image.pixel_max)


def register():
	#	add a FloatProperty to the image type to store the fstop range
	bpy.types.Image.fstop_range = bpy.props.FloatProperty()
	bpy.types.Image.pixel_min = bpy.props.FloatProperty()
	bpy.types.Image.pixel_max = bpy.props.FloatProperty()

	bpy.utils.register_class(CalcFStopOperator)
	bpy.utils.register_class(IMAGE_PT_fstop_range)


def unregister():
	del bpy.types.Image.fstop_range
	del bpy.types.Image.pixel_min
	del bpy.types.Image.pixel_max
	bpy.utils.unregister_class(CalcFStopOperator)
	bpy.utils.unregister_class(IMAGE_PT_fstop_range)


if __name__ == "__main__":
	register()