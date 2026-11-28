// The 3D robot: a URDF (stock Bittle or the crab legs) drawn with three.js, posed by joint angles in degrees.
// No physics: the body stays in place and is lowered so the lowest foot touches the floor. play() animates a plan of
// segments [[seconds, {joint: degrees}]] the way the firmware moves between frames, so the twin and the robot keep time.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const numbers = (text, fallback) => (text ? text.trim().split(/\s+/).map(Number) : fallback);
const colourOf = link => (/knee|cover|head|neck/.test(link) ? '#eab94f' : /shoulder/.test(link) ? '#38444f' : /board|imu/.test(link) ? '#355c43' : '#61707b');

function parseUrdf(text) {
  const doc = new DOMParser().parseFromString(text, 'application/xml');
  if (doc.querySelector('parsererror')) throw new Error('Het URDF-bestand is beschadigd');
  const links = [...doc.querySelectorAll('robot > link')].map(link => ({
    name: link.getAttribute('name'),
    visuals: [...link.querySelectorAll(':scope > visual')].map(visual => {
      const origin = visual.querySelector('origin');
      const geometry = visual.querySelector('geometry > *');
      return {
        xyz: numbers(origin?.getAttribute('xyz'), [0, 0, 0]), rpy: numbers(origin?.getAttribute('rpy'), [0, 0, 0]),
        type: geometry?.tagName, filename: geometry?.getAttribute('filename'),
        scale: numbers(geometry?.getAttribute('scale'), [1, 1, 1]), size: numbers(geometry?.getAttribute('size'), [.01, .01, .01]),
        radius: Number(geometry?.getAttribute('radius') || .01), length: Number(geometry?.getAttribute('length') || .01),
      };
    }),
  }));
  const joints = [...doc.querySelectorAll('robot > joint')].map(joint => {
    const origin = joint.querySelector('origin'), limit = joint.querySelector('limit');
    return {
      name: joint.getAttribute('name'), type: joint.getAttribute('type'),
      parent: joint.querySelector('parent').getAttribute('link'), child: joint.querySelector('child').getAttribute('link'),
      xyz: numbers(origin?.getAttribute('xyz'), [0, 0, 0]), rpy: numbers(origin?.getAttribute('rpy'), [0, 0, 0]),
      axis: numbers(joint.querySelector('axis')?.getAttribute('xyz'), [1, 0, 0]),
      lower: limit ? THREE.MathUtils.radToDeg(Number(limit.getAttribute('lower'))) : -180,
      upper: limit ? THREE.MathUtils.radToDeg(Number(limit.getAttribute('upper'))) : 180,
    };
  });
  return { links, joints };
}

const meshes = new Map();
function parseMesh(url) {
  const extension = url.split('?')[0].split('.').pop().toLowerCase();
  if (extension === 'obj') return new OBJLoader().loadAsync(url);
  if (extension === 'stl') return new STLLoader().loadAsync(url).then(geometry => new THREE.Mesh(geometry));  // Bittle's head
  return Promise.reject(new Error(`De 3D-weergave kan geen .${extension}-bestanden tonen`));
}
function loadMesh(url) {
  if (!meshes.has(url)) meshes.set(url, parseMesh(url).catch(error => { meshes.delete(url); throw error; }));
  return meshes.get(url).then(object => object.clone(true));
}

