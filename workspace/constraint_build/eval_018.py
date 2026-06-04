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
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-1.0, -0.5, -0.5),
        upper_bound=(1.0, 1.0, 1.0),
    ),
    vis_options=gs.options.VisOptions(
        visualize_mpm_boundary=True,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(960, 640),
    ),
    show_viewer=True,
)

########################## create entities ##########################
# ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

# bathtub mesh (static rigid)
# Assumes a mesh file named 'bathtub.obj' exists in the working directory.
# Alternatively, replace with a box approximation as a placeholder.
bathtub = scene.add_entity(
    morph=gs.morphs.Mesh(file='bathtub.obj'),
    material=gs.materials.Rigid(),
)

# MPM liquid volume poured from above into the bathtub
liquid = scene.add_entity(
    morph=gs.morphs.Box(
        lower=(0.0, 0.4, -0.2),
        upper=(0.6, 0.6, 0.2),
    ),
    material=gs.materials.MPM.Liquid(),
)

########################## build the scene ##########################
scene.build()

########################## run simulation ##########################
for i in range(500):
    scene.step()