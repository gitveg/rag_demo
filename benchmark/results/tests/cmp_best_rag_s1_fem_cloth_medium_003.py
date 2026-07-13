import numpy as np
import genesis as gs

def main():
    # Initialize Genesis
    gs.init()

    # Create scene with PBD cloth solver options
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.005,
            substeps=10,
        ),
        show_viewer=True,
    )

    # Add ground plane
    scene.add_entity(gs.morphs.Plane())

    # Add a horizontal pole (cylinder) – static due to missing material
    pole = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0.0, 0.0, 1.0),   # center of the pole at z=1
            radius=0.05,
            height=1.0,            # length along the cylinder's axis
            euler=(0, 90, 0),      # rotate 90° around Y to make it horizontal along X
        )
    )

    # Create a rectangular cloth mesh in the XY plane (initially flat above the pole)
    cloth_width = 0.3   # along X
    cloth_length = 0.8  # along Y
    res_x = 16
    res_y = 32
    z_init = 1.2        # slightly above the pole

    x = np.linspace(-cloth_width/2, cloth_width/2, res_x)
    y = np.linspace(-cloth_length/2, cloth_length/2, res_y)
    xx, yy = np.meshgrid(x, y)
    z = np.full_like(xx, z_init)

    # vertices: shape (N, 3)
    vertices = np.stack([xx.ravel(), yy.ravel(), z.ravel()], axis=-1)

    # faces: triangulate a grid of quads
    idx = np.arange(res_x * res_y).reshape(res_y, res_x)
    faces = []
    for i in range(res_y - 1):
        for j in range(res_x - 1):
            # two triangles per quad
            faces.append([idx[i, j], idx[i+1, j], idx[i, j+1]])
            faces.append([idx[i+1, j], idx[i+1, j+1], idx[i, j+1]])
    faces = np.array(faces, dtype=np.int32)

    # Add cloth entity with PBD Cloth material
    cloth = scene.add_entity(
        gs.morphs.Mesh(
            vertices=vertices,
            faces=faces,
        ),
        material=gs.materials.PBD.Cloth(),
        surface=gs.surfaces.Default(),
    )

    # Build the scene
    scene.build()

    # Run simulation steps to let the cloth drape naturally
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()