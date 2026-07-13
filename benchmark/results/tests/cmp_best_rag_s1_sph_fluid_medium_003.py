import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
        ),
        pbd_options=gs.options.PBDOptions(
            lower_bound=(0.0, 0.0, 0.0),
            upper_bound=(1.0, 1.0, 1.0),
        ),
        show_viewer=True,
    )

    # transparent cubical tank (static rigid box)
    tank = scene.add_entity(
        morph=gs.morphs.Box(pos=(0.5, 0.5, 0.5), size=(1.0, 1.0, 1.0)),
        material=gs.materials.Rigid(fixed=True),
        surface=gs.options.surfaces.Smooth(color=(0.8, 0.9, 0.8, 0.3)),
    )

    # liquid initially filling the lower half of the tank
    liquid = scene.add_entity(
        morph=gs.morphs.Box(pos=(0.5, 0.5, 0.25), size=(1.0, 1.0, 0.5)),
        material=gs.materials.PBD.Liquid(),
    )

    scene.build()

    # Run simulation to let fluid settle under gravity
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()