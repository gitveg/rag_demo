import argparse
import sys
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
        ),
        show_viewer=args.vis,
    )

    # Ground plane
    plane = gs.morphs.Plane()
    scene.add_entity(plane)

    # Soft elastic cube (FEM)
    cube_morph = gs.morphs.Mesh(
        file="cube.obj",
        pos=(0.0, 0.5, 0.0),  # sit on the plane
        scale=0.5,
        euler=(0.0, 0.0, 0.0),
    )
    soft_mat = gs.materials.FEM.Elastic(
        E=50000.0,  # softer for visible deformation
        nu=0.45,
        rho=1000.0,
        hydroelastic_modulus=100000.0,
        friction_mu=0.5,
        model="linear",
    )
    cube = scene.add_entity(cube_morph, material=soft_mat)

    # Rigid sphere
    sphere_morph = gs.morphs.Sphere(
        radius=0.3,
        pos=(0.0, 2.0, 0.0),  # above the cube
    )
    sphere = scene.add_entity(sphere_morph, material=gs.materials.Rigid())

    scene.build()

    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()