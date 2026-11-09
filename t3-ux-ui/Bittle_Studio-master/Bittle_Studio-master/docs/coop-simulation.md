# Coop Guard simulator

A digital twin for the *Kippenhok-waakhond* concept (TDD M2, group 7): Bittle patrols a chicken coop on rough ground at night, recognises a fox, chases it off, walks back to its dock and charges. The simulator tests design choices before hardware is ordered: the leg design, where sensors go, how much the extra modules weigh, how Bittle copes with bumps, stones and mud, how well the camera sees at night, how precisely it must dock and how long the battery lasts.

It runs next to Bittle Studio and reuses its PyBullet engine, its Bittle model and Petoi's own gait data. The Studio itself is unchanged.

**Status: everything in the proposal is built** (sections 1-7 and 10; sections 8 and 9 were missing from it).
- **Phase 1:** terrain, coop, dock, robot model and payload, camera, ToF and IMU sensors, the module hub and the dashboard.
- **Leg design:** stones, parametric legs (longer legs, splay and fan angles, knees pointing forward or backward), generated gaits including the crab gait, servo limits and a traverse test.
- **Phase 2:** chickens, a fox and a farmer; day and night with infrared; a replaceable detector; the patrol route; the behaviour (patrol → detect → deter → back to the dock → charge); docking with a capture zone; battery and energy; the metrics of proposal section 7.
- **Phase 3:** batch experiments (variants × seeds in parallel worker processes, with CSV export), a browser test and this guide.

## Start it

| | Windows | Mac | Linux |
|---|---|---|---|
| Start | `launchers/windows/Start Coop Simulator.cmd` | `launchers/mac/Start Coop Simulator.command` | `launchers/linux/start-coop.sh` |

It opens http://127.0.0.1:8780. Run **Setup** first if the Studio has never been installed on this computer; no extra packages are needed.

**A first run:** press **▶ Mission** in the top bar. Bittle walks the patrol route around the run. At 40 s a fox comes from the north-east; the **Mission** tab shows the camera image with what the detector finds, the alarm, the chase and the fox running off, then the walk back to the dock. The metrics fill in as it goes.

## Scenarios

Everything the simulation uses is in one JSON *scenario*: terrain, mud, stones, coop and fence, dock, robot model, legs, gait, servos, payload, sensors, day or night, chickens, visitors, patrol route, detector, behaviour, battery and simulation speed. Scenarios are saved in `coop-scenarios/`; the last one used is restored at the next start (`user-data/coop-session.json`). `app/coop/config.py` holds the defaults and checks every value, and an error names the setting that is wrong.

Bundled:
- **default:** 3 × 2 m fenced run, 12 mm bumps, one mud patch, 4 chickens in the run and 2 outside, a fox at 40 s and a farmer at 120 s.
- **flat-baseline:** no bumps and no mud, the reference to compare against.
- **heavy-mud:** 20 mm bumps, three mud patches on the patrol line.
- **spider:** the spider leg design with its crawl.
- **crab:** the crab leg design (front knees forward) with the crab gait; the dock's stop block is moved to fit it and the head camera sits 3 cm higher, looking 10° up, so the knees stay out of its picture.
- **stony-mud:** 20 mm bumps, 60 stones and a mud patch on the path ahead of the start. This is the course for the traverse test.
- **night-patrol:** the default coop at night, with the camera's infrared light.

Applying a scenario restarts the run from the robot's start position. Choosing another robot model moves payload and sensors whose link that robot lacks to its base link, and says so in the event log. If the robot reaches the edge of the terrain, the run pauses: there is no ground beyond it.

Units: metres, degrees, seconds, kilograms. World axes: X east, Y north, Z up. A heading of 0° faces +X, 90° faces +Y.

Sensor positions use **body axes**: x forward, y left, z up, measured from the origin of the link the sensor is attached to. A sensor on `head-link` turns with the neck.

## Modules

Every part is a module of the hub, with its settings, a self-test (**Hub → Run all self-tests** in the dashboard) and a list of what it does not model.

