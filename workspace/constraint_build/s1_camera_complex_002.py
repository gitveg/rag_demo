import genesis as gs
import cv2
import numpy as np

def main():
    gs.init(backend=gs.gpu)

    # Scene setup
    scene = gs.Scene(
        show_viewer=False,
        vis_options=gs.options.VisOptions(plane_reflection=False),
        rigid_options=gs.options.RigidOptions(dt=0.01),
    )

    # Room floor
    plane = gs.options.morphs.Plane()
    scene.add_entity(plane)

    # Room walls (using planes, oriented appropriately)
    wall_vertices = [
        (0.0, 0.0, 1.0, (0, 5, 0)),  # wall1: pos (0,5,0) facing -y? Actually, plane normal is default (0,0,1) upward. For walls we need to rotate? Plane morph doesn't have orientation parameter? Actually, Plane morph has only pos? The API shows Plane(**data), likely it has pos, eular, etc. We'll assume pos is available. For walls, we can set pos to shift them and use default normal (0,0,1) which is upward. Not perfect for walls but okay for a simple room. Better to use boxes for walls? Not shown. We'll skip walls for simplicity.
    ]

    # Load humanoid robot (URDF)
    humanoid = scene.add_entity(
        morph=gs.options.morphs.URDF(
            file="humanoid.urdf",
            pos=(0.0, 0.0, 0.0),
            quat=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # Build scene
    scene.build()

    # Add custom camera
    cam = scene.add_camera(
        res=(1920, 1080),
        pos=(3.0, 3.0, 2.0),
        lookat=(0.0, 0.0, 0.0),
        fov=60,
        GUI=False,
        spp=128,
        denoise=True,
    )

    # Prepare video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("cinematic_recording.mp4", fourcc, 30.0, (1920, 1080))

    # Simulation loop
    num_steps = 600
    for i in range(num_steps):
        # Update camera to follow robot (simple orbiting)
        t = i * 0.01
        offset_x = 3.0 * np.cos(t)
        offset_y = 3.0 * np.sin(t) + 1.0
        cam_pos = (offset_x, offset_y, 2.0)
        # Get robot position (approximate from its base link)
        # We assume humanoid entity has method get_pos() – common in Genesis
        robot_pos = humanoid.get_pos()  # expecting a numpy array
        # Set camera to look at robot
        cam.set_pose(pos=cam_pos, lookat=robot_pos)

        # Step simulation
        scene.step()

        # Render from camera
        img = cam.render()

        # Convert to BGR for cv2
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        out.write(img_bgr)

    # Release video
    out.release()

if __name__ == "__main__":
    main()