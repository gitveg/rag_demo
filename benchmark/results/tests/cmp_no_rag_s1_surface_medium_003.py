import genesis as gs

# Initialize Genesis
gs.init()

# Create scene
scene = gs.Scene()

# Define materials
shiny_metallic_silver = gs.materials.Metal(
    color=(0.85, 0.85, 0.85),  # silver
    roughness=0.2,             # low roughness for shiny finish
)

matte_blue_plastic = gs.materials.Plastic(
    color=(0.1, 0.2, 0.8),     # blue
    roughness=0.8,             # high roughness for matte finish
)

# Spawn cube (box)
scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(1.0, 1.0, 1.0)),
    material=shiny_metallic_silver,
)

# Spawn cylinder
scene.add_entity(
    morph=gs.morphs.Cylinder(pos=(1.5, 0.0, 0.5), radius=0.5, height=1.0),
    material=matte_blue_plastic,
)

# Build the scene (finalize)
scene.build()

# Set a default camera view and start the interactive viewer
scene.viewer.set_camera_pose((2.0, 2.0, 2.0), (0.75, 0.0, 0.5))
scene.viewer.start()