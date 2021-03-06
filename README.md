# Ring Ruler

This add on for Blender helps in the creation of rings with text written on them. 

They are used to mark birds when they are young.

## Installation

Blender add ons are nothing more than python scripts stored in `scripts/addons/` within blender's configuration.

Download and zip the `ring_ruler` directory in this repository. In Blender, go to "Preferences -> Add-ons" and click "Install".

A file browser pops up. Pick the zipped version of the `ring_ruler` directory and hit "Install Add-on". 

Blender will automatically unpack the zip and store all files at the right place in `scripts/addons/ring_ruler`.

## Usage

In Blender, search for "Ring Ruler" or go to "Object -> Ring Ruler". A helper window with settings will pop up.

The rings are created in original size (millimeters) scaled by a scale factor (usually 1000). 
The default cube measures 1x1x1 meter, so it covers the created rings if the scale factor is 1.
Delete/move it and zoom towards the center.

You can choose a custom font in the drop down menu. The font must be loaded, do this by going to a text object and loading the font there in the "Font" tab.

