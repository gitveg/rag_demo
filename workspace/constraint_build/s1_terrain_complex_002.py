import genesis as gs
import numpy as np


def main():
    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, 5, 5),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=True,
    )

    ########################## terrain ##########################
    # Generate a random mountainous terrain using subterrains
    nx, ny = 8, 8
    subterrains = []
    for i in range(nx):
        for j in range(ny):
            height = np.random.uniform(0.0, 1.5)  # mixed flat and hilly
            subterrains.append(
                {
                    "height": height,
                    "x_segment": (i / nx, (i + 1) / nx),
                    "y_segment": (j / ny, (j + 1) / ny),
                }
            )
    scene.add_entity(
        morph=gs.options.morphs.Terrain(
            subterrains=subterrains,
            size=(20, 20),
        ),
    )

    ########################## scattered rocks ##########################
    rock_material = gs.materials.Rigid(rho=500.0)
    for _ in range(30):
        x = np.random.uniform(-9, 9)
        y = np.random.uniform(-9, 9)
        radius = np.random.uniform(0.15, 0.4)
        pos = (x, y, radius)  # place on terrain surface (approximate)
        scene.add_entity(
            morph=gs.options.morphs.Sphere(
                pos=pos,
                radius=radius,
            ),
            material=rock_material,
        )

    ########################## off‑road vehicle ##########################
    # Assume a simple car URDF exists in the default assets
    car_morph = gs.options.morphs.URDF(
        file="genesis/assets/urdf/car.urdf",
        pos=(0.0, 0.0, 0.5),
        scale=1.0,
    )
    car = scene.add_entity(
        morph=car_morph,
        material=gs.materials.Rigid(rho=200.0, friction=0.8),
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(1000):
        # Simple throttle: apply force on the car to drive it forward
        # This simulates driving by applying a force along the car's forward direction
        # (approximate: apply at the center of mass)
        if i < 500:
            car.apply_force(
                force=(1000.0, 0.0, 0.0),  # forward in world x direction
                pos=car.get_link_pose(name="body")[:3],  # apply at body center
            )
        scene.step()

    print("Simulation finished.")


if __name__ == "__main__":
    main()