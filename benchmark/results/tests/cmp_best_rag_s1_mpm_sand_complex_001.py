import argparse
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # Initialize genesis
    gs.init(precision="32", logging_level="info")

    # Create scene with MPM options
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.2, -2.0, -1.2),
            upper_bound=(1.2, 2.0, 1.2),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=False,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 0.8, 2.0),
            camera_lookat=(0.0, -0.2, 0.0),
            res=(960, 640),
        ),
        show_viewer=True,
    )

    # Helper to add a static box wall
    def add_wall(pos, size):
        return scene.add_entity(
            morph=gs.options.morphs.Box(pos=pos, size=size),
            material=None,
        )

    # Ground plane (just safety)
    scene.add_entity(
        morph=gs.options.morphs.Plane(pos=(0.0, -1.2, 0.0)),
        material=None,
    )

    # Dimensions: outer width of chambers = 1.0, height of each chamber = ~1.0
    half_extent = 0.5

    # ---------- Upper chamber floor (frame with hole) ----------
    # Floor at y=0.0, hole from -0.1..0.1 in x and z
    hole_half = 0.1
    # Front bar (along x at z = +0.5)
    add_wall((0.0, 0.0, half_extent), (1.0, 0.05, 0.1))
    # Back bar
    add_wall((0.0, 0.0, -half_extent), (1.0, 0.05, 0.1))
    # Left bar (along z at x = -0.5)
    add_wall((-half_extent, 0.0, 0.0), (0.1, 0.05, 1.0))
    # Right bar
    add_wall((half_extent, 0.0, 0.0), (0.1, 0.05, 1.0))

    # ---------- Upper chamber vertical walls ----------
    wall_height = 1.0
    wall_y_center = wall_height / 2.0  # 0.5
    # +x wall
    add_wall((half_extent, wall_y_center, 0.0), (0.1, wall_height, 1.0))
    # -x wall
    add_wall((-half_extent, wall_y_center, 0.0), (0.1, wall_height, 1.0))
    # +z wall
    add_wall((0.0, wall_y_center, half_extent), (1.0, wall_height, 0.1))
    # -z wall
    add_wall((0.0, wall_y_center, -half_extent), (1.0, wall_height, 0.1))

    # ---------- Neck vertical tube (from y=-0.1 to y=0) ----------
    neck_height = 0.1
    neck_y_center = -0.05
    neck_half = 0.1
    thick = 0.02
    # +x side
    add_wall((neck_half, neck_y_center, 0.0), (thick, neck_height, 2*neck_half))
    # -x side
    add_wall((-neck_half, neck_y_center, 0.0), (thick, neck_height, 2*neck_half))
    # +z side
    add_wall((0.0, neck_y_center, neck_half), (2*neck_half, neck_height, thick))
    # -z side
    add_wall((0.0, neck_y_center, -neck_half), (2*neck_half, neck_height, thick))

    # ---------- Lower chamber ----------
    # Floor at y = -1.0
    floor_y = -1.0
    add_wall((0.0, floor_y, 0.0), (1.0, 0.05, 1.0))
    # Lower chamber walls from y=-1.0 to y=-0.1 (height 0.9)
    lower_wall_height = 0.9
    lower_wall_y_center = -0.55
    # +x
    add_wall((half_extent, lower_wall_y_center, 0.0), (0.1, lower_wall_height, 1.0))
    # -x
    add_wall((-half_extent, lower_wall_y_center, 0.0), (0.1, lower_wall_height, 1.0))
    # +z
    add_wall((0.0, lower_wall_y_center, half_extent), (1.0, lower_wall_height, 0.1))
    # -z
    add_wall((0.0, lower_wall_y_center, -half_extent), (1.0, lower_wall_height, 0.1))

    # ---------- Initial sand block in upper chamber ----------
    # Placed inside the upper chamber, above the neck
    sand_size = (0.8, 0.8, 0.8)
    sand_y_center = 0.6  # inside the upper half
    sand = scene.add_entity(
        morph=gs.options.morphs.Box(pos=(0.0, sand_y_center, 0.0), size=sand_size),
        material=gs.materials.MPM.Sand(
            E=1000000.0,
            nu=0.2,
            rho=1200.0,      # sand density
            friction_angle=35,
        ),
    )

    # Build the scene
    scene.build()

    # Simulation loop
    sim_steps = 2000 if args.vis else 500
    for _ in range(sim_steps):
        scene.step()

    if args.vis:
        # Keep viewer open
        print("Simulation complete. Close viewer to exit.")
        scene.viewer.run()


if __name__ == "__main__":
    main()