import argparse
import genesis as gs

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 3.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## add entities ##########################
    # Ramp: a static box tilted about the x-axis by 20 degrees
    ramp = scene.add_entity(
        morph=gs.morphs.Box(
            size=(2.0, 0.5, 0.2),
            pos=(0.0, 0.0, 0.0),
            euler=(20.0, 0.0, 0.0),
        ),
        material=None,  # static collision shape
    )

    # Sphere (dynamic) that will roll down the ramp
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.2,
            pos=(-0.8, 0.0, 0.5),  # placed near the top of the tilted ramp
        ),
        material=gs.materials.Rigid(rho=200.0, friction=0.5),
    )

    # Three boxes stacked at the bottom of the ramp
    box_size = (0.2, 0.2, 0.2)
    # Bottom box
    box1 = scene.add_entity(
        morph=gs.morphs.Box(
            size=box_size,
            pos=(0.8, 0.0, 0.2),
        ),
        material=gs.materials.Rigid(rho=200.0, friction=0.3),
    )
    # Middle box
    box2 = scene.add_entity(
        morph=gs.morphs.Box(
            size=box_size,
            pos=(0.8, 0.0, 0.5),
        ),
        material=gs.materials.Rigid(rho=200.0, friction=0.3),
    )
    # Top box
    box3 = scene.add_entity(
        morph=gs.morphs.Box(
            size=box_size,
            pos=(0.8, 0.0, 0.8),
        ),
        material=gs.materials.Rigid(rho=200.0, friction=0.3),
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(2000):
        scene.step()

if __name__ == "__main__":
    main()