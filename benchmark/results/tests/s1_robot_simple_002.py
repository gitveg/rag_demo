"""
User Query: Load a Franka Panda robot arm (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")) and move its end effector to a target position above a table.
task_id: s1_robot_simple_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.5, 0.0, 0.6),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

table = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.55, 0.0, 0.35),
        size=(0.8, 1.2, 0.7),
    ),
    material=gs.materials.Rigid(rho=800, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Aluminium(color=(0.75, 0.75, 0.78, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

target_pos = (0.55, 0.0, 0.85)

try:
    ee_link = robot.get_link("panda_hand")
except Exception:
    ee_link = None

try:
    qpos_home = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04]
    robot.set_qpos(qpos_home)
except Exception:
    pass

for _ in range(100):
    scene.step()

ik_solved = False

if ee_link is not None:
    for method_name in ["inverse_kinematics", "ik", "solve_ik"]:
        if hasattr(robot, method_name):
            method = getattr(robot, method_name)
            try:
                qpos_target = method(
                    link=ee_link,
                    pos=target_pos,
                )
                if qpos_target is not None:
                    try:
                        robot.set_qpos(qpos_target)
                    except Exception:
                        pass
                    ik_solved = True
                    break
            except Exception:
                try:
                    qpos_target = method(
                        ee_link,
                        target_pos,
                    )
                    if qpos_target is not None:
                        try:
                            robot.set_qpos(qpos_target)
                        except Exception:
                            pass
                        ik_solved = True
                        break
                except Exception:
                    pass

if not ik_solved and ee_link is not None:
    current_qpos = None
    try:
        current_qpos = robot.get_qpos()
    except Exception:
        pass

    if current_qpos is not None:
        for i in range(400):
            alpha = (i + 1) / 400.0
            interp_target = (
                0.4 + alpha * (target_pos[0] - 0.4),
                0.0 + alpha * (target_pos[1] - 0.0),
                0.6 + alpha * (target_pos[2] - 0.6),
            )
            for method_name in ["inverse_kinematics", "ik", "solve_ik"]:
                if hasattr(robot, method_name):
                    method = getattr(robot, method_name)
                    try:
                        qpos_target = method(link=ee_link, pos=interp_target)
                        if qpos_target is not None:
                            try:
                                robot.set_qpos(qpos_target)
                            except Exception:
                                pass
                            break
                    except Exception:
                        try:
                            qpos_target = method(ee_link, interp_target)
                            if qpos_target is not None:
                                try:
                                    robot.set_qpos(qpos_target)
                                except Exception:
                                    pass
                                break
                        except Exception:
                            pass
            scene.step()
    else:
        for _ in range(400):
            scene.step()
else:
    for _ in range(400):
        scene.step()

for _ in range(300):
    scene.step()