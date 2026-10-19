# bittle-urdf-ua-tdd

| | |
|---|---|
| Link in de slides | https://github.com/UA-ProductDevelopment-TDD/Bittle_URDF |
| Opgehaald van | https://github.com/UA-ProductDevelopment-TDD/Bittle_URDF |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | git clone zonder bestandsinhoud; README + volledige bestandenlijst, geen CAD- of codebestanden overgenomen |

---

Branch `main`, laatste commit `0a6f2303fe98fa3d7e78c3b87cd24fd39352ad9f 2026-10-01`. Bestanden: 27.

## README (README.md)

# Bittle X — Simulation-Ready URDF

This repository contains the **University of Antwerp simulation version of the Petoi Bittle X URDF**.

The model has already been prepared for use in a physics simulator. You therefore **do not need to build or repair the URDF yourself before starting**.

The goal of this model is to let you experiment with:

- robot motion,
- joint control,
- new mechanical designs,
- reach and clearance,
- stability,
- sensing,
- control strategies,
- and eventually transferring ideas from simulation to the physical Bittle X.

For this course, we recommend using **PyBullet**.

---

# 1. What is a URDF?

**URDF** stands for **Unified Robot Description Format**.

A URDF describes the structure of a robot using XML.

It defines, among other things:

- the different rigid parts of the robot (**links**),
- how these parts are connected (**joints**),
- joint rotation axes,
- joint limits,
- mass and inertia,
- collision geometry,
- visual geometry.

You can think of the URDF as the bridge between your **CAD model** and a **robotics simulator**.

A simplified robot structure looks like this:

```text
Body
│
├── Front Left Hip
│   └── Front Left Knee
│
├── Front Right Hip
│   └── Front Right Knee
│
├── Rear Left Hip
│   └── Rear Left Knee
│
└── Rear Right Hip
    └── Rear Right Knee
```

Each part is a **link**.

The connections between the parts are **joints**.

---

# 2. Repository structure

Your repository will contain the URDF together with the 3D geometry needed by the model.

A typical structure looks like:

```text
Bittle_X_URDF/
│
├── urdf/
│   └── bittle_x.urdf
│
├── meshes/
│   ├── body.obj
│   ├── leg.obj
│   ├── foot.obj
│   └── ...
│
├── simulation/
│   └── test_bittle.py
│
└── README.md
```

The exact filenames may differ slightly in your repository.

### Important

Do not randomly move the URDF or mesh files.

The URDF contains file paths pointing toward the mesh files. If you change the folder structure, PyBullet may no longer be able to find the geometry.

---

# 3. The model is already simulation-ready

The URDF supplied for this course has already been prepared for simulation.

This means that the important elements required by a physics simulator have been configured, including:

- robot link structure,
- joint hierarchy,
- joint axes,
- joint limits,
- visual meshes,
- collision geometry,
- link origins,
- basic inertial properties.

Your first task is therefore **not to repair the robot model**.

Instead, you can start by loading the robot in PyBullet and understanding how the model behaves.

---

# 4. Installing PyBullet

Make sure Python is installed.

Then install PyBullet:

```bash
pip install pybullet
```

You can check the installation with:

```bash
python -c "import pybullet; print('PyBullet installed')"
```

---

# 5. Loading Bittle X in PyBullet

A minimal simulation can look like this:

```python
import pybullet as p
import pybullet_data
import time

# Start the simulator
physicsClient = p.connect(p.GUI)

# Standard PyBullet assets
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Gravity
p.setGravity(0, 0, -9.81)

# Ground plane
plane_id = p.loadURDF("plane.urdf")

# Load Bittle X
robot_id = p.loadURDF(
    "urdf/bittle_x.urdf",
    basePosition=[0, 0, 0.2]
)

# Run simulation
while True:
    p.stepSimulation()
    time.sleep(1 / 240)
```

Run the script:

```bash
python simulation/test_bittle.py
```

A PyBullet window should open containing:

- the ground plane,
- the Bittle X,
- gravity,
- and the physics simulation.

---

# 6. Inspecting the joints

Before controlling the robot, it is useful to inspect which joints PyBullet has loaded.

```python
num_joints = p.getNumJoints(robot_id)

print("Number of joints:", num_joints)

for i in range(num_joints):
    info = p.getJointInfo(robot_id, i)

    joint_index = info[0]
    joint_name = info[1].decode("utf-8")

    print(joint_index, joint_name)
```

This gives you something similar to:

```text
0 front_left_hip
1 front_left_knee
2 front_right_hip
3 front_right_knee
...
```

The exact names and indices depend on the supplied URDF.

### Important

The **PyBullet joint index is not automatically the same as the servo number on the physical Bittle X**.

