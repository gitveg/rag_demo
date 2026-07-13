import numpy as np
import genesis as gs


def main():
    # Initialize
    gs.init()

    # Create scene with default rigid options and gravity
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(gravity=(0, 0, -9.81)),
        show_viewer=True,
    )

    # Floor (plane at z=0)
    scene.add_entity(gs.morphs.Plane())

    # Box dimensions: square enclosure of side 2.0 m, walls 0.1 m thick, 1.0 m high
    wall_thickness = 0.1
    wall_height = 1.0
    enclosure_half = 1.0

    # Four walls: +X, -X, +Y, -Y
    scene.add_entity(
        gs.morphs.Box(
            pos=(enclosure_half, 0, wall_height / 2),
            size=(wall_thickness, 2 * enclosure_half, wall_height),
        )
    )
    scene.add_entity(
        gs.morphs.Box(
            pos=(-enclosure_half, 0, wall_height / 2),
            size=(wall_thickness, 2 * enclosure_half, wall_height),
        )
    )
    scene.add_entity(
        gs.morphs.Box(
            pos=(0, enclosure_half, wall_height / 2),
            size=(2 * enclosure_half, wall_thickness, wall_height),
        )
    )
    scene.add_entity(
        gs.morphs.Box(
            pos=(0, -enclosure_half, wall_height / 2),
            size=(2 * enclosure_half, wall_thickness, wall_height),
        )
    )

    # Ball (rigid sphere) placed just above the floor
    ball_radius = 0.2
    ball = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0, 0, ball_radius + 0.01),
            radius=ball_radius,
        )
    )

    scene.build()

    # Rotating force field: tangential force in the horizontal plane
    force_magnitude = 5.0  # N, enough to overcome friction
    for _ in range(1000):
        pos = ball.get_pos()
        radial_xy = np.array([pos[0], pos[1]])
        if np.linalg.norm(radial_xy) > 1e-6:
            perp = np.array([-radial_xy[1], radial_xy[0]])
            perp_norm = perp / np.linalg.norm(perp) * force_magnitude
        else:
            perp_norm = np.array([0.0, 0.0])
        force = np.array([perp_norm[0], perp_norm[1], 0.0])
        ball.set_force(force)
        scene.step()


if __name__ == "__main__":
    main()