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
# Ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Horizontal pole (rigid cylinder)
pole = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="cylinder.obj",
        pos=(0.0, 0.5, 0.0),
        scale=(0.05, 0.05, 1.0),  # thin, long cylinder
    ),
    material=gs.materials.Rigid(),
)

# Rectangular cloth (PBD) – initial position above the pole so that it drapes over both sides
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="cloth.obj",  # rectangular mesh (e.g., a flat sheet)
        pos=(0.0, 1.0, 0.0),
        scale=(0.8, 0.8, 1.0),
    ),
    material=gs.materials.PBD.Cloth(),
)

########################## build ##########################
scene.build()

########################## run ##########################
for i in range(1000):
    scene.step()