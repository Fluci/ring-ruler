import bpy  
import math
from mathutils import Vector

class RingPrototype:
    @classmethod
    def new(cls, ring_size=15):
        """
        Factory function: Creates new rings with most values hard coded to proper defaults.
        
        text: text to write on ring
        ring_size: "official" size in mm (a ring with 16 mm inner diameter fits a cylinder of 15 mm, 15 mm is expected to be passed in)
        """
        inner_radius = (ring_size-1)/2
        outer_radius = (ring_size+3)/2
        height = 8
        text_size = 8
        text_thickness = 0.15
        text_offset = Vector((0, 0, -(height-2)/2))
        scale = 0.001
        return cls(
            scale*ring_size, 
            scale*inner_radius, 
            scale*outer_radius, 
            scale*height, 
            scale*text_thickness, 
            scale*text_size,
            scale*text_offset)

    def __init__(self, 
            size, 
            inner_radius, 
            outer_radius, 
            height, 
            text_thickness, 
            text_size,
            text_offset):
        self.location = Vector((-size, -size, -size))
        self.size = size
        self.text_size = text_size
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.height = height
        self.text_thickness = text_thickness
        self.text_offset = text_offset
        self.bounding_box = Vector((2*outer_radius + 2*text_thickness, 2*outer_radius + 2*text_thickness, height))
        self.ring_resolution = 96
        self.bevel_resolution = 1
        self.text_resolution = 24
        self.bevel_depth = 0.0002
        self.baked = False

    def bake(self, context):
        if self.baked:
            return
        self.baked = True

        text_location = self.location + self.text_offset

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=self.ring_resolution,
            radius=self.inner_radius, 
            depth=self.height*1.3, 
            enter_editmode=False, 
            location=self.location)
        self.inside = context.selected_objects[0]
        self.inside.name = "Inside"

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=self.ring_resolution,
            radius=self.outer_radius, 
            depth=self.height, 
            enter_editmode=False, 
            location=self.location)
        self.outside = context.selected_objects[0]
        self.outside.name = "Outside"

        bpy.ops.curve.primitive_bezier_circle_add(
            radius=self.outer_radius, 
            enter_editmode=False, 
            location=text_location)
        self.curve = context.selected_objects[0]

        bpy.ops.object.text_add(
            enter_editmode=False, 
            location=text_location)
        self.text_obj = context.selected_objects[0]
        self.text_obj.data.extrude = self.text_thickness
        self.text_obj.data.bevel_depth = self.bevel_depth 
        self.text_obj.data.bevel_resolution = self.bevel_resolution
        self.text_obj.data.size = self.text_size
        self.text_obj.data.resolution_u = self.text_resolution
        self.text_obj.select_set(False)

        self.connect_objects(context)
        self.merge_objects(context)
        self.base = self.outside
        self.base.name = "RingBase"

    def connect_objects(self, context):
        """
        Sets up any needed modifiers between objects but doesn't apply them.
        """
        # Poke hole in ring
        m = self.outside.modifiers.new(name="boolean_inner", type="BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = self.inside

        # Give text more geometry for better bending
        m = self.text_obj.modifiers.new(name="remesh", type="REMESH")
        m.octree_depth = 8
        m.use_remove_disconnected = False

        # Fix text to ring curve
        self.text_obj.rotation_euler.x = math.pi
        m = self.text_obj.modifiers.new(name="curve", type="CURVE")
        m.deform_axis = "NEG_X"
        m.object = self.curve

    def merge_objects(self, context):

        override = context
        override.view_layer.objects.active = self.outside
        # Poke hole in ring
        self.outside.select_set(True)
        r = bpy.ops.object.modifier_apply(apply_as="DATA", modifier="boolean_inner")
        assert "FINISHED" in r
        self.outside.select_set(False)
        
        delete_objects = [self.inside]
        bpy.ops.object.delete({"selected_objects": delete_objects})


class InstancedRing:
    @classmethod
    def new(cls, text: str, prototype):
        """
        text: text to write on ring
        """
        location = Vector((0,0,0))
        return cls(text, location, prototype)

    def __init__(self, text, location, prototype):
        self.text = text
        self.location = location
        self.prototype = prototype
    
    @property
    def size(self):
        return self.prototype.size

    @property
    def inner_radius(self):
        return self.prototype.inner_radius

    @property
    def outer_radius(self):
        return self.prototype.outer_radius

    @property
    def height(self):
        return self.prototype.height

    @property
    def bounding_box(self):
        return self.prototype.bounding_box

    def create_objects(self, context):
        self.prototype.bake(context)
        text_location = self.location + self.prototype.text_offset
        
        self.base = self.prototype.base.copy()
        self.base.location = self.location

        self.curve = self.prototype.curve.copy()
        self.curve.location = text_location
        # For some strange reason, the convert_to_mesh step
        # is a lot faster, if we perform a copy of the data
        self.curve.data = self.curve.data.copy() # deep copy

        self.text_obj = self.prototype.text_obj.copy()
        self.text_obj.data = self.text_obj.data.copy() # deep copy
        self.text_obj.data.body = self.text
        self.text_obj.location = text_location
        self.text_obj.modifiers["curve"].object = self.curve

        context.collection.objects.link(self.base)
        context.collection.objects.link(self.curve)
        context.collection.objects.link(self.text_obj)

        self.objects = [self.base, self.curve, self.text_obj]

    def add_text_modifiers(self, context):
        return
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
        #me = self.text_obj.to_mesh()
        #bpy.data.objects.new("text_mesh", me)
        context.view_layer.objects.active = self.text_obj
        self.text_obj.select_set(True)
        bpy.ops.object.convert(target="MESH")
        ## Check normals
        # bpy.ops.mesh.normals_make_consistent()
        # bpy.ops.mesh.print3d_clean_non_manifold()
        self.text_obj.select_set(False)

    def get_base_object(self):
        return self.text_obj

    def get_subtract_objects(self):
        return []

    def get_add_objects(self):
        return [self.base]

