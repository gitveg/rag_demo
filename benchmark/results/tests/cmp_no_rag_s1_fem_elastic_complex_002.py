import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(show_viewer=True)

# soft bunny material
soft_mat = gs.materials.FEM.Soft(E=1e5, nu=0.4, rho=1000)
# rigid metal material for platform and spheres
rigid_mat = gs.materials.Rigid(rho=7800)

# bunny mesh (scaled down to fit)
bunny = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/bunny.obj",
        scale=0.1,
        pos=(0.0, 0.2, 0.0)
    ),
    material=soft_mat,
)

# platform
platform = scene.add_entity(
    morph=gs.morphs.Plane(pos=(0.0, 0.0, 0.0)),
    material=rigid_mat,
)

# several rigid spheres dropped from different heights
heights = [1.0, 1.5, 2.0]
x_positions = [-0.3, 0.0, 0.3]
spheres = []
for h, x in zip(heights, x_positions):
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.05,
            pos=(x, h, 0.0)
        ),
        material=rigid_mat,
    )
    spheres.append(sphere)

scene.build()

# run simulation
for i in range(1000):
    scene.step()
    scene.viewer.render()