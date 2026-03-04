import time
import os
import numpy as np
import genesis as gs


def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -5.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.0),
        camera_fov=40,
        max_FPS=200,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=False,
        renderer=gs.options.renderers.BatchRenderer(resolution=(1920, 1200)),
    )

    scene.add_entity(morph=gs.morphs.Plane())
    scene.build()

    recorder = gs.options.recorders.VideoFile(path="output.mp4", fps=30)

    def get_frame():
        return scene.visualizer.camera.render()

    scene.start_recording(recorder=recorder, data_func=get_frame)

    for _ in range(100):
        scene.step()
        time.sleep(0.01)

    scene.stop_recording()


if __name__ == "__main__":
    main()