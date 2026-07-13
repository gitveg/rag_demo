import genesis as gs

gs.init()

scene = gs.Scene()

# Platform (static ground plane)
plane = scene.add_entity(gs.morphs.Plane())

# Rigid body (falling box)
box = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 1.0), size=(0.1, 0.1, 0.1)),
)

# Equip IMU sensor on the box
imu = box.add_imu_sensor()

scene.build()

# Simulation parameters
dt = scene.dt  # Use scene's default timestep
num_steps = 500  # Enough for fall and impact

# Record linear acceleration
lin_acc_log = []

for step in range(num_steps):
    scene.step()
    # IMU provides linear acceleration in world frame
    acc = imu.lin_acc
    lin_acc_log.append(acc)

# Output the recorded data (for demonstration)
print("Time(s) | Linear acceleration (x, y, z) in world frame")
for i, acc in enumerate(lin_acc_log):
    print(f"t={i * dt:.3f} | {acc[0]:.3f} {acc[1]:.3f} {acc[2]:.3f}")