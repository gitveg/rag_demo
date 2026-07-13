import genesis as gs
import numpy as np
import time

def main():
    gs.init()

    # Create scene with default solver settings
    scene = gs.Scene(
        show_viewer=True,
    )

    # Add drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            pos=(0.0, 0.0, 1.0),   # start at 1m altitude
        ),
        material=gs.materials.Rigid(),
    )

    # Sandy desert terrain (colored ground plane)
    ground = scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(
            color=(0.76, 0.60, 0.42, 1.0),  # sandy brown
        ),
    )

    # Build the scene
    scene.build()

    # Hover RPM (taken from the reference DroneController)
    hover_rpm = 14475.8
    drone.set_propellels_rpm([hover_rpm] * 4)

    # Strong wind force field
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),   # blowing along +X
        strength=8.0,
        radius=50.0,
        center=(0.0, 0.0, 1.5),
    )
    scene.add_force_field(wind)
    wind.deactivate()   # start with no wind

    wind_active = False
    print("Simulation started. Press ESC in viewer to exit.")

    # Simulation loop
    for step in range(5000):   # roughly 50 s at dt=0.01
        # Keep hovering (no manual control)
        drone.set_propellels_rpm([hover_rpm] * 4)

        # Toggle wind: active for 30 steps, inactive for 70 – "occasionally pushes"
        should_be_active = (step % 100) < 30
        if should_be_active and not wind_active:
            wind.activate()
            wind_active = True
        elif not should_be_active and wind_active:
            wind.deactivate()
            wind_active = False

        scene.step()
        time.sleep(0.001)  # small pause to keep viewer responsive

    print("Simulation finished.")

if __name__ == "__main__":
    main()