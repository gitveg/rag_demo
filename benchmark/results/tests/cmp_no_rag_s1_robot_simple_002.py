import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    show_viewer=True,
)

# load Franka Panda robot from MJCF file
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# run simulation (end-effector control not implemented due to missing API)
for i in range(2000):
    scene.step()