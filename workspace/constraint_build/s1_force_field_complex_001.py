import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
    )

    # Floor (static)
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=1e9, gravity_compensation=1),
    )

    # Box walls (thin rectangles)
    wall_thickness = 0.1
    wall_height = 1.0
    box_half = 1.5

    for y_pos in [-box_half, box_half]:
        scene.add_entity(
            morph=gs.morphs.Box(
                size=(2*box_half, wall_thickness, wall_height),
                pos=(0, y_pos, wall_height/2),
            ),
            material=gs.materials.Rigid(rho=1e9, gravity_compensation=1),
        )
    for x_pos in [-box_half, box_half]:
        scene.add_entity(
            morph=gs.morphs.Box(
                size=(wall_thickness, 2*box_half, wall_height),
                pos=(x_pos, 0, wall_height/2),
            ),
            material=gs.materials.Rigid(rho=1e9, gravity_compensation=1),
        )

    # Ball
    ball = scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.2, pos=(0, 0, 0.2)),
        material=gs.materials.Rigid(rho=200.0, friction=0.1),
    )

    scene.build()

    force_strength = 15.0  # adjust magnitude as needed

    while True:
        # Get ball position (assumed API)
        pos = ball.get_pos()
        x, y = pos[0], pos[1]

        # Tangential force around vertical axis
        r = np.hypot(x, y)
        if r > 1e-6:
            fx = -y / r * force_strength
            fy =  x / r * force_strength
        else:
            fx, fy = 0.0, 0.0
        force = np.array([fx, fy, 0.0])
        ball.set_force(force)
        ball.set_torque(np.zeros(3))

        scene.step()

if __name__ == "__main__":
    main()