Always check the joint names before writing control code.

---

# 7. Moving a joint

You can command a joint using:

```python
p.setJointMotorControl2(
    bodyUniqueId=robot_id,
    jointIndex=0,
    controlMode=p.POSITION_CONTROL,
    targetPosition=0.5
)
```

`targetPosition` is expressed in **radians**.

For example:

```text
0 rad       = 0°
0.52 rad    ≈ 30°
1.57 rad    ≈ 90°
```

You can convert degrees to radians with:

```python
import math

angle = math.radians(30)
```

---

# 8. Controlling multiple joints

For a quadruped, you will normally control several joints together.

For example:

```python
joint_positions = {
    0: 0.4,
    1: -0.8,
    2: -0.4,
    3: 0.8
}

for joint, position in joint_positions.items():

    p.setJointMotorControl2(
        robot_id,
        joint,
        p.POSITION_CONTROL,
        targetPosition=position
    )
```

This is the beginning of creating:

- poses,
- walking patterns,
- behaviours,
- animations,
- or control algorithms.

---

# 9. Useful PyBullet functions

### Get the number of joints

```python
p.getNumJoints(robot_id)
```

### Get information about a joint

```python
p.getJointInfo(robot_id, joint_id)
```

### Read a joint position

```python
p.getJointState(robot_id, joint_id)
```

### Set a joint target

```python
p.setJointMotorControl2(...)
```

### Get robot position and orientation

```python
position, orientation = p.getBasePositionAndOrientation(robot_id)
```

### Get link position

```python
state = p.getLinkState(robot_id, link_id)
```

### Detect contacts

```python
contacts = p.getContactPoints(robot_id)
```

These functions allow you to start analysing the behaviour of your design instead of only visually observing it.

---

# 10. What can you test in simulation?

Physics simulation is most useful when you use it to answer a **design question**.

Do not simulate something only because you can.

Examples include:

## Reach & clearance

Can the robot reach the required position?

Does a leg collide with:

- the body,
- another leg,
- the environment,
- or a new component you added?

---

## Stability

Does the robot remain upright?

Questions could include:

- Does a new component make the robot tip over?
- What happens when the centre of mass changes?
- Is a wider stance more stable?
- Can the robot remain stable during a motion?

---

## Control

Can the robot perform the desired movement?

For example:

- Can the joints reach the required angles?
- Is the motion smooth?
- Does the robot follow the intended trajectory?
- What happens when the joint speed changes?

---

## Sensing

A simulator can also approximate sensors.

Examples include:

- distance sensors,
- contact sensors,
- IMUs,
- cameras,
- LiDAR.

This makes it possible to test simple **sense → decide → act** behaviours before implementing them on the physical robot.

---

# 11. Designer workflow

For this project, a useful workflow is:

```text
DESIGN QUESTION
      ↓
CAD
      ↓
Simplified simulation geometry
      ↓
URDF
      ↓
Physics simulator
      ↓
Test movement / collisions / stability
      ↓
Modify design
      ↓
Repeat
      ↓
Physical prototype
      ↓
Test on Bittle X
```

Simulation should therefore be considered part of the **iterative design process**.

You are not trying to make a perfect virtual copy of reality.

You are using simulation to make faster and better-informed design decisions.

---

# 12. Modifying the robot

During the project you may want to add:

- new body geometry,
- different legs,
- sensor mounts,
- protective structures,
- a head,
- a tail,
- accessories,
- additional mechanisms.

A typical workflow is:

```text
1. Design the component in CAD

2. Export simplified geometry
   ↓
   STL / OBJ

3. Add the geometry to the URDF

4. Define its position relative to the robot

5. Add collision geometry

6. Add mass and inertia where necessary

7. Load the model in PyBullet

8. Test the design

9. Build the physical version
```

---

# 13. Visual geometry vs collision geometry

A simulation often uses two different representations of an object.

### Visual geometry

Determines what the robot **looks like**.

```xml
<visual>
    ...
</visual>
```

This can contain a relatively detailed CAD mesh.

### Collision geometry

Determines how the robot **interacts physically**.

```xml
<collision>
    ...
</collision>
```

Collision geometry should normally be simpler.

For example, instead of using a very detailed leg mesh, you might approximate it with:

- a box,
- a cylinder,
- a capsule,
- or a simplified mesh.

Simpler collision geometry generally makes the simulation:

- faster,
- more stable,
- easier to debug.

---

# 14. Mass and inertia

Physics simulators do not only need geometry.

They also need information about how objects behave physically.

A URDF link can therefore contain:

```xml
<inertial>

    <mass value="0.1"/>

    <inertia
        ixx="..."
        ixy="..."
        ixz="..."
        iyy="..."
        iyz="..."
        izz="..."
    />

</inertial>
```

