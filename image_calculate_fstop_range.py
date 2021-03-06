import bpy
import logging
from math import log
import numpy

logger = logging.getLogger('image_measure_fstop_range')


def calc_fstop(operator, context):
	#    get currently active image in the image editor
	img = context.edit_image
	render_result = None
	_numpyImg = numpy.array(img.pixels)

	#    the render result image unfortunately does not expose its pixels
	#    save the rendering first to be able to read them
	if len(_numpyImg) == 0:
		#    try to hookup a Viewer Node insted, its pixels can be accessed
		_numpyImg = numpy.array(render_result_workaround(operator, context).pixels)
		render_result = bpy.data.images.get('Render Result')

	#    delete every 4th pixel, as this represents the Alpha channel
	_numpyImg_noAlpha = numpy.delete(_numpyImg, numpy.arange(3, _numpyImg.size, 4))

	#    after discussing with Troy Sobotka, there is two more things to implement
	#    1) calculate the range based on the luminance of a pixel instead of the lowest and highest linear radiance channel
	#       see https://medium.com/the-hitchhikers-guide-to-digital-colour/question-12-how-the-f-ck-can-we-talk-about-light-intensity-c6ba0ff0388e
	#    2) use a pre-pass (lo-pass is suggested) on the pixels
	#    the first can be achieved by generating a new array based on a REC.709 related formula,
	#    as Blender uses REC.709 lights in linear space
	#    the latter is more tricky, would possible be doable using the Compositor and reading pixels from the Viewer Node

	_numpyImg_noAlpha_rs = _numpyImg_noAlpha.reshape(int(len(_numpyImg_noAlpha) / 3), 3)

	#    multiply the three channels in place with the lightness conversion values
	_numpyImg_noAlpha_rs[..., 0] *= 0.2126    #    R channel
	_numpyImg_noAlpha_rs[..., 1] *= 0.7152    #    G channel
	_numpyImg_noAlpha_rs[..., 2] *= 0.0722    #    B channel

	#    sum the channels now
	_lightnessPixels = _numpyImg_noAlpha_rs.sum(axis = 1)

	#    magic formula to calculate the fstop range
	try:
		_nonZeros = _lightnessPixels[numpy.nonzero(_lightnessPixels)]
		_max = numpy.max(_nonZeros)
		_min = numpy.min(_nonZeros)
	except ValueError as exc:
		operator.report({'ERROR'}, 'Cannot measure a range:\n %s' % exc)
		return

	img.fstop_range = (log(_max) / log(2)) - (log(_min) / log(2))
	img.pixel_min = _min
	img.pixel_max = _max

	#    workaround to display the value which is stored on the Viewer Node on the Render Result as well
	if render_result:
		render_result.fstop_range = img.fstop_range
		render_result.pixel_min = img.pixel_min
		render_result.pixel_max = img.pixel_max

	logger.debug('max: %.20f' % _max)
	logger.debug('min: %.20f' % _min)


def render_result_workaround(operator, context):
	context.scene.use_nodes = True
	tree = context.scene.node_tree
	result = context.edit_image

	_comp = tree.nodes.get('Composite')
	if _comp:
		#    There is a composition set up, its input is the thing we want to measure
		#    let's step up one node and try to hookup a Viewer to this
		try:
			print('searching source of comp')
			_from_node = _comp.inputs.get('Image').links[0]

			print('hooking up a viewer')
			viewerNode = tree.nodes.get('Viewer')
			if not viewerNode:
				viewerNode = tree.nodes.new('CompositorNodeViewer')

			tree.links.new(_from_node.from_socket, viewerNode.inputs['Image'])

			#    return the Viewer Node image
			result = bpy.data.images.get('Viewer Node')

		except Exception as _exc:
			operator.report({'ERROR'}, 'tried to find valid composition, but failed\nTry switching to and measuring a Viewer Node manually\n%s' % _exc)

	return result


#===============================================================================
#    fstop calculation operator
#===============================================================================
class IMAGE_OT_CalcFStopOperator(bpy.types.Operator):
	bl_idname = "image.calc_fstop"
	bl_label = "calculate fstop range"
	bl_description = 'Calculates the fstop range of the currently visible image'

	@classmethod
	def poll(cls, context):
		#    only run if we're in the image editor window, and there is an image displayed
		return context.space_data.type == 'IMAGE_EDITOR' and context.edit_image

	def execute(self, context):
		calc_fstop(self, context)
		return {'FINISHED'}


#===============================================================================
#    UI function
#===============================================================================
class IMAGE_PT_fstop_range(bpy.types.Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_label = "FStop Range"
	bl_parent_id = 'IMAGE_PT_image_properties'
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		return context.edit_image

	def draw(self, context):
		layout = self.layout

		col = layout.column()
		col.operator(IMAGE_OT_CalcFStopOperator.bl_idname)

		if context.edit_image.fstop_range:
			box = col.box()
			box.label(text = 'FStop Range: %f' % context.edit_image.fstop_range)

			col = col.column()
			col.label(text = f'Luminance Min: {context.edit_image.pixel_min:10f}')

			col = col.column()
			col.label(text = f'Luminance Max: {context.edit_image.pixel_max:10f}')
