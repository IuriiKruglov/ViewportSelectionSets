"""Viewport Selection Sets — Blender 3.6 LTS through Blender 5.2.

PURPOSE
    Manage named groups of object references from the 3D Viewport's N-panel.

FEATURES
    * Create a set from the current selection and give it a name.
    * Rename a set by editing its name directly in the list.
    * Add selected objects to, or remove them from, the active set.
    * Select a set's members, hiding/unhiding members in the viewport.
    * Delete a set definition without deleting any scene objects.

IMPLEMENTATION NOTES
    Selection sets are stored as a Scene CollectionProperty, so each scene has
    its own sets and the data is saved inside the .blend file. Every membership
    entry uses a PointerProperty to reference an Object datablock rather than
    relying only on its name; object renaming therefore normally preserves the
    reference. Deleting an object can leave an empty pointer, which is ignored.

    Hide/unhide uses Object.hide_set(), which affects viewport visibility in
    the current view layer and does not control render visibility. Objects
    excluded from the active view layer may not be selectable from this panel.

COMPATIBILITY
    The add-on intentionally uses established Blender Python API components:
    Panel, Operator, UIList, PropertyGroup, CollectionProperty and
    PointerProperty. It is written for Blender 3.6 through 5.2, but should be
    tested in each target Blender build before use in a production project.
"""

