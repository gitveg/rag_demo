import numpy as np
import genesis as gs

def main():
    gs.init(backend="torch", device="cuda")

    # Create a scene with FEM and rigid solvers enabled
    scene = gs.Scene(
        fem_options=gs.options.FEMOptions(),
        rigid_options=gs.options.RigidOptions(),
        coupler_options=gs.options.IPCCouplerOptions(),
    )

    # Add a soft body sphere (FEM)
    soft_body = scene.add_entity(
        name="soft_sphere",
        material=gs.materials.FEM(),
        morph=gs.morphs.Sphere(radius=0.3, order=1),  # order=1 for linear FEM
    )

    # Add a kinematic rigid body (small box)
    rigid_body = scene.add_entity(
        name="kinematic_box",
        material=gs.materials.Rigid(kinematic=True),
        morph=gs.morphs.Box(half_extents=[0.05, 0.05, 0.05]),
    )

    # Build the scene
    scene.build()

    # Indices of vertices to pin (example: first 10 vertices)
    fixed_vert_indices = list(range(10))

    # Simulation loop
    steps = 500
    for i in range(steps):
        # Animate the rigid body in a circular path
        t = i * 0.01
        new_pos = np.array([0.5 + 0.2 * np.sin(t), 0.5, 0.5 + 0.2 * np.cos(t)])
        scene.entity_states["kinematic_box"].pos = new_pos

        # Pin the selected soft body vertices to the rigid body's position
        scene.entity_states["soft_sphere"].pos[fixed_vert_indices] = new_pos
        # Set their velocity to zero to keep them pinned
        scene.entity_states["soft_sphere"].vel[fixed_vert_indices] = 0.0

        scene.step()

        # Optional: visualize every 10 steps
        if i % 10 == 0:
            scene.draw()

if __name__ == "__main__":
    main()