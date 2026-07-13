import numpy as np
import genesis as gs
from tqdm import tqdm

def main():
    gs.init(backend=gs.gpu, precision='32', logging_level='info')

    # Container dimensions (interior)
    L, W, H = 0.5, 0.3, 0.4           # length, width, height (walls above bottom)
    water_height = 0.3                 # water fill level

    # Scene with solvers for MPM (water) and rigid (sphere, walls)
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.3, -0.2, -0.1),
            upper_bound=(0.3, 0.2, 1.0),
        ),
        rigid_options=gs.options.RigidOptions(
            gravity=(0, 0, -9.8),
            enable_collision=True,
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.5, -1.5, 0.8),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Container walls (static rigid planes)
    # Bottom
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(0, 0, 0), normal=(0, 0, 1)),
        material=gs.materials.Rigid(),
    )
    # Left wall (x = -L/2)
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(-L/2, 0, H/2), normal=(1, 0, 0)),
        material=gs.materials.Rigid(),
    )
    # Right wall (x = L/2)
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(L/2, 0, H/2), normal=(-1, 0, 0)),
        material=gs.materials.Rigid(),
    )
    # Front wall (y = W/2)
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(0, W/2, H/2), normal=(0, -1, 0)),
        material=gs.materials.Rigid(),
    )
    # Back wall (y = -W/2)
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(0, -W/2, H/2), normal=(0, 1, 0)),
        material=gs.materials.Rigid(),
    )

    # Water block (MPM liquid)
    water_morph = gs.options.morphs.Box(
        pos=(0, 0, water_height / 2),
        size=(L - 0.02, W - 0.02, water_height),  # slightly smaller to avoid wall overlap
    )
    water_material = gs.materials.MPM.Liquid(
        rho=1000.0,
        viscous=False,
    )
    scene.add_entity(morph=water_morph, material=water_material)

    # Rigid sphere dropped from above water
    sphere_morph = gs.options.morphs.Sphere(
        pos=(0, 0, 0.5),
        radius=0.05,
    )
    sphere_material = gs.materials.Rigid(
        rho=200.0,
    )
    scene.add_entity(morph=sphere_morph, material=sphere_material)

    # Build the scene
    scene.build()

    # Simulate for 2 seconds (1000 steps at dt=4e-3)
    for _ in tqdm(range(500), desc='Simulating'):
        scene.step()

if __name__ == '__main__':
    main()