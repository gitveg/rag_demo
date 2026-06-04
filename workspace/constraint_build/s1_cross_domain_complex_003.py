import numpy as np
import genesis as gs

def main():
    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, 0.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=viewer_options,
        rigid_options=gs.options.RigidOptions(),
        fem_options=gs.options.FEMOptions(),
    )

    ########################## add entities ##########################
    # Uneven terrain
    terrain = scene.add_entity(
        morph=gs.morphs.Terrain(
            pos=(0.0, 0.0, -0.1),
        ),
    )

    # Drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            pos=(0.0, 0.0, 0.5),
        ),
    )

    # Humanoid robot (using a URDF – ensure the file is available)
    humanoid = scene.add_entity(
        morph=gs.morphs.URDF(
            file="../../assets/urdf/humanoid.urdf",  # adjust path as needed
            pos=(1.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    # Soft debris (FEM elastic box)
    debris = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(2.0, 0.5, 0.2),
            size=(0.3, 0.3, 0.3),
        ),
        material=gs.materials.FEM.Elastic(
            E=50000.0,
            nu=0.45,
            rho=500.0,
        ),
    )

    # Target object (a small rigid sphere)
    target = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(3.0, 0.0, 0.2),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )

    # Shallow water (SPH emitter)
    water_emitter = scene.add_emitter(
        material=gs.materials.SPH.Liquid(),
        max_particles=20000,
    )

    ########################## build the scene ##########################
    scene.build(n_envs=1)

    ########################## simulation loop ##########################
    for i in range(1000):
        # Drone scanning: slowly move in a circle
        t = i * 0.01
        drone_pos = np.array([2.0 * np.cos(t), 2.0 * np.sin(t), 1.0 + 0.3 * np.sin(2 * t)])
        drone.set_dofs_position(np.array([0.5, 0.2, 0.0, 0.0, -0.2, -0.2, 0.0, 0.0]))

        # Humanoid: simple walking motion (set joint positions)
        # Example: swing legs
        phase = np.sin(i * 0.05)
        humanoid.set_dofs_position(
            np.array([phase * 0.3, -phase * 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        )

        # Water emitter: emit each step (creates a small pool)
        water_emitter.emit(100)

        scene.step()

if __name__ == "__main__":
    main()