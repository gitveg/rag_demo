import os
import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(1280, 720),
        max_FPS=60,
    ),
    show_viewer=True,
)

########################## entities ##########################
# Ground plane to catch anything that falls through
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Round dining table - using a disk-like cylinder (radius 0.6m, height 0.05m)
# Note: Cylinder morph is assumed to be available in genesis.morphs
table = scene.add_entity(
    morph=gs.morphs.Cylinder(
        radius=0.6,
        height=0.05,
        pos=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(rho=500.0),
    surface=gs.options.surfaces.Default(
        color=(0.8, 0.6, 0.4),  # wood-like
    ),
)

# Large tablecloth (2.4m x 2.4m) placed above the table, dropped from a height
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="cloth_rectangle.obj",  # user must provide a rectangular mesh file
        scale=2.4,
        pos=(0.0, 0.4, 0.0),  # slightly above the table top
    ),
    material=gs.materials.PBD.Cloth(
        rho=4.0,
        stretch_compliance=1e-7,
        bending_compliance=1e-5,
        air_resistance=0.001,
    ),
    surface=gs.options.surfaces.Default(
        color=(0.9, 0.2, 0.2),  # red cloth
    ),
)

########################## build ##########################
scene.build()

########################## simulate ##########################
for i in range(1000):
    scene.step()