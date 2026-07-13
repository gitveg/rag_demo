import genesis as gs

def main():
    gs.init(backend=gs.gpu, precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-2,
            substeps=10,
        ),
        pbd_options=gs.options.PBDOptions(
            particle_size=1e-2,
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, -1.5, 1.0),
            camera_lookat=(0.0, 0.0, 0.3),
        ),
    )

    # rectangular cloth placed above the pole
    cloth = scene.add_entity(
        material=gs.materials.PBD.Cloth(),
        morph=gs.morphs.Plane(
            pos=(0.0, 0.0, 0.4),   # starting above the pole
            euler=(0.0, 0.0, 0.0),
            size=(0.8, 1.0),       # wide enough to drape on both sides
            n_segs=(16, 20),
        ),
        surface=gs.surfaces.Default(
            color=(0.2, 0.4, 0.8, 1.0),
        ),
    )

    # horizontal pole (static rigid body)
    pole = scene.add_entity(
        material=gs.materials.Rigid(
            rho=1e6,                 # practically immovable
            gravity_compensation=1.0, # ignore gravity
        ),
        morph=gs.morphs.Cylinder(
            pos=(0.0, 0.0, 0.3),
            radius=0.05,
            height=1.0,              # length along Y after rotation
            euler=(90.0, 0.0, 0.0),  # rotate to align axis with Y (horizontal)
        ),
        surface=gs.surfaces.Default(
            color=(0.8, 0.4, 0.2, 1.0),
        ),
    )

    scene.build()

    # let the cloth fall and drape
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()