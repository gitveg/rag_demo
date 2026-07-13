import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 3, 3),
            camera_lookat=(0, 0, 0.5),
        ),
        show_viewer=True,
    )

    # -------- floor --------
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(0, 0, 0), fixed=True),
        material=gs.materials.Rigid(),
    )

    # -------- box walls (fixed) --------
    wall_thickness = 0.1
    half_size = 1.0
    height = 1.0

    # left, right
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-half_size, 0, height / 2),
            size=(wall_thickness, 2 * half_size, height),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(half_size, 0, height / 2),
            size=(wall_thickness, 2 * half_size, height),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )
    # front, back
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, -half_size, height / 2),
            size=(2 * half_size, wall_thickness, height),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, half_size, height / 2),
            size=(2 * half_size, wall_thickness, height),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # -------- ball --------
    ball_radius = 0.15
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.5, 0.0, ball_radius),  # start off-centre to see circular motion sooner
            radius=ball_radius,
            fixed=False,
        ),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Default(color=(0.8, 0.2, 0.2, 1.0)),
    )

    # -------- rotating force field around vertical axis --------
    force_field = gs.force_fields.VortexForceField(
        axis=[0, 0, 1],
        angular_velocity=5.0,  # rad/s
        center=[0, 0, 0],
    )
    scene.add_force_field(force_field)

    scene.build()

    # simulation loop
    for _ in range(1200):
        scene.step()

if __name__ == "__main__":
    main()