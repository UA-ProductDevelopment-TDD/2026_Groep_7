"""Example outside module for the Coop Guard simulator, and the template for an AI camera module.

It is a separate program: it joins the running simulator over HTTP (coop/hub_client.py), reads the head camera and
the distance sensors, and publishes a one-line summary on 'example/summary'. The dashboard lists it as the module
'frame-monitor' and marks it stale if its heartbeat stops.

Run it while the Coop simulator is running (start the simulator first and let it run or step):

    .venv\\Scripts\\python.exe app\\coop\\examples\\external_monitor.py
    .venv\\Scripts\\python.exe app\\coop\\examples\\external_monitor.py --url http://192.168.1.20:8780  # other computer

Stop it with Ctrl+C: it unregisters itself.

Where an image-recognition model plugs in: analyse() below receives the newest head camera frame as PNG bytes plus
its message (frame number, brightness, what the simulator knows is visible). A real detector decodes the PNG with
its own libraries (for example PIL.Image.open(io.BytesIO(png)) in the model's environment, so the simulator itself
needs none), runs the model, and returns fields such as {'detections': [{'label': 'fox', 'score': .9}]}. Publish
those on a topic of its own (say 'vision/detections') with client.publish(), and list that topic in `publishes`."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # app/, so that `coop` imports like inside the simulator

from coop.hub_client import DEFAULT_URL, HubClient, HubError  # noqa: E402

MODULE_ID = 'frame-monitor'
CAMERA = 'head-cam'
TOF_SENSORS = ('tof-left', 'tof-front')


def analyse(png, camera):
    """Plug an image-recognition model in here. Returns extra fields for the summary (none in this example)."""
    return {}


def summarise(client):
    """Read the newest camera and distance messages and build the summary that is published."""
    topics = client.latest()
    camera = topics.get('camera/' + CAMERA, {}).get('value')
    distances = [topics[f'sensors/{name}']['value']['distance'] for name in TOF_SENSORS
                 if f'sensors/{name}' in topics and topics[f'sensors/{name}']['value'].get('distance') is not None]
    summary = {'camera_frame': None, 'brightness': None, 'nearest_tof_m': min(distances) if distances else None,
               'png_bytes': None}
    if camera:
        png = client.frame(CAMERA)
        summary.update(camera_frame=camera.get('frame'), brightness=camera.get('brightness'), png_bytes=len(png))
        summary.update(analyse(png, camera))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Example outside module: summarises the head camera and ToF sensors.')
    parser.add_argument('--url', default=DEFAULT_URL, help=f'address of the Coop simulator (default {DEFAULT_URL})')
    args = parser.parse_args(argv)
    client = HubClient(MODULE_ID, 'Frame monitor (example)', kind='example', publishes=['example/summary'],
                       subscribes=['camera/' + CAMERA] + ['sensors/' + name for name in TOF_SENSORS],
                       limitations=['Example only: reads frame sizes, it does not look at the pixels.'],
                       info={'program': Path(__file__).name}, base_url=args.url)
    try:
        client.register()
    except HubError as error:
        sys.exit(f'Could not register: {error}')
    client.start_heartbeat()
    print(f'Registered as {MODULE_ID} at {args.url}. Press Ctrl+C to stop.')
    try:
        while True:
            try:
                summary = summarise(client)
                client.publish('example/summary', summary)
                print(summary)
            except HubError as error:  # a hiccup or a stopped simulator: keep the module alive and try again
                print('Waiting for the simulator:', error)
            time.sleep(1.)
    except KeyboardInterrupt:
        print('Stopping.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
