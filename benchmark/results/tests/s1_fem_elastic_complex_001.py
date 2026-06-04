"""
User Query: Build a scene with a soft elastic beam fixed at one end and free at the other. Release it and let it oscillate under gravity while a second soft elastic sphere bounces off the beam's free end.
task_id: s1_fem_elastic_complex_001
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=5e-4,
            substeps=10,
            gravity=(0.0, 0.0, -9.81),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.8, -2.2, 1.6),
            camera_lookat=(0.4, 0.0, 0.45),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.2),
        surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.78, 1.0)),
    )

    beam_material = gs.materials.FEM.Elastic(
        density=900,
        youngs_modulus=8e4,
        poissons_ratio=0.35,
    )

    sphere_material = gs.materials.FEM.Elastic(
        density=1000,
        youngs_modulus=1.2e5,
        poissons_ratio=0.32,
    )

    beam = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.45, 0.0, 0.6),
            size=(0.9, 0.12, 0.12),
        ),
        material=beam_material,
        surface=gs.surfaces.Default(color=(0.35, 0.7, 0.95, 1.0)),
    )

    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(1.15, 0.0, 1.0),
            radius=0.09,
        ),
        material=sphere_material,
        surface=gs.surfaces.Glass(color=(1.0, 0.45, 0.35, 0.5)),
    )

    cam = scene.add_camera(
        res=(1280, 720),
        pos=(2.8, -2.2, 1.6),
        lookat=(0.4, 0.0, 0.45),
        fov=45,
    )

    scene.build()

    if hasattr(beam, "set_fem_dirichlet_boundary"):
        beam.set_fem_dirichlet_boundary(
            axis="x",
            value=0.0,
            side="min",
        )
    elif hasattr(beam, "set_dirichlet_boundary"):
        beam.set_dirichlet_boundary(
            axis="x",
            value=0.0,
            side="min",
        )
    elif hasattr(beam, "fix_vertices_in_box"):
        beam.fix_vertices_in_box(
            lower=(-0.02, -0.08, 0.5),
            upper=(0.08, 0.08, 0.7),
        )
    elif hasattr(beam, "fix_particles_in_box"):
        beam.fix_particles_in_box(
            lower=(-0.02, -0.08, 0.5),
            upper=(0.08, 0.08, 0.7),
        )

    if hasattr(sphere, "set_velocity"):
        sphere.set_velocity((-2.2, 0.0, -0.2))
    elif hasattr(sphere, "set_vel"):
        sphere.set_vel((-2.2, 0.0, -0.2))

    for i in range(2400):
        scene.step()
        if i % 2 == 0 and hasattr(cam, "render"):
            cam.render()


if __name__ == "__main__":
    main()