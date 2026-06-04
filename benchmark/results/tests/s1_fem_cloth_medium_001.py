"""
User Query: Create a rectangular piece of cloth pinned at its four corners. Let it sag under gravity, then release two corners and watch it swing down.
task_id: s1_fem_cloth_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.9, 1.0)),
)

cloth = scene.add_entity(
    gs.morphs.Mesh(
        file="meshes/cloth.obj",
        pos=(0.0, 0.0, 1.4),
        scale=1.2,
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Rough(color=(0.7, 0.2, 0.2, 1.0)),
)

camera = scene.add_camera(
    pos=(2.2, -2.0, 1.6),
    lookat=(0.0, 0.0, 0.9),
    res=(1280, 720),
    fov=45,
)

scene.build()

corner_local_positions = [
    (-0.5, -0.5, 0.0),
    (-0.5,  0.5, 0.0),
    ( 0.5, -0.5, 0.0),
    ( 0.5,  0.5, 0.0),
]

pins = []
for p in corner_local_positions:
    try:
        pin = cloth.pin_particle(pos_local=p)
    except Exception:
        try:
            pin = cloth.pin_vertex(pos_local=p)
        except Exception:
            pin = cloth.pin(pos_local=p)
    pins.append(pin)

for _ in range(200):
    scene.step()

for idx in [2, 3]:
    pin = pins[idx]
    try:
        cloth.unpin_particle(pin)
    except Exception:
        try:
            cloth.unpin_vertex(pin)
        except Exception:
            try:
                cloth.unpin(pin)
            except Exception:
                try:
                    pin.release()
                except Exception:
                    pass

for _ in range(400):
    scene.step()