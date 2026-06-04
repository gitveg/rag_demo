import genesis as gs

def main():
    gs.init(seed=0, precision="32", logging_level="warning")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1e-2, substeps=10),
        rigid_options=gs.options.RigidOptions(),
        mpm_options=gs.options.MPMOptions(),
        show_viewer=True,
    )

    # Load articulated gripper
    gripper = scene.add_entity(
        morph=gs.morphs.URDF(file="../../examples/URDF/gripper/gripper.urdf"),
        material=gs.materials.Rigid(),
    )

    # Add soft MPM elastic sphere (approximated as a cube)
    sphere = scene.add_entity(
        morph=gs.morphs.Box(
            size=(0.1, 0.1, 0.1),
            pos=(0.0, 0.0, 0.15),  # between fingers
        ),
        material=gs.materials.MPM.Elastic(),
    )

    scene.build()

    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()