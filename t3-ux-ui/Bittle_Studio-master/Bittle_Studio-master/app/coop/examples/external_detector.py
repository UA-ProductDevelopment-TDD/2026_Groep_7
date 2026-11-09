"""Example outside module for the Coop Guard simulator, and the template for the team's AI camera model.

It is a separate program: it joins the running simulator over HTTP (coop/hub_client.py), downloads each new head
camera image, looks for fox, chicken and person, and publishes what it found on 'detections/external'. The
simulator's detector reads that topic when the scenario sets detector type 'external'; the dashboard lists this
program as the module 'ai-camera' and marks it stale if its heartbeat stops.

Run it while the Coop simulator is running (start the simulator first and let it run or step), with the detector
type set to external in the scenario:

    .venv\\Scripts\\python.exe app\\coop\\examples\\external_detector.py
    .venv\\Scripts\\python.exe app\\coop\\examples\\external_detector.py --url http://192.168.1.20:8780  # other computer

Stop it with Ctrl+C: it unregisters itself.

Where the model plugs in: recognise() below receives the image as a numpy array and returns the objects it sees.
The stand-in there only finds fox-orange, chicken-white and jacket-blue patches (the colour classifier of the
simulator's own detector); a trained model replaces its body. The simulator accepts for every object

    {'label': 'fox' | 'chicken' | 'person', 'confidence': 0 to 1, 'bbox': [x0, y0, x1, y1]}

with the box in image pixels (x1 and y1 just outside it). Optional: 'pixels', 'distance' in metres and 'bearing'
in degrees (positive to the left of the image centre); the simulator works the bearing out from the box if it is
missing. Objects that do not fit are skipped, and the simulator counts them on the detector's module page.

A detection is only used for 'stale' simulation seconds (scenario setting, 2 s by default). Simulation time runs
faster than the clock at a speed above 1x, so keep the model quick or lower the speed.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # app/, so that `coop` imports like inside the simulator

from coop import png  # noqa: E402
from coop.detector import colour_blobs  # noqa: E402
from coop.hub_client import DEFAULT_URL, HubClient, HubError  # noqa: E402

MODULE_ID = 'ai-camera'
CAMERA = 'head-cam'
TOPIC = 'detections/external'
POLL = .1  # seconds between looks at the camera's latest message; the camera makes 4 frames per simulated second


def recognise(rgb):
    """Plug the image-recognition model in here. rgb: uint8 numpy array of shape (height, width, 3).

    Returns a list of {'label', 'confidence', 'bbox'} as described at the top of this file.
    """
    # Stand-in: colour patches. Replace these two lines with the model, for example
    #     return [{'label': names[c], 'confidence': float(s), 'bbox': [float(v) for v in box]} for box, s, c in model(rgb)]
    # (a PyTorch, TensorFlow Lite or ONNX model needs its own libraries in its own environment, not the simulator's).
    found = colour_blobs(rgb)
    return [{key: found_one[key] for key in ('label', 'confidence', 'bbox', 'pixels')} for found_one in found]


def newest_frame(client):
    """(frame number, rgb array) of the camera's newest image, or None before its first frame.

    The camera's message names the frame, the image comes separately: the number is read again after the download
    and the pair is taken again if the camera moved on in between, so the number belongs to the image.
    """
    topic = 'camera/' + CAMERA
    for _ in range(3):
        message = client.latest(topic).get(topic)  # latest() matches prefixes: pick the exact topic
        if message is None:
            return None
        image = png.decode(client.frame(CAMERA))
        again = client.latest(topic).get(topic)
        if again is not None and again['value']['frame'] == message['value']['frame']:
            break
    return message['value']['frame'], image


def step(client, last=None):
    """Recognise and publish if the camera has a frame other than `last`; returns the frame number it has now."""
    frame = newest_frame(client)
    if frame is None or frame[0] == last:
        return last
    number, image = frame
    objects = recognise(image)
    client.publish(TOPIC, {'frame': number, 'objects': objects})
    print(f'frame {number}: ' + (', '.join(f"{o['label']} {o['confidence']:.2f}" for o in objects) or 'nothing'))
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description='Example outside module: finds fox, chicken and person in the head camera.')
    parser.add_argument('--url', default=DEFAULT_URL, help=f'address of the Coop simulator (default {DEFAULT_URL})')
    args = parser.parse_args(argv)
    client = HubClient(MODULE_ID, 'AI camera (example)', kind='detector', publishes=[TOPIC], subscribes=['camera/' + CAMERA],
                       limitations=['Example only: finds colour patches in the simulator\'s flat colours, no trained model.'],
                       info={'program': Path(__file__).name}, base_url=args.url)
    try:
        client.register()
    except HubError as error:
        sys.exit(f'Could not register: {error}')
    client.start_heartbeat()
    print(f'Registered as {MODULE_ID} at {args.url}. Press Ctrl+C to stop.')
    last = None
    try:
        while True:
            try:
                last = step(client, last)
            except HubError as error:  # a hiccup or a stopped simulator: keep the module alive and try again
                print('Waiting for the simulator:', error)
                time.sleep(1.)
            time.sleep(POLL)
    except KeyboardInterrupt:
        print('Stopping.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
