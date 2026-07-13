import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 2),
            camera_lookat=(0, 0, 0.8),
            camera_fov=40,
        ),
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        show_viewer=True,
    )

    # ground plane to catch cloth
    scene.add_entity(gs.morphs.Plane())

    # horizontal pole (cylinder along x-axis)
    pole = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0, 0, 0.8),   # height of pole center
            radius=0.05,
            height=1.2,        # length of pole along x-axis
            axis="x",
        ),
    )

    # rectangular cloth placed above the pole
    cloth = scene.add_entity(
        gs.morphs.Plane(
            pos=(0, 0, 1.2),   # initial height above pole
            euler=(0, 0, 0),
            lx=0.6,
            ly=0.6,
            n_segments=(20, 20),
        ),
        material=gs.materials.Cloth(),
        surface=gs.surfaces.Default(),
    )

    scene.build()

    # run simulation with viewer
    gs.tools.run(scene)

if __name__ == "__main__":
    main()