import genesis as gs
import numpy as np

def main():
    # Initialize Genesis with 32-bit precision
    gs.init(precision="32", logging_level="info")

    # Create the scene
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1e-2,      # time step for SPH
            substeps=10,   # substeps for solver
        ),
        sph_options=gs.options.SPHOptions(
            lower_bound=(0.0, 0.0, 0.0),      # tank bottom
            upper_bound=(1.0, 1.0, 0.6),      # tank top
            particle_size=0.03,               # SPH particle spacing
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, -1.5, 1.2),      # camera position to see splash
            camera_lookat=(0.5, 0.5, 0.3),    # look at center of tank
            camera_fov=40,
            res=(960, 720),
        ),
        show_viewer=True,
    )

    # ----------------------------------------------------------------
    # 1. Floor (visual only, also acts as a rigid ground)
    # ----------------------------------------------------------------
    scene.add_entity(gs.morphs.Plane())

    # ----------------------------------------------------------------
    # 2. Tank walls (rigid, fixed)
    # ----------------------------------------------------------------
    wall_thickness = 0.05
    tank_w = 1.0   # inner width
    tank_d = 1.0   # inner depth
    tank_h = 0.6   # inner height

    # Left wall (x = 0)
    scene.add_entity(
        gs.morphs.Box(pos=(0.0, tank_d/2, tank_h/2), 
                       size=(wall_thickness, tank_d, tank_h),
                       fixed=True),
        material=gs.materials.Rigid(),
    )
    # Right wall (x = tank_w)
    scene.add_entity(
        gs.morphs.Box(pos=(tank_w, tank_d/2, tank_h/2), 
                       size=(wall_thickness, tank_d, tank_h),
                       fixed=True),
        material=gs.materials.Rigid(),
    )
    # Front wall (y = 0)
    scene.add_entity(
        gs.morphs.Box(pos=(tank_w/2, 0.0, tank_h/2), 
                       size=(tank_w, wall_thickness, tank_h),
                       fixed=True),
        material=gs.materials.Rigid(),
    )
    # Back wall (y = tank_d)
    scene.add_entity(
        gs.morphs.Box(pos=(tank_w/2, tank_d, tank_h/2), 
                       size=(tank_w, wall_thickness, tank_h),
                       fixed=True),
        material=gs.materials.Rigid(),
    )

    # ----------------------------------------------------------------
    # 3. Water block (SPH liquid)
    # Fill bottom part of the tank
    # ----------------------------------------------------------------
    water_height = 0.2
    water_block_size = (tank_w - 2*wall_thickness, 
                        tank_d - 2*wall_thickness, 
                        water_height)
    water_pos = (tank_w/2, tank_d/2, water_height/2 + wall_thickness)  # offset by wall thickness

    scene.add_entity(
        gs.morphs.Box(pos=water_pos, size=water_block_size),
        material=gs.materials.SPH.Liquid(rho=1000.0),
        surface=gs.surfaces.Default(color=(0.2, 0.5, 0.8, 0.7)),
    )

    # ----------------------------------------------------------------
    # 4. Heavy metallic sphere (rigid)
    # ----------------------------------------------------------------
    sphere_radius = 0.08
    sphere_start_pos = (tank_w/2, tank_d/2, 0.8)   # above water

    sphere = scene.add_entity(
        gs.morphs.Sphere(pos=sphere_start_pos, radius=sphere_radius),
        material=gs.materials.Rigid(rho=5000.0, friction=0.5),   # heavy metal
        surface=gs.surfaces.Rough(color=(0.9, 0.9, 0.9, 1.0), roughness=0.2),
    )

    # ----------------------------------------------------------------
    # Build and simulate
    # ----------------------------------------------------------------
    scene.build()

    # Run simulation for enough steps to see splash and sinking
    for _ in range(2500):
        scene.step()

if __name__ == "__main__":
    main()