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
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.1, -0.1, 0.5),
        upper_bound=(0.1, 0.1, 0.6),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

########################## entities ##########################
# ground plane
plane = scene.add_entity(
    morph=gs.options.morphs.Plane(),
)

########################## build ##########################
scene.build()

########################## simulate ##########################
for i in range(500):
    scene.step()