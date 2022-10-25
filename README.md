# AtomBlend-II: A visualization addon for Blender (3.0+)
**Display and edit data from atom tips and render images or videos of your science.**

<p float="left">
  <img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/eisenkorngrenze.gif" width="25%" height="25%"/>
  <img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/iso-surface.gif" width="25%" height="25%"/>
</p>

## Installation of the addon
Install the addon as explained on [the Blender website](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).<br/>
Remember that the addon will not be automatically enabled. Enable it as explained [here](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#installing-add-ons).<br/>
Restart Blender after installation and enabling.<br/>
Go to 3D View, press `N` if the sidebar isn't showing yet, then click `AtomBlend-II`.

## Usage of the addon
### File loading
<img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/readme-file_loading.PNG"/>
Click the file browser icon in the first line to load .pos or .epos files and the icon in the second line to load .rrng files.<br/>
<b>Depending on your hardware, file loading may take a while! Try not to click anywhere while loading a file as Blender may crash in that case.</b>
<br/><br/>
After loading both the .pos/.epos and .rrng files, your screen should look similar to this:
<img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/readme-after_file_loading.PNG" width="50%" height="50%"/>

### Display settings
`Point size` - Changes the point size of all the atoms<br/>
`Total displayed` - Changes the percentage of all the displayed atoms<br/>

<b>The following lines describe the data for every element</b><br/>
`Hide/Display icon` - Hides or displays the element<br/>
`Name` - The name of the element (can not be changed)<br/>
`Charge` - The charge of the element (can not be changed)<br/>
`Color` - The color of this element<br/>
`Point size` - The point size of this element<br/>
`% Displayed` - The displayed percentage of this element<br/>
`# Displayed` - The amount of displayed atoms of this element (can not be changed)<br/>
`Export` - Exports this element as separate object in Blender (<b>As we are using point clouds to keep the frame time in the viewport fast, this feature can only be used in the [Blender alpha version (currently 3.4.0 Alpha)](https://builder.blender.org/download/daily/)</b>). Currently it is not possible to change the color or point size of the exportet object. <br/>

### Rendering
`Picture / Video` - Select if you want to render a picture or video<br/>

#### Picture
<img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/readme-picture_rendering.PNG" width="50%" height="50%"/>

`Camera distance` - Change the distance of the camera to the tip<br/>
`Camera rotation` - Change the rotation of the tip<br/>
`Camera elevation` - Change the elevation of the camera<br/>
`Background color` - Change the background color of the rendering<br/>
`File Format` - Select the file format of your rendering. Currently, you can select between .png, .jpg and .tiff<br/>
`Output Path` - Select the output path of your rendering<br/>
`Preview` - Preview your rendering<br/>
`Render` - Render a picture of your tip. Currently only PNG files are supported.<br/>

#### Video
<img src="https://github.com/peterfelfer/AtomBlend-II/blob/media/media/readme-video_rendering.PNG" width="50%" height="50%"/>

`Camera distance` - Change the distance of the camera to the tip<br/>
`Camera rotation` - Change the start of the rotation of the tip<br/>
`Camera elevation` - Change the elevation of the camera<br/>
`Background color` - Change the background color of the rendering<br/>
`Frames` - Total frame of your video, the approximal duration of the video is also shown<br/>
`Number of rotations` - Change the number of rotations in your video<br/>
`Animation mode` - Change the animation of your video. You can select between:
  - Circle around tip: Camera moves around the tip but stays at the same height<br/>
  - Spiral around tip: Camera moves spirally around the tip from top to bottom<br/>

`File Format` - The file format of your rendering will be .avi. But first, all the frames will be rendered separately and will be converted to a video later. Here, you can choose the file format for these frames. You can select between .png, jpg and .tiff<br/>
`Output Path` - Select the output path of your rendering<br/>
`Preview` - Preview your rendering<br/>
`Render` - Render a video of your tip. Currently only AVI files are supported. <b>Depending on your hardware and frame time, rendering may take a while! Try not to click anywhere while rendering as Blender may crash in that case.</b><br/>

When rendering a video, it can be helpful to open the terminal to see the progress of your render.
This works different on Windows, macOS and Linux. Refer to [the Blender website](https://docs.blender.org/manual/en/3.0/advanced/command_line/launch/index.html) and follow the instructions for your platform.

