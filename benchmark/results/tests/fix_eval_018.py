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
        lower_bound=(-1.0, -1.0, 0.0),
        upper_bound=(1.0, 1.0, 1.5),
    ),
    vis_options=gs.options.VisOptions(
        visualize_mpm_boundary=True,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=40,
        res=(960, 640),
    ),
    show_viewer=True,
)

########################## entities ##########################

# Rigid ground plane
plane = scene.add_entity(
    morph=gs.options.morphs.Plane(),
)

# Bathtub mesh as a static rigid container
bathtub = scene.add_entity(
    morph=gs.options.morphs.Mesh(
        file="meshes/bathtub.obj",
        pos=(0.0, 0.0, 0.1),
        scale=0.5,
    ),
    material=gs.materials.Rigid(
        gravity_compensation=1.0,
    ),
    surface=gs.options.surfaces.Default(),
)

# MPM liquid volume poured from above
liquid = scene.add_entity(
    material=gs.materials.MPM.Liquid(
        rho=1.0,
        sampler="pbs-64",
    ),
    morph=gs.options.morphs.Box(
        pos=(0.0, 0.0, 0.8),
        size=(0.3, 0.3, 0.15),
    ),
    surface=gs.options.surfaces.Default(
        color=(0.4, 0.7, 1.0),
    ),
)

########################## build and run ##########################
scene.build()

for _ in range(600):
    scene.step()