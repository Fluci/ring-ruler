import bpy  
import math
from mathutils import Vector

class Ring:

    @classmethod
    def new(cls, text: str, ring_size=15):
        """
        Factory function: Creates new rings with most values hard coded to proper defaults.
        
        text: text to write on ring
        ring_size: "official" size in mm (a ring with 16 mm inner diameter fits a cylinder of 15 mm, 15 mm is expected to be passed in)
        """
        inner_radius = (ring_size-1)/2
        outer_radius = (ring_size+3)/2
        height = 8
        location = Vector((0,0,0))
        text_thickness = 0.15
        text_offset = Vector((0, 0, -(height-2)/2))
        return cls(
            ring_size, 
            inner_radius, 
            outer_radius, 
            height, 
            location, 
            text, 
            text_thickness, 
            text_offset)
    
    def __init__(self, 
            size, 
            inner_radius, 
            outer_radius, 
            height, 
            location, 
            text, 
            text_thickness, 
            text_offset):
        self.size = size
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.location = location
        self.height = height
        self.text = text
        self.text_thickness = text_thickness
        self.text_offset = text_offset
        self.bounding_box = Vector((2*outer_radius + 2*text_thickness, 2*outer_radius + 2*text_thickness, height))
    
    def create_objects(self, context):
        ring_resolution = 96
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=ring_resolution,
            radius=self.inner_radius, 
            depth=self.height+2, 
            enter_editmode=False, 
            location=self.location)
        self.inside = context.selected_objects[0]

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=ring_resolution,
            radius=self.outer_radius, 
            depth=self.height, 
            enter_editmode=False, 
            location=self.location)
        self.outside = context.selected_objects[0]
        text_location = self.location + self.text_offset

        bpy.ops.curve.primitive_bezier_circle_add(
            radius=self.outer_radius, 
            enter_editmode=False, 
            location=text_location)
        self.curve = context.selected_objects[0]
        
        bpy.ops.object.text_add(
            enter_editmode=False, 
            location=text_location)
        self.text_obj = context.selected_objects[0]
        self.text_obj.data.body = self.text
        self.text_obj.data.extrude = self.text_thickness
        self.text_obj.data.bevel_depth = 0.02
        self.text_obj.data.bevel_resolution = 1
        self.text_obj.data.size = 8
        self.text_obj.data.resolution_u = 24

        self.objects = [self.inside, self.outside, self.curve, self.text_obj]

    def add_text_modifiers(self, context):
        # Give text more geometry for better bending
        m = self.text_obj.modifiers.new(name="remesh", type="REMESH")
        m.octree_depth = 8
        m.use_remove_disconnected = False

        # Fix text to ring curve
        self.text_obj.rotation_euler.x = math.pi
        m = self.text_obj.modifiers.new(name="curve", type="CURVE")
        m.deform_axis = "NEG_X"
        m.object = self.curve
        
    def convert_to_mesh(self, context):
        # Crashes:
        #override = context.copy()
        #override["active_object"] = self.text_obj
        context.view_layer.objects.active = self.text_obj
        self.text_obj.select_set(True)
        bpy.ops.object.convert(target="MESH")

    def get_base_object(self):
        return self.outside

    def get_subtract_objects(self):
        return [self.inside]

    def get_add_objects(self):
        return [self.text_obj]

    def connect_objects(self, context):
        """
        Sets up any needed modifiers between objects but doesn't apply them.
        """
        # Poke hole in ring
        m = self.outside.modifiers.new(name="boolean_inner", type="BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = self.inside

    def merge_objects(self, context, should_delete_objects=True):
        override = context.copy()
        m = self.outside.modifiers.new(name="boolean_text", type="BOOLEAN")
        m.operation = "UNION"
        m.object = self.text_obj
        
        # Poke hole in ring
        override["active_object"] = self.outside
        bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_inner")
        bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_text")

        delete_objects = [self.inside, self.text_obj]
        if should_delete_objects:
            bpy.ops.object.delete({"selected_objects": delete_objects})
        else:
            return delete_objects

