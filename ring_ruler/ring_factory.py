import bpy
from .utils import log


class RingFactory:
    def log(self, msg):
        log(msg)

    def create_rings(self, context, rings):
        
        self.log("Creating rings ...")
        for r in rings:
            r.create_objects(context)
        
        context.view_layer.objects.active = None

        self.log("Connect objects ...")
        for r in rings:
            r.add_text_modifiers(context)
        
        self.log("Convert parts to mesh ...")
        for r in rings:
            r.convert_to_mesh(context)

        self.log("Join parts ...")
        parts = self.join_ring_objects(context, rings)

        self.log("Merge parts ...")
        delete_objects = self.merge_ring_objects(context, parts["base"], parts["subtracts"], parts["adds"])

        # clean up
        for r in rings:
            delete_objects.append(r.curve)
        
        self.log("Delete objects ...")
        bpy.ops.object.delete({"selected_objects": delete_objects})

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
        override = context.copy()
        override["active_object"] = base

        for add in adds:
            m = base.modifiers.new(name="boolean_add", type="BOOLEAN")
            m.operation = "UNION"
            m.object = add
            bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_add")
        
        for sub in subtracts:
            m = base.modifiers.new(name="boolean_sub", type="BOOLEAN")
            m.operation = "DIFFERENCE"
            m.object = sub
            bpy.ops.object.modifier_apply(override, apply_as="DATA", modifier="boolean_sub")
            
        delete_objects = subtracts + adds
        return delete_objects

      
