import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        show_viewer=False,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
    )

    # Add a static sphere
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.0),
            radius=0.5,
        ),
        material=gs.materials.Rigid(rho=1000.0),
    )

    # Add a depth camera looking at the sphere
    cam = scene.add_camera(
        res=(640, 480),
        pos=(1.5, 0.0, 0.5),
        lookat=(0.0, 0.0, 0.0),
        fov=30,
        GUI=False,
    )

    scene.build()

    # Step a few times to ensure scene is up-to-date
    for _ in range(10):
        scene.step()

    # Render depth
    results = scene.render_all_cameras(depth=True)
    depth_image = results[0]['depth']
    print("Depth image shape:", depth_image.shape)
    print("Depth values (min/max):", depth_image.min(), depth_image.max())

    # Optional: save depth image as numpy file
    np.save("depth.npy", depth_image)

if __name__ == "__main__":
    main()