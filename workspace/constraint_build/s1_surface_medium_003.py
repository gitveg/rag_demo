import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(show_viewer=True)

    # Cube (shiny metallic silver finish not applied – surface API not documented)
    cube_morph = gs.options.morphs.Box(size=(0.5, 0.5, 0.5))
    cube = scene.add_entity(morph=cube_morph, material=gs.materials.Rigid())

    # Cylinder (matte blue plastic finish not applied – surface API not documented)
    cylinder_morph = gs.options.morphs.Cylinder(radius=0.3, height=0.6)
    cylinder = scene.add_entity(morph=cylinder_morph, material=gs.materials.Rigid())

    scene.build()

    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()