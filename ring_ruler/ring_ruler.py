import bpy
import datetime
from mathutils import Vector

from .ring import Ring
from .ring_factory import RingFactory
from .utils import log


def arrange_in_plane(rings):
    plane_pos = Vector((0,0))
    plane = Vector((200, 200))
    
    margin = (3,3)
    
    row_max = 0.0
    
    for i, r in enumerate(rings):
        dx = margin[0] + r.bounding_box[0]/2
        dy = margin[1] + r.bounding_box[1]/2

        if plane_pos[0] + 2*dx > plane[0]:
            # to far, move to next row
            plane_pos[0] = 0.0
            plane_pos[1] += row_max
            row_max = 0.0
            x = dx
        
        if plane_pos[0] + 2*dx > plane[0] or plane_pos[1] + 2*dy > plane[1]:
            # Next ring doesn't fit
            print(f"Removing rings [{i}:]")
            del rings[i:]
            break
        
        row_max = max(row_max, 2*dy)
        x = plane_pos[0] + dx
        y = plane_pos[1] + dy
        z = 0.0
            
        r.location = Vector((x,y,z))
        plane_pos[0] += 2*dx        

class RingRulerOperator(bpy.types.Operator):
    """Generates a bunch of rings with text on them"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "object.ring_ruler"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Ring Ruler"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    ring_size: bpy.props.IntProperty(name="Ring Size", default=15, min=9, max=20)
    text: bpy.props.StringProperty(name="Text", default="CH")
    begin: bpy.props.IntProperty(name="Begin", default=1, min=0, max=99999)
    end: bpy.props.IntProperty(name="End", default=100, min=0, max=99999)
    year: bpy.props.IntProperty(name="Year", default=datetime.datetime.now().year%100, min=0, max=99)
    zero_fill: bpy.props.IntProperty(name="Fill zeros", default=4, min=0, max=6) 

    def log(self, msg):
        log(msg)

    def define_rings(self):
        rings = []
        for i in range(self.begin, self.end+1):
            ring_texts = [self.text, str(self.ring_size), str(self.year), str(i).zfill(self.zero_fill)]
            text = " ".join(ring_texts)
            r = Ring.new(text, self.ring_size)
            rings.append(r)
        
        return rings


    def execute(self, context):
        # execute() is called when running the operator.
        self.log("Creating rings ...")
        rings = self.define_rings()

        self.log("Arranging ring layout ...")
        arrange_in_plane(rings)

        rf = RingFactory()
        rf.create_rings(context, rings)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
