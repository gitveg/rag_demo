import genesis as gs

gs.init(precision="32", logging_level="info")

scene = gs.Scene(
    rigid_options=gs.options.RigidOptions(),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 3.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=50,
    ),
    show_viewer=True,
)

# ground plane
scene.add_entity(gs.morphs.Plane())

# red sphere
scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 5.0),
        radius=0.5,
    ),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Diffuse(color=(1, 0, 0)),
)

scene.build()

for _ in range(500):
    scene.step()