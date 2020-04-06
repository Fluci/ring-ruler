import bpy  
import math
from mathutils import Vector

class RingPrototype:
    @classmethod
    def new(cls, height=8, ring_size=15, scale=0.0001, font_regular=None):
        """
        Factory function: Creates new rings with most values hard coded to proper defaults.
        
        text: text to write on ring
        ring_size: A ring of size x has an inner diameter of x mm and an outer diameter of x+3 mm. The Wall thickness is 1.5mm.
        scale: helper to convert from input values of mm to blender units.
        """
        inner_radius = ring_size/2
        outer_radius = (ring_size+3)/2
        text_size = height*7/8
        text_thickness = ring_size/100
        text_offset = Vector((0, 0, -height*0.25))
        year_offset = Vector((0, 0, -height*0.37))
        year_size = height*0.75
        return cls(
            scale*ring_size, 
            scale*inner_radius, 
            scale*outer_radius, 
            scale*height, 
            scale*text_thickness, 
            scale*text_size,
            scale*year_size,
            scale*text_offset,
            scale*year_offset,
            font_regular)

    def __init__(self, 
            size, 
            inner_radius, 
            outer_radius, 
            height, 
            text_thickness, 
            text_size,
            year_size,
            text_offset,
            year_offset,
            font_regular):
        self.location = Vector((-size, -size, -size))
        self.size = size
        self.text_size = text_size
        self.year_size = year_size
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.height = height
        self.text_thickness = text_thickness
        self.text_offset = text_offset
        self.year_offset = year_offset
        self.bounding_box = Vector((2*outer_radius + 2*text_thickness, 2*outer_radius + 2*text_thickness, height))
        self.ring_resolution = 96
        self.bevel_resolution = 1
        self.text_resolution = 24
        self.bevel_depth = 0.0002
        self.font_regular = font_regular
        self.baked = False

    def bake(self, context):
        if self.baked:
            return
        self.baked = True

        text_location = self.location + self.text_offset
        year_location = self.location + self.year_offset

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

        ## Add generic text
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
        self.text_obj.data.body = "Some text 0123"
        self.text_obj.data.resolution_u = self.text_resolution
        self.text_obj.rotation_euler.x = math.pi
        if self.font_regular != None:
            self.text_obj.data.font = self.font_regular

        self.text_obj.select_set(False)

        ## Add year
        bpy.ops.curve.primitive_bezier_circle_add(
                radius=self.outer_radius,
                enter_editmode=False,
                location=year_location)
        self.year_curve = context.selected_objects[0]
        self.year_curve.rotation_euler.z = -0.22

        bpy.ops.object.text_add(
                enter_editmode=False,
                location=year_location)
        self.year_obj = context.selected_objects[0]
        self.year_obj.data.extrude = self.text_thickness
        self.year_obj.data.bevel_depth = self.bevel_depth 
        self.year_obj.data.bevel_resolution = self.bevel_resolution
        self.year_obj.data.size = self.year_size
        self.year_obj.data.body = "21"
        self.year_obj.data.resolution_u = self.text_resolution
        self.year_obj.rotation_euler.x = math.pi
        self.year_obj.rotation_euler.z = -math.pi/2 - 0.22
        if self.font_regular != None:
            self.year_obj.data.font = self.font_regular
        self.year_obj.select_set(False)


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
        m = self.text_obj.modifiers.new(name="curve", type="CURVE")
        m.deform_axis = "NEG_X"
        m.object = self.curve

        # Give year more geometry for better bending
        m = self.year_obj.modifiers.new(name="remesh", type="REMESH")
        m.octree_depth = 8
        m.use_remove_disconnected = False

        # Fix year to ring curve
        m = self.year_obj.modifiers.new(name="curve", type="CURVE")
        m.deform_axis = "NEG_X"
        m.object = self.year_curve

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
    def new(cls, text: str, year: str, prototype):
        """
        text: text to write on ring
        """
        location = Vector((0,0,0))
        return cls(text, year, location, prototype)

    def __init__(self, text, year, location, prototype):
        self.text = text
        self.year = year
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
        year_location = self.location + self.prototype.year_offset
        
        ## Add base geometry
        self.base = self.prototype.base.copy()
        self.base.location = self.location

        ## Add generic text
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

        
        ## Add Year Text
        self.year_curve = self.prototype.year_curve.copy()
        self.year_curve.location = year_location
        self.year_curve.data = self.year_curve.data.copy() # deep copy

        self.year_obj = self.prototype.year_obj.copy()
        self.year_obj.data = self.year_obj.data.copy() # deep copy
        self.year_obj.data.body = self.year
        self.year_obj.location = year_location
        self.year_obj.modifiers["curve"].object = self.year_curve

        context.collection.objects.link(self.base)
        context.collection.objects.link(self.curve)
        context.collection.objects.link(self.text_obj)
        context.collection.objects.link(self.year_curve)
        context.collection.objects.link(self.year_obj)

    def add_text_modifiers(self, context):
        return
        
    def convert_to_mesh(self, context):
        convert_text_to_mesh(context, self.text_obj)
        convert_text_to_mesh(context, self.year_obj)

    def get_base_object(self):
        return self.text_obj

    def get_subtract_objects(self):
        return []

    def get_add_objects(self):
        return [self.base, self.year_obj]

def convert_text_to_mesh(context, text):
        #me = self.text_obj.to_mesh()
        #bpy.data.objects.new("text_mesh", me)
        context.view_layer.objects.active = text
        text.select_set(True)
        bpy.ops.object.convert(target="MESH")
        ## Check normals
        # bpy.ops.mesh.normals_make_consistent()
        # bpy.ops.mesh.print3d_clean_non_manifold()
        text.select_set(False)

