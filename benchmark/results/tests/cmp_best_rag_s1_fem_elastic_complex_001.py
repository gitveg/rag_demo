import genesis as gs

def main():
    gs.init(backend=gs.gpu, precision="32", logging_level="info")

    # Beam dimensions
    beam_length = 0.3
    beam_width = 0.05
    beam_height = 0.05
    beam_center = (beam_length / 2.0, 0.5, 0.5)

    sphere_radius = 0.05
    sphere_center = (beam_length, 0.5, 0.6)

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        fem_options=gs.options.FEMOptions(
            solver="implicit",
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Soft beam
    beam = scene.add_entity(
        morph=gs.morphs.Box(
            size=(beam_length, beam_width, beam_height),
            pos=beam_center,
        ),
        material=gs.materials.FEM.Elastic(
            E=100000.0,
            nu=0.3,
            rho=1000.0,
        ),
    )

    # Soft sphere
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=sphere_radius,
            pos=sphere_center,
        ),
        material=gs.materials.FEM.Elastic(
            E=100000.0,
            nu=0.3,
            rho=1000.0,
        ),
    )

    scene.build()

    # Fix left end of the beam (vertices with smallest x coordinate)
    vertices = beam.get_vertices()
    x_min = vertices[:, 0].min()
    fix_threshold = x_min + 0.01
    for i, pos in enumerate(vertices):
        if pos[0] <= fix_threshold:
            beam.fix_vertex(i)

    # Simulation loop
    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()