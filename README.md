> See this as a reference first:
> http://blender.stackexchange.com/questions/46825/render-with-a-wider-dynamic-range-in-cycles-to-produce-photorealistic-looking-im

In the question above the issue of photorealistic images and the need of a Wide Dynamic Range is discussed. Rendering with a wider dynamic range to produce photorealistic looking images will need high quality HDRi's (when using HDRi's). In this article http://adaptivesamples.com/2016/02/23/what-makes-good-hdri/ Greg Zaal talks about resolution and dynamic range of HDR images. Greg Zaal says:

> For an interior shot, 12 EVs is usually enough, but for an outdoor shot where the sun is visible, you might need up to 24 EVs to capture everything depending on the time of day and the weather.

**Now how can I measure the dynamic range of an HDR image ?**

Troy Sobotka says:

# Concept
To properly answer your question, I'll lean on the photographic term of F-Stop to define what this range is.

What we know:
1) An F-Stop is a halving and doubling of light, relative to the exposure referenced.
2) A scene referred system has scene linear levels of light ranging from zero to infinity.
Therefore, to get from the question of dynamic range in stops to data values, we need to do a little math and figure out what our maximum and minimum values are in a given image, then convert that range to F-Stops for our solution.
We know that 2^FStops * middle_grey_peg will give us a numerical value for a given number of stops above or below middle grey in scene linear. So how would we go back from scene linear to F-Stops? Invert the formula for log(scene_referred / middle_grey_peg) / log(2) and we get the number of stops up or down for any given scene referred value.
If we subtract the two, we'd get overall dynamic range.

We can simplify it by skipping the middle grey value:
>( log(scene_referred_maximum) / log(2) ) - ( log(scene_referred_minimum) / log(2) )
The result will be total dynamic range, expressed in stops.


# Add-On
Based on Troy's answer, here is a little Add-on that places a button in the Image Editor at the end of the Scopes Tab, and provides an operator that stores the EV value in a Custom Property of the image itself. This way, it will be saved with the Blender scene and doesn't need to be recalculated all the time. Note that all credits go to troy_s, I just don't have any other chance to post the Add-on than to write it as an answer.

Based on user request, I refactored the code a bit to also work on the Render Result slot. The issue is that the Render Result Slot does not expose the needed **.pixels** parameter. Basically, I'm looking for a Composite Node in the Node Tree. If the user had not used it at all so far, the 'use nodes' checkbox will be set, and thus a Comp node will be thrown in automatically. Then I'm searching for the Image input of the Comp node, and hook up a Viewer Node to that. If there is a Viewer Node in the tree already, I re-use it. This way, the users Composition is not destroyed.

Using the numpy library, there is a significant speedup in the calculation of the end result. Also, the min and max scene referred value are now displayed for the user to better judge the meaningfulness of the given range. The issue is, CG renderings tend to contain very low pixel values, close to black, resulting in ridiculously high dynamic ranges. No real way to fix this, but at least it can be exposed to the viewer.
Note that this method will actually measure the FStop range (I also renamed all references for clarity) of the whole composition.

You can also measure the Viewer Node with this Add-on. The benefit of this is that you can set up and tweak an HDRI image in the Compositor to fulfill a certain FStop range by doing crazy node stuff after throwing in the HDR image. Once you found the node setup that works for you, you can replicate it in the World Node Tree. Or render out the HDR Image into a new one (i.e. baking the new range). Note that you need to re-run the calculation every time you change the comp, updating it automatically would be much too expensive.

## Usage in Blender up to 2.79b
Git checkout or download the master branch of the Add-on and install it as usual.

Go to the **Image Editor**, display an Image (load in an HDRI, or look at your comp through the Viewer Node). In the toolbar under the scopes you'll find a button to **calculate the FStop range**.

If you want to use it on the Render Result, be aware that a workaround is needed. The Add-on will setup a comp for you, connecting whatever goes to the Comp node to a new Viewer Node. However, the Viewer Node only updates **after** a render. In plain English: If you start fresh, setup a scene, render, go to the Image Editor, preview the Render Result, and click **measure FStop range**, nothing happens. Why? Because when you clicked, the viewer node has just been created, but it hasn't received any data yet. Re-Render or switch to the Viewer Node in the Image Editor manually and measure again. Then it should work fine.

## Usage in Blender 2.8
First of all make sure to git check out or download the **blender2.8 branch** of the Add-on and install it as usual.

Go to the **Image Editor**, display an Image (load in an HDRI, or look at your comp through the Viewer Node). In the Properties Panel, under the Image Tab there is a **FStop Range** Sub-Panel. In there you'll find a button to **calculate the FStop range**.

If you want to use it on the Render Result, be aware that a workaround is needed. The Add-on will setup a comp for you, connecting whatever goes to the Comp node to a new Viewer Node. However, the Viewer Node only updates **after** a render. In plain English: If you start fresh, setup a scene, render, go to the Image Editor, preview the Render Result, and click **measure FStop range**, nothing happens. Why? Because when you clicked, the viewer node has just been created, but it hasn't received any data yet. Re-Render or switch to the Viewer Node in the Image Editor manually and measure again. Then it should work fine.
