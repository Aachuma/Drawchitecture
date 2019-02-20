**DRAWCHITECTURE**  
_freehand sketching in **3D** using a Add-on for [**Blender 2.8 beta**](https://www.blender.org/2-8/)_  
`Author: Philipp Sommer` `Blender Plug-In scripted in Python` `making use of graphic tablet hardware or mouse`

This Add-on makes use of the new Grease Pencil features in Blender 2.8 beta as a 3D sketching Tool for users 
without any Blender experience. **Drawchitecture** enables the user to quickly create grids of planes right 
at the last stroke of the pen or at up to 3 selected stroke vertices. 
Those planes are easy to scale, rotate and offset perpendicular to keep 
the user drawing rather than frequently setting up the environment to draw on between placing strokes.

The tool also features adding new _Grease Pencil Objects_ to the Scene for multi layered drawings and 
activating the _Grease Pencil Draw Mode_ quickly after using _Object Mode, Edit Mode, Sculpt mode_ and other 
non-drawing-related features in Blender.
![screenshot 1](https://github.com/Aachuma/Drawchitecture/blob/master/pictures/2019-02-20_23h16_11.png?raw=true) 
![screenshot 2](https://github.com/Aachuma/Drawchitecture/blob/master/pictures/2019-02-20_23h17_41.png?raw=true)
![screenshot 3](https://github.com/Aachuma/Drawchitecture/blob/master/pictures/2019-02-20_23h46_59.png?raw=true)
![screenshot 4](https://github.com/Aachuma/Drawchitecture/blob/master/pictures/2019-02-20_23h47_38.png?raw=true)
#    
**INSTALLATION**
![screenshots of the installation process](https://github.com/Aachuma/Drawchitecture/blob/master/how_to_install.png?raw=true)

1. After downloading the newest version of [**Blender 2.8 beta**](https://www.blender.org/2-8/) go to `Edit` `>` `Preferences` `>` `Add-ons` `>` `Install...`
2. Select the `drawchitecture.py` file and click `Install Add-on from File...`
3. In the list of installed Add-ons filter for `Testing`, search for `'Drawchitecture'` and activate the Plug-In
4. If you do not see the sidebar in the `3D View` you may hit `N` or click the `<` on the right edge of the screen
5. Select the Tab labeled `Drawchitecture` 
#
**INPUTS - may be mapped to your Digital Pen Tablet input device**  
`TAB` switch between modes of blender - click any button in `Drawchitecture`-menu to come back to drawmode

* mouse:  
  * `LMB` select points of strokes / draw (depending on blender's mode)  
  * `MMB` Rotate View, alternative to `ENTER` after inputs (_i.E. drawing line, circle, rectangle_)  
  * `RMB` context menu / cancel inputs   
  * `Mouse Wheel` zoom  

* keyboard:  
  * `SHIFT` while drawing: smooth strokes / `+ MMB` pan view     
  * `CTRL` `+ LMB` eraser / activate stepping in number sliders / `+ MMB` zoom
#
**BASIC WORKFLOW**

You might want to delete or turn of the visibility of the standard-objects in the scene (Camera, Light, Box) before
starting to draw. Click the eyeball icon in the `outliner` where all objects are listed to make them invisible or 
select them in the `3D View` and hit `DEL`.

![picture of the menu](https://github.com/Aachuma/Drawchitecture/blob/master/pictures/menu.png?raw=true)

#
**SETUP**
 1. Click `> Setup View` to change background color and other 3D View specific Settings
 2. Click ` horizontal base plane` to create a workplane at `(0,0,0)` 
 3. You may now: 
 * **Draw** using `Left Mouse Button`
 * **Rotate** the _work plane_ in any axis
 * **Offset** the _work plane_ (Hold `STRG` while dragging  left/right on a value for 1m steps)
 * set up the **Grid Size** and **Count**
 
 #
**WORK PLANES** 

After drawing a _stroke_ create a _work plane_ by using the buttons in the **Drawchitecture Menu**:
 * `horizontal base plane` will always bring back the workplane at `(0,0,0)` 
 * `V` / `H` creates a **vertical** or **horizontal** workplane defined by first and last point of the last stroke
 * `3D` creates a **tilted** workplane through the first and last points of the last stroke  
 * rotating the plane's `Y-Axis` will keep it in line with the last stroke
 * `delete stroke` `[ ]` will delete the last drawn stroke when using `V` / `H` / `3D`  
 alternatively click `Delete Last Stroke` to delete the strokes of the active _Grease Pencil Object_ in reversed order

When there are several strokes in 3D:
 * `select 1 / 2 / 3 points` will enter _Edit Mode_   
 you may select **up to 3 vertices (aka points)** of the active _Grease Pencil Object_ (hold `SHIFT`)  
 after selection hit `select 1 / 2 / 3 points` again to create a plane touching all 3 points  
 to cancel selection click at any _Grease Pencil Object_ in the list at the bottom of the menu  

