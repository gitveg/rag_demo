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
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.6, -0.6, -0.7),
            upper_bound=(0.6, 0.6, 0.9),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, -1.5, 0.8),
            camera_lookat=(0.0, 0.0, 0.1),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## glass material ##########################
    glass_surface = gs.surfaces.Plastic(color=(0.4, 0.6, 0.9, 0.4))

    def add_wall(pos, size, scene, rot=None):
        morph = gs.morphs.Box(pos=pos, size=size, fixed=True)
        if rot is not None:
            morph.euler = rot
        scene.add_entity(
            material=gs.materials.Rigid(),
            morph=morph,
            surface=glass_surface,
        )

    ########################## upper chamber walls ##########################
    # inner space: 0.3 x 0.3, z from 0.2 to 0.7
    hw = 0.15       # half-width of inner chamber
    wt = 0.02       # wall thickness
    ch = 0.5        # chamber height
    cz = 0.45       # chamber center z

    add_wall(pos=(0.0, hw, cz), size=(0.3 + 2*wt, wt, ch), scene=scene)        # front
    add_wall(pos=(0.0, -hw, cz), size=(0.3 + 2*wt, wt, ch), scene=scene)       # back
    add_wall(pos=(-hw, 0.0, cz), size=(wt, 0.3, ch), scene=scene)              # left
    add_wall(pos=(hw, 0.0, cz), size=(wt, 0.3, ch), scene=scene)               # right

    ########################## lower chamber walls ##########################
    # inner space: 0.3 x 0.3, z from -0.5 to 0.0
    lcz = -0.25     # lower chamber center z
    lch = 0.5

    add_wall(pos=(0.0, hw, lcz), size=(0.3 + 2*wt, wt, lch), scene=scene)      # front
    add_wall(pos=(0.0, -hw, lcz), size=(0.3 + 2*wt, wt, lch), scene=scene)     # back
    add_wall(pos=(-hw, 0.0, lcz), size=(wt, 0.3, lch), scene=scene)            # left
    add_wall(pos=(hw, 0.0, lcz), size=(wt, 0.3, lch), scene=scene)             # right

    ########################## neck walls ##########################
    # inner space: 0.05 x 0.05, z from 0.0 to 0.1
    nhw = 0.025     # neck half-width
    ncz = 0.05      # neck center z
    nh = 0.1        # neck height

    add_wall(pos=(0.0, nhw, ncz), size=(0.05 + 2*wt, wt, nh), scene=scene)     # front
    add_wall(pos=(0.0, -nhw, ncz), size=(0.05 + 2*wt, wt, nh), scene=scene)    # back
    add_wall(pos=(-nhw, 0.0, ncz), size=(wt, 0.05, nh), scene=scene)           # left
    add_wall(pos=(nhw, 0.0, ncz), size=(wt, 0.05, nh), scene=scene)            # right

    ########################## upper funnel walls ##########################
    # slopes from half-width 0.15 at z=0.2 to half-width 0.025 at z=0.1
    slope_len = ((hw - nhw)**2 + 0.1**2)**0.5
    slope_angle = 180.0 * 3.14159**-1 * (3.14159 * 0.5 - (hw - nhw) / 0.1 * 0)  # placeholder, compute properly
    import math
    slope_angle_deg = math.degrees(math.atan2(hw - nhw, 0.1))
    # slope_angle_deg ≈ atan(0.125/0.1) = 51.34 degrees from vertical
    fy = (hw + nhw) / 2.0
    fz = 0.15

    add_wall(pos=(0.0, fy, fz), size=(0.3 + 2*wt, wt, slope_len),
             scene=scene, rot=(slope_angle_deg, 0.0, 0.0))                       # front
    add_wall(pos=(0.0, -fy, fz), size=(0.3 + 2*wt, wt, slope_len),
             scene=scene, rot=(-slope_angle_deg, 0.0, 0.0))                      # back
    add_wall(pos=(-fy, 0.0, fz), size=(wt, 0.3, slope_len),
             scene=scene, rot=(0.0, -slope_angle_deg, 0.0))                      # left
    add_wall(pos=(fy, 0.0, fz), size=(wt, 0.3, slope_len),
             scene=scene, rot=(0.0, slope_angle_deg, 0.0))                       # right

    ########################## lower funnel walls ##########################
    # slopes from half-width 0.025 at z=0.0 to half-width 0.15 at z=-0.1
    lfy = (hw + nhw) / 2.0
    lfz = -0.05

    add_wall(pos=(0.0, -lfy, lfz), size=(0.3 + 2*wt, wt, slope_len),
             scene=scene, rot=(slope_angle_deg, 0.0, 0.0))                       # front
    add_wall(pos=(0.0, lfy, lfz), size=(0.3 + 2*wt, wt, slope_len),
             scene=scene, rot=(-slope_angle_deg, 0.0, 0.0))                      # back
    add_wall(pos=(lfy, 0.0, lfz), size=(wt, 0.3, slope_len),
             scene=scene, rot=(0.0, -slope_angle_deg, 0.0))                      # left
    add_wall(pos=(-lfy, 0.0, lfz), size=(wt, 0.3, slope_len),
             scene=scene, rot=(0.0, slope_angle_deg, 0.0))                       # right

    ########################## base and top covers ##########################
    add_wall(pos=(0.0, 0.0, -0.51), size=(0.34, 0.34, wt), scene=scene)          # base
    add_wall(pos=(0.0, 0.0, 0.71), size=(0.34, 0.34, wt), scene=scene)           # top cover

    ########################## sand in upper chamber ##########################
    sand = scene.add_entity(
        material=gs.materials.MPM.Sand(rho=1600.0, friction_angle=35),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.48),
            size=(0.26, 0.26, 0.44),
        ),
        surface=gs.surfaces.Default(color=(0.85, 0.75, 0.5)),
    )

    ########################## build and simulate ##########################
    scene.build()

    sim_duration = 5.0
    dt = 0.005
    steps = int(sim_duration / dt)

    for _ in range(steps):
        scene.step()


if __name__ == "__main__":
    main()