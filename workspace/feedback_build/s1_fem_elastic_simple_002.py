import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=2,
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
    )

    # Ground plane (rigid by default)
    scene.add_entity(gs.morphs.Plane())

    # Soft elastic cube falling from air
    scene.add_entity(
        gs.morphs.Box(
            size=(0.2, 0.2, 0.2),
            pos=(0, 0, 1.0),
        ),
        material=gs.materials.FEM.Elastic(),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()