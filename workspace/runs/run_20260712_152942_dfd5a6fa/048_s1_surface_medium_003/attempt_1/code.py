import genesis as gs

def main():
    gs.init(backend=gs.cpu, logging_level="warning")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0, 0, -9.81),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 2),
            camera_lookat=(0.5, 0, 0.2),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Cube: shiny metallic silver
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(rho=500),
        surface=gs.surfaces.Metallic(
            color=(0.9, 0.9, 0.9, 1.0),
            roughness=0.1,
        ),
    )

    # Cylinder: matte blue plastic
    scene.add_entity(
        morph=gs.morphs.Cylinder(
            pos=(0.5, 0.0, 0.5),
            radius=0.1,
            height=0.2,
        ),
        material=gs.materials.Rigid(rho=300),
        surface=gs.surfaces.Plastic(
            color=(0.0, 0.0, 0.8, 1.0),
            roughness=0.8,
        ),
    )

    scene.build()

    # run a few steps to let objects settle, then keep viewer open
    for _ in range(200):
        scene.step()

    # keep viewer alive until closed
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()