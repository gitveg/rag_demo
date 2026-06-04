"""
User Query: Load a humanoid robot (use gs.morphs.MJCF(file="xml/humanoid.xml")) in a simple room with boxes. Make it walk toward a shelf by moving its leg joints.
task_id: s1_robot_complex_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

wall_thickness = 0.2
room_size = 8.0
wall_height = 2.0

scene.add_entity(
    gs.morphs.Box(pos=(0.0, -room_size / 2, wall_height / 2), size=(room_size, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Rough(color=(0.9, 0.9, 0.92, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, room_size / 2, wall_height / 2), size=(room_size, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Rough(color=(0.9, 0.9, 0.92, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(-room_size / 2, 0.0, wall_height / 2), size=(wall_thickness, room_size, wall_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Rough(color=(0.9, 0.9, 0.92, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(room_size / 2, 0.0, wall_height / 2), size=(wall_thickness, room_size, wall_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Rough(color=(0.9, 0.9, 0.92, 1.0)),
)

for x in (-1.0, 0.8, 2.2):
    for y in (-1.5, 1.0):
        scene.add_entity(
            gs.morphs.Box(pos=(x, y, 0.25), size=(0.5, 0.5, 0.5)),
            material=gs.materials.Rigid(friction=0.8),
            surface=gs.surfaces.Default(color=(0.65, 0.45, 0.3, 1.0)),
        )

shelf_x = 3.0
shelf_y = 0.0
shelf_depth = 0.6
shelf_width = 1.2
shelf_height = 1.8
board_thickness = 0.08

scene.add_entity(
    gs.morphs.Box(pos=(shelf_x, shelf_y, board_thickness / 2), size=(shelf_width, shelf_depth, board_thickness)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(shelf_x - shelf_width / 2 + 0.06, shelf_y, shelf_height / 2), size=(0.08, shelf_depth, shelf_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(shelf_x + shelf_width / 2 - 0.06, shelf_y, shelf_height / 2), size=(0.08, shelf_depth, shelf_height)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(shelf_x, shelf_y, shelf_height - board_thickness / 2), size=(shelf_width, shelf_depth, board_thickness)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(shelf_x, shelf_y, 0.7), size=(shelf_width, shelf_depth, board_thickness)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(shelf_x, shelf_y, 1.2), size=(shelf_width, shelf_depth, board_thickness)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Default(color=(0.45, 0.3, 0.18, 1.0)),
)

humanoid = scene.add_entity(
    gs.morphs.MJCF(file="xml/humanoid.xml", pos=(-2.5, 0.0, 1.4)),
)

scene.build()

n_dofs = humanoid.n_dofs
q0 = [0.0] * n_dofs

try:
    humanoid.set_dofs_kp([80.0] * n_dofs)
    humanoid.set_dofs_kv([8.0] * n_dofs)
except Exception:
    pass

try:
    humanoid.control_dofs_position(q0)
except Exception:
    pass

left_hip_pitch = 0
left_knee = 1
left_ankle = 2
right_hip_pitch = 3
right_knee = 4
right_ankle = 5

if n_dofs < 6:
    raise RuntimeError(f"Humanoid has only {n_dofs} DOFs; expected at least 6 for simple leg control.")

target_x = shelf_x - 0.9
steps = 1600

for i in range(steps):
    t = i * 0.01
    pos = humanoid.get_pos()
    remaining = target_x - pos[0]

    walk_gain = 1.0 if remaining > 0.2 else max(0.0, remaining / 0.2)
    freq = 2.2
    phase = 2.0 * math.pi * freq * t

    hip_amp = 0.45 * walk_gain
    knee_amp = 0.7 * walk_gain
    ankle_amp = 0.25 * walk_gain

    q = [0.0] * n_dofs

    q[left_hip_pitch] = hip_amp * math.sin(phase)
    q[right_hip_pitch] = hip_amp * math.sin(phase + math.pi)

    q[left_knee] = max(0.0, knee_amp * math.sin(phase))
    q[right_knee] = max(0.0, knee_amp * math.sin(phase + math.pi))

    q[left_ankle] = -ankle_amp * math.sin(phase)
    q[right_ankle] = -ankle_amp * math.sin(phase + math.pi)

    upper_body_lean = -0.12 * walk_gain
    for j in range(6, min(n_dofs, 10)):
        q[j] = upper_body_lean

    try:
        humanoid.control_dofs_position(q)
    except Exception:
        try:
            humanoid.set_dofs_position(q)
        except Exception:
            pass

    scene.step()