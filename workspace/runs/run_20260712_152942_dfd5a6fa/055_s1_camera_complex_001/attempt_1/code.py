import genesis as gs
import torch

def run_simulation(view_name, camera_pos, camera_lookat, seed=42):
    # Use same seed for reproducibility
    torch.manual_seed(seed)
    gs.init(seed=seed, precision="32", logging_level="info")

    # Build scene with a rigid solver
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(gravity=(0, 0, -9.81)),
        viewer_options=gs.options.ViewerOptions(
            res=(640, 480),
            camera_pos=camera_pos,
            camera_lookat=camera_lookat,
            camera_fov=40,
        ),
        show_viewer=False,
    )

    # Static slope (a long thin box rotated to form a ramp)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.0),
            size=(5.0, 1.0, 0.2),
            euler=(0, 30, 0),   # 30 deg around y -> sloping down in +x
            fixed=True,
        ),
        material=gs.materials.Rigid(rho=500, friction=0.5),
        surface=gs.surfaces.Plastic(color=(0.8, 0.3, 0.2, 1.0)),
    )

    # Tumbling box placed at the top of the ramp
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(2.5, 0.0, 1.5),   # above the ramp surface
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(rho=300, friction=0.3),
        surface=gs.surfaces.Default(color=(0.5, 1.0, 0.5)),
    )

    scene.build()

    # Start recording the viewer's output
    scene.start_recording()

    # Run the simulation for a few seconds
    for _ in range(500):
        scene.step()

    # Save the recorded video
    scene.viewer.save_video(f"{view_name}.mp4")

# First pass: side view
run_simulation(
    view_name="side_view",
    camera_pos=(0.0, 3.0, 2.0),
    camera_lookat=(2.0, 0.0, 0.5),
)

# Second pass: top view
run_simulation(
    view_name="top_view",
    camera_pos=(2.0, 2.0, 5.0),
    camera_lookat=(2.0, 0.0, 0.5),
)