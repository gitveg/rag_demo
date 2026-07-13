import genesis as gs
import numpy as np

# Initialize Genesis
gs.init(backend=gs.cpu)

# Create scene with viewer
scene = gs.Scene(show_viewer=True)

# Add ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Add buildings (static boxes)
buildings = []
positions = [(5, 0, 0), (-5, 2, 0), (0, -5, 0), (3, 4, 0)]
sizes = [(1, 1, 4), (2, 2, 6), (1.5, 1.5, 5), (1, 2, 3)]
for pos, size in zip(positions, sizes):
    b = scene.add_entity(
        gs.morphs.Box(pos=pos, size=size, fixed=True),
        surface=gs.surfaces.Default(color=(0.4, 0.4, 0.6)),
    )
    buildings.append(b)

# Add drone (as a simplified rigid body box)
drone = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 1), size=(0.4, 0.4, 0.1), fixed=False, mass=1.0),
    surface=gs.surfaces.Default(color=(1.0, 0, 0)),
)

# Add moving barrier (oscillating box)
barrier = scene.add_entity(
    gs.morphs.Box(pos=(2, -2, 1), size=(0.2, 1.5, 1.5), fixed=False, mass=0.1),
    surface=gs.surfaces.Default(color=(0, 1, 0)),
)

# Build the scene
scene.build()

# Control parameters
kp_pos = 5.0
kd_pos = 2.0
mass = drone.mass
gravity = np.array([0.0, 0.0, -9.81])
kp_ang = 0.5  # orientation proportional gain (not used if just damping)
kd_ang = 0.2  # angular velocity damping

# Navigation waypoints (autonomous drone path)
waypoints = [np.array([3, 0, 2]), np.array([-3, 1, 2]), np.array([0, -3, 2]), np.array([2, 3, 2])]
current_target_index = 0
target = waypoints[0]
target_tolerance = 0.3

# Simulation loop
sim_time = 0.0
dt = scene.dt  # time step from scene

while scene.viewer.is_running():
    # ---- Move barrier sinusoidally ----
    barrier_x = 2.0 + 1.5 * np.sin(1.5 * sim_time)
    barrier.set_pos(np.array([barrier_x, -2, 1]))

    # ---- Drone control ----
    pos = drone.get_pos()
    vel = drone.get_vel()
    err = target - pos

    # Force: proportional + derivative + gravity compensation
    force = kp_pos * err - kd_pos * vel + mass * (-gravity)  # gravity comp: opposite of gravity

    # Apply force to drone (at center of mass)
    drone.set_force(force)

    # Angular velocity damping to stabilize orientation
    ang_vel = drone.get_ang_vel()
    torque = -kd_ang * ang_vel
    drone.set_torque(torque)

    # ---- Waypoint switching ----
    if np.linalg.norm(err) < target_tolerance:
        current_target_index = (current_target_index + 1) % len(waypoints)
        target = waypoints[current_target_index]

    # Step physics and render
    scene.step()
    scene.render()
    sim_time += dt

# Cleanup
scene.finalize()