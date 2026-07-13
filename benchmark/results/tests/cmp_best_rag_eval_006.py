import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 3.0, 3.0),
        camera_lookat=(0.0, 0.0, 1.0),
    ),
    show_viewer=True,
)

# Ground plane
scene.add_entity(gs.morphs.Plane())

# Two spheres side by side
scene.add_entity(
    gs.morphs.Sphere(pos=(-0.5, 0.0, 2.0), radius=0.3)
)
scene.add_entity(
    gs.morphs.Sphere(pos=(0.5, 0.0, 2.0), radius=0.3)
)

scene.build()

# Run the simulation for a few seconds
for _ in range(1000):
    scene.step()