| Module | Does | Does not model |
|---|---|---|
| Physics (`session.py`) | PyBullet, 240 Hz, 80 solver iterations, real-time factor 0.5–8× or as fast as possible | Bending, sinking, deformation; contact friction is simplified |
| World (`world.py`) | Height-map terrain, mud patches with their own friction and a dip, stones, fenced run with posts, house, dock with a stop block | Sinking into mud; chicken wire is a solid, closed panel |
| Robot (`robot.py`, `legs.py`, `gaits.py`) | Bittle X or any URDF; leg designs; generated gaits; servo torque and speed limits; payload; foot friction; fall detection | Servo backlash, compliance, heating; the firmware balance controller |
| Camera (`sensors.py`) | Position on any link, field of view, resolution, range, frame rate; day, moonlight and infrared night images | Textures, shadows, lens distortion; IR reflection of real fur and grass |
| ToF, IMU (`sensors.py`) | VL53L0X: cone of rays, 2 m range, noise; MPU6050: orientation, gyro, accelerometer | Reflectivity, sunlight, multipath; IMU bias and drift |
| Animals & visitors (`actors.py`) | Chickens wandering inside and outside the run, a scripted fox, a farmer | Leg movement; reactions of chickens; a real fox's behaviour |
| Detector (`detector.py`) | Fox, chicken and person in the camera image: ideal (ground truth), colour blobs, or an outside program | Real image recognition (that is the AI camera module) |
| Behaviour (`behaviour.py`, `patrol.py`) | Patrol route, obstacle stop, detect, deter, return, dock, charge, self-righting | Localisation: the robot knows its pose exactly |
| Battery (`energy.py`) | Board power, servo current in proportion to torque, IR LEDs, charging at the dock | Voltage sag, capacity loss, charging curve |
| Metrics (`metrics.py`) | Route deviation, falls, coop coverage per lap, time to recognise the fox, false alarms, docking, energy per lap | — |

## Leg design, generated gaits and the traverse test

**Leg design** (`app/coop/legs.py`, Robot → Leg design). For the bundled Bittle you set:
- **Upper and lower leg length:** upper = shoulder axis to knee axis, lower = knee axis to foot tip. Stock Bittle measures 49-50 mm and 53-55 mm.
- **Splay:** each shoulder mount tilted outward, seen from the front.
- **Fan:** each shoulder mount turned outward, seen from above: front legs toward the front corners, rear legs toward the rear corners.
- **Front and rear shoulder offset:** shoulders moved forward or back.
- **Front knees and rear knees: backward or forward.** Stock Bittle's knees all point backward. *Forward* mounts the lower leg half a turn round on the knee servo: at the zero pose the shin sticks out backward instead of forward, and the leg is the mirror image of a stock leg, joint limits included. Two servos per leg remain.

The simulator writes a variant URDF to `robot-models/bittle/generated/` (git-ignored): leg meshes stretched along the leg, knee joints moved, leg mass in proportion to length.

