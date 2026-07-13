import genesis as gs
from genesis.options.sensors import RasterizerCameraOptions

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(show_viewer=False)

    # Static sphere
    sphere = scene.add_entity(
        gs.options.morphs.Sphere(pos=(0.0, 0.0, 0.0), radius=0.5)
    )

    # Depth camera as a sensor
    cam = scene.add_sensor(
        RasterizerCameraOptions(
            pos=(1.5, 0.0, 1.5),
            lookat=(0.0, 0.0, 0.0),
            fov=30,
            res=(640, 480),
            near=0.1,
            far=10.0,
        )
    )

    scene.build()

    # A few simulation steps (static, but necessary for rendering)
    for _ in range(5):
        scene.step()

    # Render the depth map of the scene
    scene.render_all_cameras(depth=True)

if __name__ == "__main__":
    main()