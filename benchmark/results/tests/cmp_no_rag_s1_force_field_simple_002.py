import genesis as gs

gs.init()

scene = gs.Scene()

# Fixed suspension point (small sphere)
base = scene.add_entity(
    gs.morphs.Sphere(radius=0.02),
    pos=(0, 0, 0),
    fixed=True,
)

# Lightweight sphere pendulum
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.1),
    pos=(0, -0.5, 0),
    material=gs.materials.Rigid(mass=0.1),
)

# Revolute joint at suspension point, allowing sway in the XY plane
joint = scene.add_joint(
    gs.joints.RevoluteJoint(
        entity_a=base,
        entity_b=sphere,
        pos=(0, 0, 0),
        axis=(0, 0, 1),
    ),
)

scene.build()

# Constant sideways wind force along x-axis
wind = [0.5, 0, 0]

for _ in range(1000):
    sphere.add_force(force=wind)
    scene.step()