Presets:
- **Spider:** legs 1.5 times as long (75 and 83 mm), 25° splay, front shoulders 20 mm forward, all knees backward, a low and wide crawl.
- **Crab** (the team's design): the same long legs, **front knees forward and rear knees backward** (the knees point outward, away from the body), 15° splay, front shoulders 20 mm forward, and the **crab gait**.

**Generated gaits** (`app/coop/gaits.py`, Robot → Gait). Petoi's skills are joint-angle tables for the stock legs and do not fit other designs. The generator plans foot paths instead: each foot rests a set distance below its shoulder (hip height) with a reach forward or back, pushes back along the ground and swings forward with a lift. Two-link inverse kinematics in the leg's swing plane turns those paths into joint angles, exact to well under 1 mm, with each knee bending the way the design says.
- **Crawl:** one foot at a time, the most stable gait.
- **Trot:** diagonal pairs.
- **Crab:** diagonal pairs, like a crab's alternating leg sets, turned to walk forward instead of sideways. The front feet reach ahead and pull, the rear feet reach back and push. Each foot is lifted straight up, carried forward and set straight down, so it does not drag through mud or catch the edge of a stone. The feet are on the ground 60 % of the cycle, so all four stand at every change of pair.
- **Motions:** stance, forward, backward, arcs, veers (one side's steps at 60 %) and turning on the spot.

The **walking-pattern overview** under the gait settings draws the legs from the side over one cycle (hip, knee and foot of all four legs, the foot paths, which feet are on the ground) and lists every joint's range of angles against its limits. Change hip height, reach, stride, step height or cycle time, apply, and see the new angles at once.

The crab preset was tuned in a sweep on level ground: 5.3 cm/s with 5° drift in 12 s. Without splay the narrow, tall trot tips over; with the body at 85 mm instead of 70 mm it drifted more. It turns on the spot at about 9°/s; shorter steps on one side hardly turn it (under 1°/s), so the patrol steers it by turning on the spot.

**Servos.** Every joint motor is limited to the scenario's servo torque and speed. The default 0.29 Nm (3 kg·cm) is a retailer figure for Bittle's metal-gear servo set that Petoi does not confirm; enter the datasheet value when you have it. The default 350 °/s matches the speed the Studio's skill timing already assumes. The Robot tab shows each joint's torque and how often it sits at the limit.

**Stones** (Scene → Stones). Fixed boxes of 0.5-20 cm, sunk about a third into the ground, scattered over the terrain or concentrated in a rectangle such as the patrol path. Never inside the run, near the dock or near the start.

**Traverse test** (Robot → Traverse test). The same course is walked by stock legs with Petoi's walk, stock legs with the generated crawl, spider legs with the crawl, crab legs with the crab gait, and the current design when it is no preset. The course is the current scenario, from the start position along the start heading. Every run happens in a separate, sensorless world in a worker process, so the running simulation is not disturbed and the runs go side by side. The test reports distance, speed, sideways drift, turning, falls, how often a servo was at its limit, and the share of time in mud and touching stones.

Traverse test on the stony and muddy path (20 mm bumps, 60 stones, mud of friction 0.25), 30 s:

| Design | Distance | Turned | Servo at its limit | Touching stones |
|---|---|---|---|---|
| Stock legs, Petoi walk | 42 cm | −13° | 24 % of the time | 65 % |
| Stock legs, generated crawl | 46 cm | 26° | 15 % | 43 % |
| Spider legs, crawl | 52 cm | 47° | 1 % | 42 % |
| **Crab legs, crab gait** | **90 cm** | −60° | 2 % | 32 % |

The crab legs go about twice as far as the stock legs over stones and mud, touch the stones less and hardly load the servos. They also turn the most when walking straight without steering; on patrol the steering takes that out (see the experiments below).

## Animals and visitors

Scene → Chickens and Scene → Visitors (`app/coop/actors.py`).
- **Chickens** wander at a set speed with pauses to peck: some inside the run (outside the house), some in a band 0.15-1 m outside the fence, where they get in the robot's way. The seed fixes their places and walks.
- **Visitors** walk a path from their appear time. *Loop* makes them pace the path back and forth. A **fox** runs off when the robot, deterring, comes within its flee distance: away from the robot, to the nearest terrain edge, at three times its speed. A **person** never does. The default fox appears at 40 s in the north-east and prowls along the east and south fence; the farmer walks past on the north side at 120 s.

Animals and people are shapes in flat colours that never push the robot: the camera and the ToF sensors see them, the physics lets the robot through. Paths can be typed in or clicked on the ground in the 3D view.

## Day and night

Scene → Day and night. At night the camera image is the daylight render times the moonlight (5 % by default), plus what the camera's **infrared LEDs** light up: a grey image whose brightness falls with the square of the distance, set so that a light surface at the infrared range (2.5 m by default) is just bright enough for the detector. Noise is added at night. The IR LEDs cost power (1 W by default). The 3D view turns dark too.

## Recognising fox, chicken and person

The camera only takes pictures; the **detector** (`app/coop/detector.py`, Mission → Detector) says what is in them, as the proposal asks, so it can be replaced:
- **ground-truth:** an ideal model. It knows which body each pixel shows; only size (minimum pixels) and light (minimum brightness) limit it. Use it to test everything else.
- **colour-blob:** a simple hand-made classifier of the image colours: fox orange, chicken cream-white, jacket blue. It shows what a weak recogniser does: in the grey infrared image it finds nothing, and some colours in the scene come close.
- **external:** the detections an outside program publishes on a hub topic: the place for the team's AI camera module. `app/coop/examples/external_detector.py` is a working template: it registers with the hub, downloads every new camera frame, runs `recognise(rgb)` (a stand-in; the model plugs in there) and publishes `{'frame', 'objects': [{'label', 'confidence', 'bbox'}]}` on `detections/external`. Keep the simulation speed at 1× with an outside model: a detection only counts for the stale time (2 s by default) in simulated seconds.

```bash
.venv/Scripts/python.exe app/coop/examples/external_detector.py
```

The behaviour raises the alarm after the set number of frames in a row with a fox (2 by default, half a second at 4 frames per second).

## Patrol, behaviour and docking

Mission tab and **▶ Mission** in the top bar (`app/coop/behaviour.py`, `app/coop/patrol.py`). The state machine of proposal section 6:

1. **patrol:** follow the route, a closed loop of waypoints around the run (Mission → Patrol route; click **Add waypoints on the ground** to place them in the 3D view). The robot steers toward a point 40 cm further along the route. Stock legs walk with Petoi's skills (walk, arcs, turning on the spot); other leg designs with the generated gait. When the front ToF sees something within 12 cm (a chicken), the robot stops; after 4 s it turns away.
2. **detect:** a fox in the image: the robot stops and looks until enough frames confirm it (the **alarm**), or gives up after 2 s without one.
3. **deter:** the deterrent is on (light and sound are not modelled further); the robot walks toward the fox, up to the chase distance. When no fox was seen for the deter time (10 s), or after 90 s at most, it goes back.
4. **return:** walk to the approach point 40 cm behind the dock. Also when the battery is low (30 %) or after the set number of laps.
5. **dock:** turn to the dock's heading, walk in along the dock axis. Inside the **capture zone** (3 cm, 10° by default) the magnet latches it; when it goes past, more than 15 cm aside or makes no progress for 4 s, it backs out and tries again (3 attempts).
6. **charge:** latched to the dock until the battery is at 90 %; then **undock** (back out) and patrol on.

After a fall the robot stands up again after 3 s where it lies (Bittle's firmware can self-right; how is not simulated). With an empty battery the mission stops.

**The dock and the leg design.** The dock's stop block must stand further ahead than the robot reaches with its feet and body: stock Bittle reaches 113 mm ahead of its body centre, the crab legs 171 mm while walking. With the stop block at the stock 120 mm, the crab's front feet hit it before its body is in the capture zone. Scene → Dock → **stop block distance** (190 mm in the crab scenario); the behaviour's self-test checks it.

## Battery and energy

Mission → Energy (`app/coop/energy.py`). The boards draw a constant power (1.5 W: BiBoard, ESP32-S3 camera board, ToF sensors), the IR LEDs 1 W at night, and every servo a small idle current plus a current in proportion to its torque, up to its stall current (1 A) at the servo torque limit. Holding a pose costs energy too, as on the real robot. The default battery is 7.4 V × 1000 mAh = 7.4 Wh; the dock charges at 7 W. **These are assumptions**: read the battery label and measure the boards' current.

## What the simulation measures

The metrics of proposal section 7 (`app/coop/metrics.py`, Mission → Metrics; `GET /api/coop/metrics`, or **Download metrics**):
- **Route deviation:** distance to the route while patrolling, mean and largest, per lap and in total.
- **Falls** and self-rightings; obstacle stops.
- **Coop coverage:** points every 25 cm along the outside of the fence, halfway up; a point counts as seen when a camera frame shows it (in the image, not hidden behind something nearer, within range, bright enough for the detector). Per finished lap, and over the whole run.
- **Camera image showing the robot itself:** the share of every frame that shows the robot's own legs or body.
- **Time to recognise the fox:** from its appearance to the alarm, and from the first frame that really shows it to the alarm.
- **False alarms:** alarms while no fox was in view, and sightings that were not confirmed.
- **Docking:** attempts, successes, success rate, and the error beside the dock axis, along it and in heading when it latched.
- **Energy:** used, charged, per lap; the lowest state of charge.

## Batch experiments

Experiments tab (`app/coop/experiments.py`, `app/coop/jobs.py`). A single run says little: the open-loop gaits drift differently on every patch of ground. An experiment runs the mission for a set time per **variant** (another leg design, night, another detector, another locomotion, or any change as JSON) and per **seed** (each seed changes the terrain's bumps, the stones and the chickens). The runs go to worker processes, several at a time, and the result is the mean and spread of every metric per variant, with a CSV of all runs.

First results (3 seeds per variant unless noted; mean ± spread over the seeds). They are indications for this simulator with assumed servo and battery values, not measurements of the real robot.

**Patrol around the default coop, by day, 900 s:**

| | Stock legs | Crab legs | Crab legs, camera raised |
|---|---|---|---|
| Distance walked | 33.9 ± 0.3 m | 34.8 ± 1.4 m | 34.4 ± 1.2 m |
| Laps | 1 | 1 | 1 |
| Route deviation | 3.3 cm | 2.9 cm | 3.1 cm |
| Falls | 0.3 | 0 | 0 |
| Fence seen during the run | 87 % | 92 % | 92 % |
| Camera image showing the robot itself | 0 % | **14 %** | 0.2 % |
| Fox alarm after it came into view | 0.3 s | 0.3 s | 0.3 s |
| Fox chased off | 3 of 3 | 3 of 3 | 3 of 3 |
| Docking | 3 of 3, 7 mm beside | 3 of 3, 10 mm | 3 of 3, 14 mm |
| Energy per lap | 1.38 Wh | 1.76 Wh (+28 %) | 1.78 Wh |
| Battery left | 71 % | 65 % | 65 % |

The time from the fox's appearance to the alarm (0.7 s stock, 8 s crab) depends mostly on where along the route the robot happens to be when it comes, not on the legs: once the fox is in view, every variant raises the alarm within 0.3 s.

**The stony and muddy path, 600 s:** the crab legs walked 15.3 ± 2.1 m, the stock legs 8.6 ± 2.7 m (+77 %), neither fell, and the route deviation was the same (7-8 cm). The crab used 1.5 Wh against 1.2 Wh.

**Recognising the fox by day and night** (default coop, 150 s, 2 seeds):

| | Alarm after the fox appeared | After it was in view (lit) | Fox chased off | Fence seen |
|---|---|---|---|---|
| Day, ideal detector | 0.8 s | 0.3 s | yes | 45 % |
| Day, colour blobs | 2.2 s | 1.7 s | yes | 36 % |
| Night with IR, ideal detector | 8.3 s (once within 2.5 m) | 0.3 s | yes | 48 % |
| Night with IR, colour blobs | never | – | no | 41 % |
| Night without IR, ideal detector | never | – | no | 0 % |

No false alarms in any run.

**What the experiments say about the design:**
- **The crab legs are the better design for the stony and muddy ground** the team expected: about twice as far in the traverse test and three quarters further on patrol over stones and mud, without falls and with the servos far from their limit. On the easier default ground they patrol as well as the stock legs.
- **They cost about 28 % more energy per lap** (longer legs, more torque to hold the body).
- **The forward knees get into the head camera's picture:** 14 % of the image while walking. Mounting the camera 3 cm higher and 10° up takes that to 0.2 % (the crab scenario does so).
- **The dock must be made for the legs:** the stop block 190 mm ahead of the dock point instead of 120 mm.
- **At night the camera needs its infrared light, and the recogniser needs to work on grey images:** a colour-based recogniser finds nothing in infrared. With infrared the fox is only seen within the infrared range (2.5 m assumed), so it comes closer before the alarm.
- **Docking within 3 cm and 10° succeeded every time here, but with perfect knowledge of the robot's position.** On the real robot the position comes from its sensors; test docking on the real dock early.

## The hub: connecting outside programs

The hub connects every module. Built-in modules publish on topics; outside programs (the AI camera model on a laptop now, an ESP32-S3 later) register, read topics and camera frames, and publish their results the same way.

| Topic | Published by | Contents |
|---|---|---|
| `robot/state` | robot | position, heading, roll, pitch, height, speed, fallen, current skill (20 per simulated second) |
| `camera/<id>` | each camera | frame number, lighting, brightness, nearest distance, visible objects, `url` of the PNG |
| `sensors/<id>` | each ToF / IMU | its reading |
| `detections/<camera>` | detector | objects found in each frame: label, confidence, box, pixels, distance, bearing |
| `detections/external` | an outside program | its detections, read by the detector of type external |
| `behaviour/state`, `behaviour/alarm` | behaviour | every change of state; every alarm (true or false) |
| `energy/battery`, `metrics/summary` | battery, metrics | once per simulated second |
| `session/event` | session | log lines (scenario applied, robot fell, fox appeared, ...) |
| `tests/traverse` | session | the latest traverse test |
| `hub/self-test` | hub | each self-test result |

HTTP API (local only, port 8780):

| Call | Purpose |
|---|---|
| `GET /api/coop/state`, `GET /api/coop/model` | the live state; the scenario and everything static |
| `POST /api/coop/command` | `{action: run | reset | speed | drive | gait | mission | refresh-sensors, value}` |
| `GET /api/coop/gait-preview?motion=forward` | the generated gait from the side, frame by frame |
| `GET /api/coop/metrics` | the metrics of the current run |
| `POST /api/coop/jobs/traverse`, `POST /api/coop/jobs/experiment` | start a traverse test or an experiment in worker processes |
| `GET /api/coop/jobs`, `GET /api/coop/jobs/{id}`, `DELETE ...`, `GET .../csv` | progress, result, cancel, CSV |
| `GET /api/hub/modules` | every module: status, settings, limitations, last self-test |
| `POST /api/hub/modules/{id}/test`, `POST /api/hub/test-all` | run self-tests |
| `GET /api/hub/topics?prefix=sensors/` | latest message per topic |
| `GET /api/hub/stream?prefix=...` | live messages (Server-Sent Events) |
| `GET /api/hub/frame/{camera}.png` | latest camera image |
| `POST /api/hub/register` | register an outside module `{id, name, kind, publishes, subscribes, limitations}` |
| `POST /api/hub/modules/{id}/heartbeat` | keep it alive (stale after 5 s) |
| `POST /api/hub/publish` | `{module, topic, value}`, at most 64 KB |
| `DELETE /api/hub/modules/{id}` | unregister an outside module |

`app/coop/hub_client.py` wraps these calls (standard library only). `app/coop/examples/external_monitor.py` and `external_detector.py` are working outside modules.

## Open points

- **Servo torque:** 0.29 Nm is unconfirmed; Bittle X may use plastic P1L servos. Read the label and set it in Robot → Servos: it decides whether longer legs are realistic.
- **Battery and power:** all energy values are assumptions until measured.
- **Printed legs:** their mass grows with length in the model; weigh the real parts and add the difference as payload. Check that a mirrored shin clears the thigh.
- **The real robot needs to know where it is:** the simulated behaviour uses its exact pose. Docking precision and route deviation on the real robot depend on how it estimates its position (odometry, IMU, ToF along the fence, a beacon at the dock).
- **Sections 8 and 9** of the proposal were missing.

## Tests

```bash
.venv/Scripts/python.exe -m unittest discover -s app/tests -t app -p "test_coop_*.py" -v
```
