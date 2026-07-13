import numpy as np
import genesis as gs

# Initialize Genesis
gs.init(backend=gs.cpu)

# Create scene with viewer
scene = gs.Scene(show_viewer=True)

# Add ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Add Crazyflie 2.X drone
drone = scene.add_entity(
    gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X"),
)

# Build the scene
scene.build()

# Parameters
base_rpm = 14468.429183500699  # hover RPM from reference examples
Kp = 20000.0                  # proportional gain for altitude control
dt = 0.01                     # simulation timestep (default)

# State machine
state = "takeoff"             # takeoff, hover, landing, done
hover_start_step = 0
hover_steps = int(3.0 / dt)   # 300 steps for 3 seconds
step = 0

while True:
    # Current height
    pos = drone.get_pos()
    current_height = pos[2]  # z-coordinate

    # State transitions
    if state == "takeoff":
        target_height = 2.0
        if abs(current_height - 2.0) < 0.05:   # within 5cm of target
            state = "hover"
            hover_start_step = step
    elif state == "hover":
        target_height = 2.0
        if (step - hover_start_step) >= hover_steps:
            state = "landing"
    elif state == "landing":
        target_height = 0.0
        if current_height < 0.02:               # near ground
            drone.set_propellels_rpm([0, 0, 0, 0])
            break

    # Simple proportional altitude control
    error = target_height - current_height
    rpm = base_rpm + Kp * error
    rpm = max(0, min(rpm, 30000))               # clamp RPM to safe range

    # Apply same RPM to all four propellers
    drone.set_propellels_rpm([rpm] * 4)

    # Step the simulation
    scene.step()
    step += 1