import genesis as gs

gs.init()

scene = gs.Scene(renderer=gs.renderers.Viewer())
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.5))
sphere.color = (1.0, 0.0, 0.0)  # bright red

scene.build()

while True:
    scene.step()
    scene.viewer.render()