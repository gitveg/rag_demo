import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.cpu, precision="32")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, -5.0, 5.0),
            camera_lookat=(0.0, 0.0, 0.5),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Place boxes with alternating light and heavy densities
    num_boxes = 10
    light_rho = 200.0   # kg/m³, lighter
    heavy_rho = 1000.0  # kg/m³, heavier
    box_size = 0.3
    spacing = 0.8

    boxes = []
    for i in range(num_boxes):
        x = (i - (num_boxes - 1) / 2) * spacing
        y = 0.0
        z = box_size / 2 + 0.02  # just above ground
        rho = light_rho if i % 2 == 0 else heavy_rho
        box = scene.add_entity(
            gs.morphs.Box(pos=(x, y, z), size=(box_size, box_size, box_size)),
            material=gs.materials.Rigid(rho=rho),
        )
        boxes.append(box)

    scene.build()

    # Parameters for the pulsing upward force (implemented via velocity modulation)
    omega = 2 * np.pi * 0.5   # 0.5 Hz
    amplitude = 5.0           # m/s² upward acceleration amplitude

    for _ in range(300):
        t = scene.sim.cur_time
        upward_acc = amplitude * np.sin(omega * t)

        for box in boxes:
            vel = box.get_dofs_velocity()
            # Add acceleration * dt to vertical linear velocity (index 2)
            vel[2] += upward_acc * scene.sim.dt
            box.set_dofs_velocity(vel)

        scene.step()

if __name__ == "__main__":
    main()