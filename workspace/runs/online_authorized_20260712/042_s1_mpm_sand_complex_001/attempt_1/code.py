import genesis as gs


def main():
    gs.init(backend=gs.cpu, precision="32", performance_mode=True)

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.005),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, -2, 2),
            camera_lookat=(0, 0, 0.75),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # ---------- Lower chamber walls ----------
    # Bottom plate
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0, 0.01), size=(1.0, 0.5, 0.02), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Left wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(-0.5, 0, 0.25), size=(0.02, 0.5, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Right wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.5, 0, 0.25), size=(0.02, 0.5, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Back wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, -0.25, 0.25), size=(1.0, 0.02, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Front wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0.25, 0.25), size=(1.0, 0.02, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )

    # ---------- Upper chamber bottom plates (leave gap) ----------
    # Left part of the bottom
    scene.add_entity(
        morph=gs.morphs.Box(pos=(-0.275, 0, 0.5), size=(0.45, 0.5, 0.02), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Right part of the bottom
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.275, 0, 0.5), size=(0.45, 0.5, 0.02), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )

    # ---------- Upper chamber walls ----------
    # Left wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(-0.5, 0, 0.75), size=(0.02, 0.5, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Right wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.5, 0, 0.75), size=(0.02, 0.5, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Back wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, -0.25, 0.75), size=(1.0, 0.02, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )
    # Front wall
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0.25, 0.75), size=(1.0, 0.02, 0.5), fixed=True),
        material=gs.materials.Rigid(rho=1000),
        surface=gs.surfaces.Plastic(color=(0.8, 0.9, 1.0, 0.5)),
    )

    # ---------- Sand (MPM) initially inside the upper chamber ----------
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0, 0.75), size=(0.8, 0.4, 0.4)),
        material=gs.materials.MPM.Sand(),
    )

    scene.build()

    horizon = 500
    for i in range(horizon):
        scene.step()


if __name__ == "__main__":
    main()