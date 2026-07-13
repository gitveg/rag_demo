import genesis as gs

gs.init()

scene = gs.Scene(
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())
sand_pile = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0, 0, 1.0),
        radius=0.5,
        height=0.2,
    ),
    material=gs.materials.DEM(),
    particle_size=0.02,
)

scene.build()

while scene.viewer.is_alive():
    scene.step()
    scene.render()