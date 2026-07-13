import genesis as gs

def main():
    gs.init()
    scene = gs.Scene()
    # Add a static ground plane
    scene.add_entity(gs.morphs.Plane())
    # Stack three boxes vertically
    size = (0.5, 0.5, 0.5)
    z_offsets = [size[2] / 2, size[2] * 1.5, size[2] * 2.5]
    for z in z_offsets:
        scene.add_entity(
            gs.morphs.Box(size=size, pos=(0.0, 0.0, z))
        )
    scene.build()
    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()