These values describe how mass is distributed through the object.

For your first experiments, the supplied model already contains the required simulation configuration.

When you make large modifications to the robot, however, you should consider whether the:

- mass,
- centre of mass,
- and inertia

should also change.

---

# 15. Simulation is not reality

A physics simulator is always an **approximation**.

A robot that works perfectly in PyBullet may behave differently in reality.

Differences can come from:

- servo backlash,
- flexible plastic components,
- cable forces,
- battery voltage,
- servo speed,
- motor torque,
- friction,
- inaccurate mass estimates,
- manufacturing tolerances,
- sensor noise,
- communication delays.

This difference is often called the:

## Sim-to-real gap

Therefore:

> **Simulation should guide physical testing, not replace it.**

Always verify important behaviour on the real Bittle X.

---

# 16. Common mistakes

### Robot falls immediately

Check:

- starting height,
- joint starting positions,
- gravity,
- collision geometry.

---

### Robot explodes or jumps violently

This often indicates:

- overlapping collision geometry,
- unrealistic masses,
- incorrect joint configuration,
- very large motor forces.

---

### Meshes are missing

Check the mesh paths inside the URDF.

For example:

```xml
<mesh filename="../meshes/body.obj"/>
```

Folder structure matters.

---

### Joint moves in the wrong direction

The joint axis or coordinate system may differ from what you expected.

Inspect:

```xml
<axis xyz="..."/>
```

Do not simply assume that positive rotation corresponds to the physical servo direction.

---

### Robot works in simulation but not in reality

This is normal to some extent.

Check:

- joint mapping,
- servo calibration,
- angle conventions,
- physical joint limits,
- servo speed,
- motor torque,
- centre of mass.

---

# 17. Recommended way of working

Keep your simulation work inside the team GitHub repository.

For example:

```text
simulation/
├── README.md
├── test_bittle.py
├── poses.py
├── experiments/
│   ├── stability_test.py
│   └── sensor_test.py
└── results/
```

For each important experiment, document:

```text
Design question

↓

Simulation setup

↓

What did you change?

↓

What did you observe?

↓

What design decision did you make?
```

Screenshots, short videos and plots are strongly encouraged.

The goal is not only to show that your simulation runs.

The goal is to show **how simulation informed your design process**.

---

# 18. Suggested first exercise

Before modifying the robot:

### 1. Load Bittle X

Check that the model appears correctly.

### 2. Print all joints

Identify which joint corresponds to each leg.

### 3. Move one joint

Try a target of approximately:

```python
math.radians(20)
```

### 4. Read its joint state

Use:

```python
p.getJointState()
```

### 5. Create one pose

Move several joints together.

### 6. Let physics run

Observe:

- balance,
- collisions,
- contact with the ground.

Once you understand these steps, you are ready to start modifying the robot.

---

# 19. PyBullet documentation

Useful resources:

PyBullet repository  
https://github.com/bulletphysics/bullet3

PyBullet Quickstart Guide  
https://pybullet.org/wordpress/

Petoi Bittle X  
https://www.petoi.com/products/petoi-robot-dog-bittle-x-voice-controlled

Petoi documentation  
https://docs.petoi.com/

Original Bittle URDF reference  
https://github.com/AIWintermuteAI/Bittle_URDF

---

# 20. Final reminder

The URDF is not the final product.

It is a **digital representation of your design**.

Use it to test questions such as:

> Can it move?

> Can it reach?

> Does it collide?

> Is it stable?

> Can it sense the environment?

> Can we control it?

Then validate your conclusions on the **physical Bittle X**.

## Bestandenlijst

```
LICENSE
README.md
meshes/obj/Cube.011.obj
meshes/obj/Plane.obj
meshes/obj/base_frame.001.obj
meshes/obj/base_frame.obj
meshes/obj/battery.001.obj
meshes/obj/battery.obj
meshes/obj/cover.001.obj
meshes/obj/cover.obj
meshes/obj/left_knee.001.obj
meshes/obj/left_knee.002.obj
meshes/obj/left_knee.003.obj
meshes/obj/left_knee.obj
meshes/obj/right_knee.001.obj
meshes/obj/right_knee.002.obj
meshes/obj/right_knee.003.obj
meshes/obj/right_knee.obj
meshes/obj/shoulder.001.obj
meshes/obj/shoulder.002.obj
meshes/obj/shoulder.003.obj
meshes/obj/shoulder.004.obj
meshes/obj/shoulder.005.obj
meshes/obj/shoulder.006.obj
meshes/obj/shoulder.007.obj
meshes/obj/shoulder.obj
urdf/bittle.urdf
```
