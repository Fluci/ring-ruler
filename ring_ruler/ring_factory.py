import bpy
import bmesh
from .utils import log

def triangulate_object(obj):
    ## https://blender.stackexchange.com/questions/45698/triangulate-mesh-in-python
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    bm.free()

class RingFactory:
    def __init__(self, vector_merge = True):
        self.vector_merge = vector_merge

    def log(self, msg):
        log(msg)

    def create_rings(self, context, rings):
        
        self.log("Creating rings ...")
        for r in rings:
            r.create_objects(context)
        
        context.view_layer.objects.active = None
        bpy.ops.object.select_all(action='DESELECT')

        self.log("Connect objects ...")
        for r in rings:
            r.add_text_modifiers(context)
        
        self.log("Convert parts to mesh ...")
        bpy.ops.object.select_all(action='DESELECT')
        for r in rings:
            r.convert_to_mesh(context)

        context.view_layer.objects.active = None
        bpy.ops.object.select_all(action='DESELECT')

        if self.vector_merge:
            self.log("Join parts ...")
            parts = self.join_ring_objects(context, rings)

            self.log("Merge parts ...")
            delete_objects = self.merge_ring_objects(context, parts["base"], parts["subtracts"], parts["adds"])
            base = parts["base"]
        else:
            self.log(f"Merge parts of {len(rings)} rings ...")
            delete_objects = []
            bases = []
            for r in rings:
                base = r.get_base_object()
                subs = r.get_subtract_objects()
                adds = r.get_add_objects()
                ds = self.merge_ring_objects(context, base, subs, adds)
                bases.append(base)
                delete_objects.extend(ds)

            self.log("Join rings ...")
            base = self.join_objs(bases)
            base.name = "rings"

        # clean up
        for r in rings:
            delete_objects.append(r.curve)
        
        self.log("Delete objects ...")
        bpy.ops.object.delete({"selected_objects": delete_objects})

        # Polish base
        self.log("Polish rings ...")
        triangulate_object(base)

        self.log("Done.")
        context.view_layer.objects.active = None        


    def join_objs(self, objs):
        for b in objs:
            b.select_set(True)

        bpy.ops.object.join({"active_object": objs[0], "selected_objects": objs})
        objs[0].select_set(False)
        return objs[0]
        
        
    def transpose_object_matrix(self, objects):
        t = []
        for objs in objects:
            for i, obj in enumerate(objs):
                if len(t) <= i:
                    t.append([])
                t[i].append(obj)
        return t
        
    def join_ring_objects(self, context, rings):
        base_objects = []
        subtract_objects = []
        add_objects = []
        
        for r in rings:
            base_objects.append(r.get_base_object())
            subtract_objects.append(r.get_subtract_objects())
            add_objects.append(r.get_add_objects())

        bpy.ops.object.select_all(action='DESELECT')
        base = self.join_objs(base_objects)

        # Transpose
        subtracts = self.transpose_object_matrix(subtract_objects)
        adds = self.transpose_object_matrix(add_objects)

        for i, sub in enumerate(subtracts):
            subtracts[i] = self.join_objs(sub)

        for i, add in enumerate(adds):
            adds[i] = self.join_objs(add)
        
        # Use modifier to merge everything into one model
        
        return {
            "base": base,
            "subtracts": subtracts,
            "adds": adds
            }

    def merge_ring_objects(self, context, base, subtracts, adds):        
        """
        Modifies base such that base := (base + adds) - subs
        """
        override = context.copy()
        override["active_object"] = base

        if True:
            all_objs = [base]
            all_objs.extend(adds)
            self.join_objs(all_objs)
        else:
            for add in adds:
                m = base.modifiers.new(name="boolean_add", type="BOOLEAN")
                m.operation = "UNION"
                m.object = add
                r = bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_add")
                assert "FINISHED" in r
        
        for sub in subtracts:
            m = base.modifiers.new(name="boolean_sub", type="BOOLEAN")
            m.operation = "DIFFERENCE"
            m.object = sub
            bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_sub")
            assert "FINISHED" in r
            
        delete_objects = subtracts + adds
        return delete_objects

      
