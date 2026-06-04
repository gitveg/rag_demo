import genesis as gs
import numpy as np

def main():
    ########################## init ##########################
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        show_viewer=False,
        vis_options=gs.options.VisOptions(
            plane_reflection=False,
        ),
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
    )

    ########################## entities ##########################
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    cube = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.5, 0.5, 2.0),
            size=(0.2, 0.2, 0.2),
        ),
    )

    ########################## camera (depth sensor) ##########################
    # Attach a depth camera to the cube by initially placing it above the cube
    camera = scene.add_camera(
        model="pinhole",
        res=(640, 480),
        pos=(0.5, 0.5, 2.5),
        lookat=(0.5, 0.5, 0.0),
        fov=60,
        near=0.1,
        far=10.0,
    )

    ########################## build ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(500):
        scene.step()

        # Update camera pose to follow the cube
        cube_pos = cube.get_pos()
        camera.set_pos(cube_pos + (0.0, 0.0, 0.5))  # stay 0.5 m above cube
        camera.set_lookat(cube_pos - (0.0, 0.0, 0.5))  # look downwards

        # Render depth image
        depth = camera.render_depth()

        # Read distance at the centre pixel (assuming image is 640x480)
        cx, cy = 320, 240
        distance = depth[cy, cx]

        print(f"Step {i:3d} – measured distance to ground: {distance:.4f} m")

if __name__ == "__main__":
    main()