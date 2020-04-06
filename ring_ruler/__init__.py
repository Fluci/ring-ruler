import bpy

from .ring_ruler import RingRulerOperator

bl_info = {
    "name": "RingRuler",
    "description": "Generate a list of rings with writing on them.",
    "author": "Felice Serena",
    "version": (0, 2, 0),
    "blender": (2, 81, 0),
    "wiki_url": "https://github.com/Fluci/ring-ruler",
    "tracker_url": "https://github.com/Fluci/ring-ruler/issues",
    "category": "Add Mesh",
    "location": "View3d > Object",
    "support": "COMMUNITY"
}

def menu_func(self, context):
    self.layout.operator(RingRulerOperator.bl_idname)

def register():
    """
    Turn on the add on.
    """
    bpy.utils.register_class(RingRulerOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    """
    Turn off the add on.
    """
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(RingRulerOperator)