bl_info = {
    "name": "Viewport Selection Sets",
    "author": "Kruglov Iurii and ChatGPT",
    "version": (1, 1, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport > Sidebar (N) > Selection Sets",
    "description": "Create and manage named sets of objects in the 3D Viewport",
    "category": "3D View",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy.props import (
    CollectionProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


# ---------------------------------------------------------------------------
# Helpers shared by UI drawing and operators
# ---------------------------------------------------------------------------
def active_set(context):
    """Return the selected set, or None if the list/index is empty or invalid."""
    scene = context.scene
    if not scene.vss_sets:
        return None
    index = scene.vss_active_index
    if index < 0 or index >= len(scene.vss_sets):
        return None
    return scene.vss_sets[index]


def set_objects(selection_set):
    """Return unique, valid object references stored in a set.

    Object pointers can become empty when users delete objects elsewhere.
    Filter those entries out so all operators can safely use this helper.
    """
    """Return unique, existing objects referenced by a selection set."""
    result = []
    seen = set()
    for item in selection_set.objects:
        obj = item.object
        if obj is not None and obj.name in bpy.data.objects and obj.name not in seen:
            result.append(obj)
            seen.add(obj.name)
    return result


# ---------------------------------------------------------------------------
# Data model: one pointer per member, and a named collection of members
# ---------------------------------------------------------------------------
class VSS_ObjectRef(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object included in this selection set",
    )


class VSS_SelectionSet(PropertyGroup):
    name: StringProperty(name="Set Name", default="Selection Set")
    objects: CollectionProperty(type=VSS_ObjectRef)


# ---------------------------------------------------------------------------
# Operators: create/delete sets and edit set membership
# ---------------------------------------------------------------------------
class VSS_OT_new_set(Operator):
    bl_idname = "vss.new_set"
    bl_label = "Create Set from Selection"
    bl_description = "Create a selection set containing the currently selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Name", default="Selection Set")

    def execute(self, context):
        # Capture the current selection before creating the set. An empty
        # selection is rejected so users do not accidentally create an empty set.
        selected = list(context.selected_objects)
        if not selected:
            self.report({'WARNING'}, "Select at least one object first")
            return {'CANCELLED'}

        scene = context.scene
        item = scene.vss_sets.add()
        item.name = self.name.strip() or "Selection Set"
        for obj in selected:
            ref = item.objects.add()
            ref.object = obj
        scene.vss_active_index = len(scene.vss_sets) - 1
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Selection Set"
        return context.window_manager.invoke_props_dialog(self)


class VSS_OT_delete_set(Operator):
    bl_idname = "vss.delete_set"
    bl_label = "Delete Selection Set"
    bl_description = "Delete the active selection set without deleting its objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        index = scene.vss_active_index
        if index < 0 or index >= len(scene.vss_sets):
            return {'CANCELLED'}
        scene.vss_sets.remove(index)
        scene.vss_active_index = min(max(0, index - 1), len(scene.vss_sets) - 1)
        return {'FINISHED'}


class VSS_OT_add_selected(Operator):
    bl_idname = "vss.add_selected"
    bl_label = "Add Selected"
    bl_description = "Add currently selected objects to the active selection set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selection_set = active_set(context)
        if selection_set is None:
            self.report({'WARNING'}, "Create or select a set first")
            return {'CANCELLED'}

        # Compare Blender datablock pointers to avoid duplicate membership;
        # object names are not reliable identifiers because users can rename them.
        existing = {item.object.as_pointer() for item in selection_set.objects if item.object}
        added = 0
        for obj in context.selected_objects:
            if obj.as_pointer() not in existing:
                ref = selection_set.objects.add()
                ref.object = obj
                existing.add(obj.as_pointer())
                added += 1
        self.report({'INFO'}, f"Added {added} object(s)")
        return {'FINISHED'}


class VSS_OT_remove_selected(Operator):
    bl_idname = "vss.remove_selected"
    bl_label = "Remove Selected"
    bl_description = "Remove currently selected objects from the active set (does not delete objects)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selection_set = active_set(context)
        if selection_set is None:
            return {'CANCELLED'}
        selected_ptrs = {obj.as_pointer() for obj in context.selected_objects}
        removed = 0
        # Remove backwards through the collection so deleting an entry does not
        # shift the indices of entries that are still waiting to be checked.
        for i in range(len(selection_set.objects) - 1, -1, -1):
            obj = selection_set.objects[i].object
            if obj and obj.as_pointer() in selected_ptrs:
                selection_set.objects.remove(i)
                removed += 1
        self.report({'INFO'}, f"Removed {removed} object(s) from set")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Operators: select, hide and unhide all members of a set
# ---------------------------------------------------------------------------
class VSS_OT_select_set(Operator):
    bl_idname = "vss.select_set"
    bl_label = "Select Set"
    bl_description = "Select all objects in this set and deselect other objects"
    bl_options = {'REGISTER', 'UNDO'}

    set_index: IntProperty()

    def execute(self, context):
        scene = context.scene
        if self.set_index < 0 or self.set_index >= len(scene.vss_sets):
            return {'CANCELLED'}
        objects = set_objects(scene.vss_sets[self.set_index])

        # Unhide set members first so Blender can select them in the viewport.
        # This does not override collection exclusion or make objects outside
        # the active view layer available in that layer.
        for obj in objects:
            if obj.hide_get():
                obj.hide_set(False)
        # This operation replaces the current selection, rather than adding to it.
        for obj in context.view_layer.objects:
            obj.select_set(False)
        active = None
        for obj in objects:
            if obj.name in context.view_layer.objects:
                obj.select_set(True)
                active = obj
        if active:
            context.view_layer.objects.active = active
        return {'FINISHED'}


class VSS_OT_hide_set(Operator):
    bl_idname = "vss.hide_set"
    bl_label = "Hide Set"
    bl_description = "Hide all objects in this set in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    set_index: IntProperty()

    def execute(self, context):
        scene = context.scene
        if self.set_index < 0 or self.set_index >= len(scene.vss_sets):
            return {'CANCELLED'}
        for obj in set_objects(scene.vss_sets[self.set_index]):
            obj.hide_set(True)
        return {'FINISHED'}


class VSS_OT_unhide_set(Operator):
    bl_idname = "vss.unhide_set"
    bl_label = "Unhide Set"
    bl_description = "Unhide all objects in this set in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    set_index: IntProperty()

    def execute(self, context):
        scene = context.scene
        if self.set_index < 0 or self.set_index >= len(scene.vss_sets):
            return {'CANCELLED'}
        for obj in set_objects(scene.vss_sets[self.set_index]):
            obj.hide_set(False)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# User interface: a compact row per set and the right-hand N-panel
# ---------------------------------------------------------------------------
class VSS_UL_sets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        # The name field is editable in-place, which provides the rename feature.
        row.prop(item, "name", text="", emboss=False, icon='GROUP')
        op = row.operator("vss.select_set", text="", icon='RESTRICT_SELECT_OFF')
        op.set_index = index
        op = row.operator("vss.hide_set", text="", icon='HIDE_ON')
        op.set_index = index
        op = row.operator("vss.unhide_set", text="", icon='HIDE_OFF')
        op.set_index = index


class VIEW3D_PT_viewport_selection_sets(Panel):
    """Main panel registered in the 3D Viewport's N-sidebar."""
    bl_label = "Selection Sets"
    bl_idname = "VIEW3D_PT_viewport_selection_sets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Selection Sets"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            "VSS_UL_sets", "",
            scene, "vss_sets",
            scene, "vss_active_index",
            rows=4,
        )
        col = row.column(align=True)
        col.operator("vss.new_set", text="", icon='ADD')
        col.operator("vss.delete_set", text="", icon='REMOVE')

        selection_set = active_set(context)
        if selection_set:
            layout.label(text=f"Objects in set: {len(set_objects(selection_set))}")
            row = layout.row(align=True)
            row.operator("vss.add_selected", text="Add Selected", icon='ADD')
            row.operator("vss.remove_selected", text="Remove Selected", icon='REMOVE')
            row = layout.row(align=True)
            op = row.operator("vss.select_set", text="Select", icon='RESTRICT_SELECT_OFF')
            op.set_index = scene.vss_active_index
            op = row.operator("vss.hide_set", text="Hide", icon='HIDE_ON')
            op.set_index = scene.vss_active_index
            op = row.operator("vss.unhide_set", text="Unhide", icon='HIDE_OFF')
            op.set_index = scene.vss_active_index
        else:
            layout.label(text="Select objects, then click +", icon='INFO')


CLASSES = (
    VSS_ObjectRef,
    VSS_SelectionSet,
    VSS_OT_new_set,
    VSS_OT_delete_set,
    VSS_OT_add_selected,
    VSS_OT_remove_selected,
    VSS_OT_select_set,
    VSS_OT_hide_set,
    VSS_OT_unhide_set,
    VSS_UL_sets,
    VIEW3D_PT_viewport_selection_sets,
)


def register():
    """Register classes, then attach per-scene properties to Blender's Scene."""
    # Register PropertyGroup types first; Blender needs them defined before
    # CollectionProperty(type=...) can refer to them.
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    # Store the selection-set collection on each Scene so it is saved in .blend.
    bpy.types.Scene.vss_sets = CollectionProperty(type=VSS_SelectionSet)
    bpy.types.Scene.vss_active_index = IntProperty(default=0)


def unregister():
    """Remove Scene properties before unregistering the classes they depend on."""
    del bpy.types.Scene.vss_active_index
    del bpy.types.Scene.vss_sets
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
