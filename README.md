# Viewport Selection Sets

<img width="234" height="327" alt="SelectionSets_01" src="https://github.com/user-attachments/assets/43af2b66-df50-4872-a673-9073bfa0063a" />

**Version:** 1.1.0  
**Supported Blender versions:** Blender 3.6 LTS through Blender 5.2  


A lightweight Blender add-on for creating named sets of objects and managing them from the 3D Viewport's right-hand N-panel.

## Features

- Create a named selection set from the currently selected objects.
- Rename sets by editing their names directly in the list.
- Add the current object selection to the active set.
- Remove selected objects from the active set without deleting the objects.
- Select all members of a set and deselect other objects.
- Hide or unhide all objects in a set in the viewport.
- Quick Select, Hide, and Unhide buttons on every set-list row.
- Store sets per scene and save them inside the `.blend` file.
- Use object references rather than names, so renaming an object normally does not break set membership.

## Installation

### Option A — Install from the Python file

1. Download `viewport_selection_sets.py` from this repository.
2. Open Blender and choose **Edit → Preferences**.
3. Open the **Add-ons** section.
4. Click **Install from Disk** or **Install** (the label can vary by Blender build).
5. Select `viewport_selection_sets.py`.
6. Enable **Viewport Selection Sets** if it is not already enabled.
7. Move the pointer over the 3D Viewport and press `N`.
8. Open the **Selection Sets** tab.

Some newer Blender builds emphasize the Extensions workflow. If the legacy add-on installer is not immediately visible, check the Preferences add-on/extension menus for the legacy/script installation option available in that build.

### Option B — Install by copying the file

1. Locate Blender's user scripts directory. Its location varies by operating system and Blender version; the path can be checked in Preferences under **File Paths** or in Blender's documentation.
2. Create an `addons` directory inside the user scripts directory if it does not exist.
3. Copy `viewport_selection_sets.py` into that `addons` directory.
4. Restart Blender.
5. Open Preferences → Add-ons and enable **Viewport Selection Sets**.
6. In the 3D Viewport, press `N` and open the **Selection Sets** tab.

### Option C — Run from Blender's Text Editor (testing only)

1. Open `viewport_selection_sets.py` in Blender's Text Editor.
2. Click **Run Script**.
3. Open the 3D Viewport, press `N`, and select the **Selection Sets** tab.

Running from the Text Editor is convenient for testing but is not a persistent installation; the script may need to be run again after restarting Blender.

## How to use it

### Create a set

1. Select one or more objects in the 3D Viewport.
2. Open **N → Selection Sets**.
3. Click the `+` button next to the set list.
4. Enter a name and confirm.

The new set contains the objects selected at creation time.

### Rename a set

Click the set name in the list and edit the text field directly. Confirm the edit by pressing Enter or clicking elsewhere in the interface.

### Add objects to an existing set

1. Select the target set in the list.
2. Select the additional objects in the viewport.
3. Click **Add Selected**.

Objects already included in the set are not added again.

### Remove objects from a set

1. Select the target set in the list.
2. Select the objects to remove in the viewport.
3. Click **Remove Selected**.

This only removes those objects from the set; it does not delete them from the scene.

### Select a set

Choose a set and click **Select**, or click the selection icon on that set's row. The add-on deselects other objects and selects members available in the current view layer. Hidden members are unhidden before selection where possible.

### Hide or unhide a set

Use **Hide** or **Unhide** below the list, or the visibility icons on the set's row. This changes viewport visibility using Blender's `Object.hide_set()` behavior; it does not disable rendering.

### Delete a set

Click the `−` button beside the list. Only the set definition is removed. The objects themselves remain in the scene.

## How it works

The add-on uses Blender's Python API and registers:

- `PropertyGroup` types to define sets and object references.
- A `CollectionProperty` on `bpy.types.Scene` to store sets per scene.
- A `PointerProperty` for each set member, pointing to an object datablock.
- Operators for set creation/deletion, membership edits, selection, hiding and unhiding.
- A `UIList` and `Panel` to display the controls in the N-panel.

Selection sets are saved in the `.blend` file. The add-on Python file itself must remain installed and enabled to provide its interface and operations.

## Compatibility and testing

The add-on targets Blender **3.6 LTS through 5.2** and uses established Python API components for add-ons, properties, operators and viewport UI. Blender 5.2 documents the core `PropertyGroup` and add-on registration APIs, but this project has not been runtime-tested in every supported Blender build or operating system. Test it on a copy of a production file before using it in a critical pipeline.

## Known behavior and limitations

- Sets are stored per scene, not globally across all scenes.
- Sets contain object references, not collections, vertices, faces or other components.
- Hide/Unhide affects viewport visibility, not render visibility.
- Collection exclusion, linked-library restrictions, or objects outside the active view layer can limit selection/visibility operations.
- Deleting an object may leave an empty pointer entry, which is ignored by the add-on's object-list helper.
- Compatibility is intended for Blender 3.6–5.2, but not every version has been tested in a live Blender session.

## Repository layout

```text
viewport-selection-sets/
├── viewport_selection_sets.py
├── README.md
└── LICENSE  # Add a license before publishing if you want to grant reuse rights.
```


## License

GNU General Public License v3.0