async function makeVisual(visual, linkName, base) {
  let object;
  if (visual.type === 'mesh') {
    object = await loadMesh(new URL(visual.filename, base).href);
    object.scale.fromArray(visual.scale);
  } else if (visual.type === 'box') {
    object = new THREE.Mesh(new THREE.BoxGeometry(...visual.size));
  } else if (visual.type === 'cylinder') {
    const geometry = new THREE.CylinderGeometry(visual.radius, visual.radius, visual.length, 24);
    geometry.rotateX(Math.PI / 2);  // URDF cylinders stand along z
    object = new THREE.Mesh(geometry);
  } else if (visual.type === 'sphere') {
    object = new THREE.Mesh(new THREE.SphereGeometry(visual.radius, 24, 16));
  } else {
    return null;
  }
  const material = new THREE.MeshStandardMaterial({ color: colourOf(linkName), roughness: .5, metalness: .1 });
  object.traverse(child => { if (child.isMesh) { child.material = material; child.castShadow = true; } });
  object.position.fromArray(visual.xyz);
  object.rotation.set(visual.rpy[0], visual.rpy[1], visual.rpy[2], 'ZYX');  // URDF rpy: R = Rz(y) Ry(p) Rx(r)
  return object;
}

export function createTwin(container, overlay) {
  const say = (text, error = false) => { overlay.hidden = !text; overlay.textContent = text || ''; overlay.classList.toggle('error', error); };
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch {
    say('De 3D-weergave heeft WebGL nodig, en die start niet in deze browser.', true);
  }
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#111c26');
  const camera = new THREE.PerspectiveCamera(38, 1, .01, 50);
  camera.up.set(0, 0, 1);
  camera.position.set(.3, -.28, .2);
  scene.add(new THREE.HemisphereLight('#dfe9f3', '#2a3540', 1.1));
  const sun = new THREE.DirectionalLight('#ffffff', 1.6);
  sun.position.set(1, -1.5, 2.5);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -.5, right: .5, top: .5, bottom: -.5, near: .1, far: 6 });
  scene.add(sun);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(1.2, 48), new THREE.MeshStandardMaterial({ color: '#1e2c38', roughness: 1 }));
  floor.receiveShadow = true;
  scene.add(floor);
  const grid = new THREE.GridHelper(2.4, 24, '#36506a', '#26394b');
  grid.rotation.x = Math.PI / 2;  // GridHelper lies in xz; the URDF world is z-up
  grid.position.z = .0005;
  scene.add(grid);
  const arrow = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, .17, .001), .08, '#7cc4fa', .03, .02);
  scene.add(arrow);  // the robot's forward direction (+y in the Bittle URDF)

  let controls = null;
  if (renderer) {
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    container.prepend(renderer.domElement);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, .06);
    controls.enableDamping = true;
    controls.addEventListener('change', () => { dirty = true; });
  }

  let robot = null, joints = {}, pose = {}, dirty = true, animation = null;
  const box = new THREE.Box3();

  function resize() {
    if (!renderer) return;
    const { clientWidth: width, clientHeight: height } = container;
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    dirty = true;
  }
  new ResizeObserver(resize).observe(container);

  // Playing runs on its own timer: animation frames stop in a hidden tab, and the real robot must keep moving.
  let ticking = 0;
  function tick() {
    ticking = 0;
    if (!animation) return;
    step(performance.now());
    if (animation) ticking = setTimeout(tick, 16);
  }

  function frame() {
    requestAnimationFrame(frame);
    controls?.update();
    if (dirty && renderer) {
      renderer.render(scene, camera);
      dirty = false;
    }
  }
  requestAnimationFrame(frame);

  function apply() {
    for (const [name, joint] of Object.entries(joints)) {
      const value = THREE.MathUtils.degToRad(pose[name] ?? 0);
      joint.motion.quaternion.setFromAxisAngle(joint.axis, value);
    }
    if (robot) {
      robot.position.z = 0;
      robot.updateMatrixWorld(true);
      box.setFromObject(robot);
      if (Number.isFinite(box.min.z)) robot.position.z = -box.min.z;  // stand on the floor
    }
    dirty = true;
  }

  async function load(url) {
    stop();
    say('3D-model laden…');
    const response = await fetch(url);
    if (!response.ok) throw new Error('3D-model niet gevonden: ' + url);
    const { links, joints: jointList } = parseUrdf(await response.text());
    const base = new URL(url, location.href);
    const groups = {};
    for (const link of links) {
      const group = new THREE.Group();
      group.name = link.name;
      for (const visual of link.visuals) {
        const object = await makeVisual(visual, link.name, base);
        if (object) group.add(object);
      }
      groups[link.name] = group;
    }
    const children = new Set(jointList.map(joint => joint.child));
    const root = new THREE.Group();
    for (const link of links) if (!children.has(link.name)) root.add(groups[link.name]);
    const found = {};
    for (const joint of jointList) {
      const holder = new THREE.Group();
      holder.position.fromArray(joint.xyz);
      holder.rotation.set(joint.rpy[0], joint.rpy[1], joint.rpy[2], 'ZYX');
      const motion = new THREE.Group();
      holder.add(motion);
      motion.add(groups[joint.child]);
      groups[joint.parent].add(holder);
      if (joint.type === 'revolute' || joint.type === 'continuous') {
        found[joint.name] = { motion, axis: new THREE.Vector3(...joint.axis).normalize(), lower: joint.lower, upper: joint.upper };
      }
    }
    if (robot) scene.remove(robot);
    robot = root;
    joints = found;
    scene.add(robot);
    pose = Object.fromEntries(Object.keys(joints).map(name => [name, clamp(name, pose[name] ?? 0)]));
    apply();
    say('');
    return { joints: Object.entries(joints).map(([name, j]) => ({ name, lower: j.lower, upper: j.upper })) };
  }

  const clamp = (name, value) => (joints[name] ? Math.min(joints[name].upper, Math.max(joints[name].lower, value)) : value);

  function setPose(values) {
    for (const [name, value] of Object.entries(values)) {
      if (name in joints && Number.isFinite(value)) pose[name] = clamp(name, value);
    }
    apply();
  }

  // Plans: ease from the current pose into each segment's pose, like the firmware and the Studio do.
  function play(plan, { onPose, onEnd } = {}) {
    stop();
    if (!plan?.segments?.length) return;
    animation = { plan, index: 0, from: { ...pose }, started: performance.now(), onPose, onEnd };
    if (!ticking) ticking = setTimeout(tick, 0);
  }

  function step(now) {
    const a = animation;
    const [seconds, target] = a.plan.segments[a.index];
    const t = seconds > 0 ? Math.min(1, (now - a.started) / 1000 / seconds) : 1;
    const k = a.plan.ease ? (1 - Math.cos(Math.PI * t)) / 2 : t;
    const values = {};
    for (const [name, value] of Object.entries(target)) {
      const start = a.from[name] ?? pose[name] ?? 0;
      values[name] = start + (value - start) * k;
    }
    setPose(values);
    a.onPose?.({ ...pose });
    if (t < 1) return;
    a.from = { ...pose };
    a.started = now;
    a.index++;
    if (a.index >= a.plan.segments.length) {
      if (a.plan.loop_from === null || a.plan.loop_from === undefined) {
        animation = null;
        a.onEnd?.();
        return;
      }
      a.index = a.plan.loop_from;
    }
  }

  function stop() {
    if (!animation) return;
    const ended = animation.onEnd;
    animation = null;
    ended?.(true);
  }

  // The surroundings (environment.js) live in the same scene; the view can step back to see them.
  const near = { position: camera.position.clone(), target: new THREE.Vector3(0, 0, .06) };
  function lookAround(wide) {
    if (!controls) return;
    if (wide) {
      camera.position.set(.9, -1.6, 1.3);
      controls.target.set(0, .2, .05);
    } else {
      camera.position.copy(near.position);
      controls.target.copy(near.target);
    }
    controls.update();
    dirty = true;
  }

  return {
    load, setPose, stop, play, resize, lookAround,
    add(object) { scene.add(object); dirty = true; },
    invalidate() { dirty = true; },
    pose: () => ({ ...pose }),
    limits: () => Object.fromEntries(Object.entries(joints).map(([name, j]) => [name, [j.lower, j.upper]])),
    get playing() { return !!animation; },
  };
}
