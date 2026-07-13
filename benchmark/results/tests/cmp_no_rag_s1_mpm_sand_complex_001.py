import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        gravity=(0, 0, -9.81),
    ),
    vis_options=gs.options.VisOptions(
        camera_pos=(1.2, 1.0, 1.0),
        camera_lookat=(0, 0, 0.3),
    ),
)

# Ground plane
plane = scene.add_entity(
    gs.morphs.Plane(pos=(0, 0, 0)),
    material=gs.materials.Rigid(),
)

# Define glass material and surface for walls (static, transparent)
glass_mat = gs.materials.Rigid()
glass_surf = gs.surfaces.Glass(color=(0.7, 0.85, 1.0, 0.3))

# -------------------------------------------------------------------
# Lower bulb (container without top)
L_zbot = 0.01   # bottom plane thickness
L_h = 0.35      # height of side walls
L_half = 0.25   # half width of bulb (square)

# bottom plate
scene.add_entity(
    gs.morphs.Box(pos=(0, 0, L_zbot/2), size=(2*L_half, 2*L_half, L_zbot)),
    material=glass_mat,
    surface=glass_surf,
)
# four side walls (they sit on bottom plate)
for x_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(pos=(x_sign * L_half, 0, L_zbot + L_h/2),
                      size=(0.02, 2*L_half + 0.04, L_h)),
        material=glass_mat,
        surface=glass_surf,
    )
for y_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(pos=(0, y_sign * L_half, L_zbot + L_h/2),
                      size=(2*L_half + 0.04, 0.02, L_h)),
        material=glass_mat,
        surface=glass_surf,
    )

# -------------------------------------------------------------------
# Upper bulb (container with bottom frame and a square hole)
U_h = 0.25              # height of upper bulb
U_half = 0.2            # half width
U_zbase = L_zbot + L_h + 0.05   # base z of upper bulb (gap between bulbs)
tube_hole = 0.05        # square hole half-size

# four side walls of upper bulb
for x_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(pos=(x_sign * U_half, 0, U_zbase + U_h/2),
                      size=(0.02, 2*U_half + 0.04, U_h)),
        material=glass_mat,
        surface=glass_surf,
    )
for y_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(pos=(0, y_sign * U_half, U_zbase + U_h/2),
                      size=(2*U_half + 0.04, 0.02, U_h)),
        material=glass_mat,
        surface=glass_surf,
    )

# Bottom frame of upper bulb – four beams forming a square ring around the hole
frame_thickness = 0.02
hole_half = tube_hole
# Front and back beams
for y_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(
            pos=(0, y_sign * (U_half - frame_thickness/2), U_zbase - frame_thickness/2),
            size=(2*U_half, frame_thickness, frame_thickness),
        ),
        material=glass_mat,
        surface=glass_surf,
    )
# Left and right beams (spanning the gap between front/back beams, excluding the hole)
for x_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(
            pos=(x_sign * (hole_half + (U_half - hole_half)/2),
                 0,
                 U_zbase - frame_thickness/2),
            size=(U_half - hole_half, 2*U_half - 2*frame_thickness, frame_thickness),
        ),
        material=glass_mat,
        surface=glass_surf,
    )

# -------------------------------------------------------------------
# Narrow tube connecting the upper bulb hole to the lower bulb interior
tube_height = 0.12
tube_inner = 2 * tube_hole  # 0.10
tube_wall = 0.015
tube_z_bottom = U_zbase - tube_height   # bottom of tube enters lower bulb

# Four walls of tube (square tube)
for x_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(
            pos=(x_sign * (tube_inner/2 + tube_wall/2), 0, tube_z_bottom + tube_height/2),
            size=(tube_wall, tube_inner, tube_height),
        ),
        material=glass_mat,
        surface=glass_surf,
    )
for y_sign in [-1, 1]:
    scene.add_entity(
        gs.morphs.Box(
            pos=(0, y_sign * (tube_inner/2 + tube_wall/2), tube_z_bottom + tube_height/2),
            size=(tube_inner, tube_wall, tube_height),
        ),
        material=glass_mat,
        surface=glass_surf,
    )

# -------------------------------------------------------------------
# Sand particles – fill top portion of upper bulb
sand_entity = scene.add_entity(
    material=gs.materials.PBD.Granular(radius=0.015, density=1600, friction=0.6),
    morph=gs.morphs.Box(
        pos=(0, 0, U_zbase + U_h * 0.6),
        size=(2*U_half - 0.05, 2*U_half - 0.05, U_h * 0.4),
    ),
    surface=gs.surfaces.Default(color=(0.9, 0.8, 0.6, 1.0)),
)

# -------------------------------------------------------------------
# Simulation loop
for i in range(3000):
    scene.step()
    if i % 100 == 0:
        print(f"Step {i}")