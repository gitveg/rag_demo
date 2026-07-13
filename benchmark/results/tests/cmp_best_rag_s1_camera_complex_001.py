import numpy as np
import genesis as gs
from genesis.utils.misc import tensor_to_array

try:
    import imageio
except ImportError:
    imageio = None
    print("imageio not installed; saving frames as individual images instead.")

def main():
    # Initialize genesis
    gs.init(backend=gs.gpu, precision="32")

    # Scene setup
    scene = gs.Scene(
        show_viewer=False,
        vis_options=gs.options.VisOptions(
            rendered_envs_idx=(0,),
        ),
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
    )

    # Tilted plane as a slope (rotate around y-axis by 20 degrees)
    slope_angle = np.radians(20)
    plane = scene.add_entity(
        gs.morphs.Plane(
            pos=(0, 0, 0),
            euler=(0, slope_angle, 0),
        ),
    )

    # Rigid box
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 1.0),     # slightly above slope at origin
            size=(0.3, 0.3, 0.3),
            euler=(0.1, 0.0, 0.0),   # small initial tilt to encourage tumbling
        ),
        material=gs.materials.Rigid(rho=200, friction=0.8),
    )

    # Two cameras: side view and top view
    cam_side = scene.add_camera(
        res=(320, 320),
        pos=(0, 2, 1),
        lookat=(0, 0, 1),
        fov=30,
        up=(0, 0, 1),
    )
    cam_top = scene.add_camera(
        res=(320, 320),
        pos=(0, 0, 3),
        lookat=(0, 0, 1),
        fov=30,
        up=(0, 1, 0),               # up is y-axis for top-down view
    )

    scene.build()

    frames_side = []
    frames_top = []
    num_steps = 300

    for step in range(num_steps):
        scene.step()

        # Get box position to track cameras
        pos = box.get_pos()

        # Side camera: offset along y-axis
        cam_side.set_pose(
            pos=(pos[0], pos[1] + 2.0, pos[2]),
            lookat=(pos[0], pos[1], pos[2]),
        )
        # Top camera: offset above box along z-axis
        cam_top.set_pose(
            pos=(pos[0], pos[1], pos[2] + 2.0),
            lookat=(pos[0], pos[1], pos[2]),
        )

        # Render both views
        cam_side.render(rgb=True)
        cam_top.render(rgb=True)

        # Convert from tensor to numpy arrays
        rgb_side = tensor_to_array(cam_side.rgb)
        rgb_top = tensor_to_array(cam_top.rgb)

        frames_side.append(rgb_side)
        frames_top.append(rgb_top)

    # Save videos or image sequences
    if imageio is not None:
        imageio.mimsave("side_view.mp4", frames_side, fps=30)
        imageio.mimsave("top_view.mp4", frames_top, fps=30)
        print("Videos saved: side_view.mp4, top_view.mp4")
    else:
        for i, (fs, ft) in enumerate(zip(frames_side, frames_top)):
            imageio.imsave(f"frames/side_{i:04d}.png", fs)
            imageio.imsave(f"frames/top_{i:04d}.png", ft)
        print("Frames saved in 'frames/' directory. Run ffmpeg to create videos manually.")

if __name__ == "__main__":
    main()