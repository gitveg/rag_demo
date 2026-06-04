import genesis as gs

def main():
    gs.init(backend=gs.gpu, precision="32", seed=0)

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(),
        mpm_options=gs.options.MPMOptions(),
        show_viewer=True,
    )

    # ground
    scene.add_entity(
        morph=gs.morphs.Box(size=(20.0, 20.0, 1.0), pos=(0.0, 0.0, -0.5)),
        material=gs.materials.Rigid(rho=200.0, friction=0.5),
    )

    # table
    scene.add_entity(
        morph=gs.morphs.Box(size=(2.0, 1.0, 0.2), pos=(0.0, 0.0, 0.9)),
        material=gs.materials.Rigid(rho=200.0, friction=0.5),
    )

    # box to be pushed (placed at the far edge of the table so it falls)
    box = scene.add_entity(
        morph=gs.morphs.Box(size=(0.3, 0.3, 0.3), pos=(0.8, 0.0, 1.1)),
        material=gs.materials.Rigid(rho=500.0, friction=0.3),
    )

    # water container (rigid walls – static box with a hollow interior? We'll simply use a box as the pool floor)
    # To keep water contained, we create a static box as the pool bed
    pool_bed = scene.add_entity(
        morph=gs.morphs.Box(size=(4.0, 4.0, 0.25), pos=(0.0, 0.0, -0.125)),
        material=gs.materials.Rigid(rho=200.0, friction=0.5),
    )

    # MPM liquid pool (cube of water)
    scene.add_entity(
        morph=gs.morphs.Box(size=(3.0, 3.0, 0.5), pos=(0.0, 0.0, 0.5)),
        material=gs.materials.MPM.Liquid(rho=1000.0),
    )

    scene.build()

    # simulation loop
    for i in range(1000):
        scene.step()

if __name__ == "__main__":
    main()