// The 3D view: terrain, coop, dock and robot drawn from the server's model and state. Z is up, as in the Studio.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { h, toast } from './ui.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const COLOR = {
  ground: new THREE.Color('#5f7a3f'), earth: new THREE.Color('#6e5b3a'), mud: new THREE.Color('#3c2a1b'),
  rayHit: new THREE.Color('#8fe08f'), rayMiss: new THREE.Color('#6d7882'), camera: new THREE.Color('#ffb454'),
  accent: new THREE.Color('#c0e581'), dock: new THREE.Color('#5ec2ff'),
  route: new THREE.Color('#f2d45c'), fox: new THREE.Color('#ff9a3c'), person: new THREE.Color('#5ea8ff'),
  alarm: new THREE.Color('#ff5a4f'), unseen: new THREE.Color('#7a8791'),
};
const RAY_HIT = COLOR.rayHit.toArray();
const RAY_MISS = COLOR.rayMiss.toArray();
const CAMERA_LINE = COLOR.camera.toArray();
const FRUSTUM_LENGTH = .5;   // metres drawn for the camera view cone
const FRUSTUM_MAX_HALF = .6; // a very wide lens would otherwise draw a huge cone
const PLATE_TOP = .008;      // metres above the dock position: the dock plate is 6 mm thick
const GROUND_STEP = .1;      // metres between the points of a line that follows the terrain
const PICK_DRAG = 5;         // pixels the pointer may move between press and release for the release to count as a click
const LIGHT = {
  day: { background: '#1f2b34', sky: 0xdbeaff, ground: 0x5b6650, sun: 0xfff0dc },
  night: { background: '#070b14', sky: 0x7088c4, ground: 0x151b2a, sun: 0x9fb4e8 },
};
const IR_INTENSITY = 1.6;    // candela of the infrared light; falls off as 1/distance and ends at the infrared range
const IR_BACK = .12;         // metres the light sits behind the camera, so the robot's own head is not blown out

const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const smooth = (value, low, high) => { const t = clamp((value - low) / (high - low), 0, 1); return t * t * (3 - 2 * t); };

// Terrain

function terrainColors({ rows: nx, cols: ny, resolution, origin, heights, materials }) {
  const colors = new Float32Array(nx * ny * 3);
  let sum = 0, sumSquares = 0;
  for (const h of heights) { sum += h; sumSquares += h * h; }
  const mean = sum / heights.length;
  const spread = Math.max(Math.sqrt(Math.max(sumSquares / heights.length - mean * mean, 0)), .004);
  const color = new THREE.Color();
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const k = i + j * nx;
      let mud = 0, count = 0;  // share of mud around the sample gives the patch a soft edge
      for (let dj = -1; dj <= 1; dj++) {
        for (let di = -1; di <= 1; di++) {
          const ii = i + di, jj = j + dj;
          if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue;
          count++;
          if (materials[ii + jj * nx] > 0) mud++;
        }
      }
      const x = origin[0] + i * resolution, y = origin[1] + j * resolution;
      const wet = smooth(mud / count, .2, .8);
      const patches = .5 + .5 * Math.sin(x * 1.9 + 1) * Math.sin(y * 1.4);  // slow green-brown variation
      color.copy(COLOR.ground).lerp(COLOR.earth, patches * .45).lerp(COLOR.mud, wet);
      color.multiplyScalar(1 + clamp((heights[k] - mean) / spread, -2, 2) * (wet > .5 ? .05 : .09));
      color.toArray(colors, k * 3);
    }
  }
  return colors;
}

function terrainMesh(terrain) {
  const { rows: nx, cols: ny, resolution, origin, heights } = terrain;
  if (heights.length !== nx * ny) throw new Error('The terrain data does not match its size');
  const positions = new Float32Array(nx * ny * 3);
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const k = i + j * nx;
      positions.set([origin[0] + i * resolution, origin[1] + j * resolution, heights[k]], k * 3);
    }
  }
  const index = new Uint32Array((nx - 1) * (ny - 1) * 6);
  let t = 0;
  for (let j = 0; j < ny - 1; j++) {
    for (let i = 0; i < nx - 1; i++) {
      const a = i + j * nx, b = a + 1, c = a + nx, d = c + 1;
      index.set([a, b, d, a, d, c], t);
      t += 6;
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(terrainColors(terrain), 3));
  geometry.setIndex(new THREE.BufferAttribute(index, 1));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .95, metalness: 0 }));
  mesh.receiveShadow = true;
  return mesh;
}

/** Height of the terrain surface, interpolated like the server does. */
function heightAt(terrain, x, y) {
  const { rows: nx, cols: ny, resolution, origin, heights } = terrain;
  const fx = clamp((x - origin[0]) / resolution, 0, nx - 1), fy = clamp((y - origin[1]) / resolution, 0, ny - 1);
  const i = Math.min(Math.floor(fx), nx - 2), j = Math.min(Math.floor(fy), ny - 2);
  const u = fx - i, v = fy - j;
  const h = (a, b) => heights[a + b * nx];
  return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v;
}

/** Where a ray first meets the terrain (a Vector3), or null when it misses: marched in small steps, then refined by bisection. */
function intersectTerrain(terrain, ray) {
  const { rows: nx, cols: ny, resolution, origin } = terrain;
  const { origin: from, direction } = ray;
  if (direction.z > -1e-6) return null;  // looking level or upward: there is no ground ahead
  const x1 = origin[0] + (nx - 1) * resolution, y1 = origin[1] + (ny - 1) * resolution;
  const below = t => {
    const x = from.x + direction.x * t, y = from.y + direction.y * t, z = from.z + direction.z * t;
    return x >= origin[0] && x <= x1 && y >= origin[1] && y <= y1 && z <= heightAt(terrain, x, y);
  };
  const step = Math.max(resolution / 2, .01), end = Math.min((from.z + 1) / -direction.z, 500);  // 1 m under the datum is below any ground
  let near = 0, far = -1;
  for (let t = step; t <= end; t += step) {
    if (below(t)) { far = t; break; }
    near = t;
  }
  if (far < 0) return null;
  for (let i = 0; i < 20; i++) {
    const middle = (near + far) / 2;
    if (below(middle)) far = middle; else near = middle;
  }
  return from.clone().addScaledVector(direction, far);
}

// Coop boxes, dock and start markers

function boxMesh(box) {
  const solid = box.kind !== 'fence';  // drawn see-through so the robot inside stays visible; the physics treats it as solid
  const material = new THREE.MeshStandardMaterial({
    color: box.color, roughness: .8, transparent: !solid, opacity: solid ? 1 : .45, depthWrite: solid,
  });
  if (box.kind === 'dock' || box.kind === 'dock-stop') {
    material.emissive = new THREE.Color(box.color);
    material.emissiveIntensity = .55;
  }
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...box.size), material);
  mesh.position.fromArray(box.position);
  mesh.quaternion.fromArray(box.quaternion);
  mesh.castShadow = solid;
  mesh.receiveShadow = true;
  return mesh;
}

function line(points, color, opacity = 1, closed = true) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity });
  return closed ? new THREE.LineLoop(geometry, material) : new THREE.Line(geometry, material);
}

const circle = (radius, steps = 64) => Array.from({ length: steps }, (_, n) => {
  const angle = n / steps * 2 * Math.PI;
  return new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0);
});

const translucent = (color, opacity) => new THREE.MeshBasicMaterial({
  color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2,
});

/** Capture zone of the dock: heading arrow, the 3 cm capture circle, the heading-tolerance wedge and a findable ring. */
function dockMarker(dock) {
  const group = new THREE.Group();
  group.position.set(dock.position[0], dock.position[1], dock.position[2] + PLATE_TOP);
  group.rotation.z = THREE.MathUtils.degToRad(dock.yaw);  // local +x is the heading of the docked robot
  const half = THREE.MathUtils.degToRad(dock.capture_angle);
  const wedge = new THREE.Shape();
  wedge.moveTo(0, 0);
  wedge.absarc(0, 0, .15, -half, half, false);
  wedge.lineTo(0, 0);
  group.add(new THREE.Mesh(new THREE.ShapeGeometry(wedge), translucent(COLOR.dock, .3)));
  group.add(line(wedge.getPoints(24).map(p => new THREE.Vector3(p.x, p.y, 0)), COLOR.dock, .9));
  group.add(new THREE.Mesh(new THREE.CircleGeometry(dock.capture_distance, 48), translucent(COLOR.accent, .55)));
  group.add(line(circle(dock.capture_distance, 48), COLOR.accent));
  group.add(line(circle(.3), COLOR.dock, .4));
  group.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), .3, COLOR.dock.getHex(), .07, .04));
  return group;
}

function startMarker(start, terrain) {
  const [x, y] = start.position;
  const group = new THREE.Group();
  group.position.set(x, y, heightAt(terrain, x, y) + .006);
  group.rotation.z = THREE.MathUtils.degToRad(start.heading);
  group.add(new THREE.Mesh(new THREE.CircleGeometry(.1, 40), translucent(COLOR.accent, .22)));
  group.add(line(circle(.1, 40), COLOR.accent));
  group.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), .25, COLOR.accent.getHex(), .07, .045));
  return group;
}

// Patrol route, visitor paths, actors, coverage points and the behaviour's markers

const ACTOR_SHAPES = {
  box: part => new THREE.BoxGeometry(...part.size),
  sphere: part => new THREE.SphereGeometry(part.radius, 16, 12),
  cylinder: part => new THREE.CylinderGeometry(part.radius, part.radius, part.length, 16).rotateX(Math.PI / 2),  // Bullet's cylinders stand along z
};
const PATH_COLOR = { fox: COLOR.fox, person: COLOR.person };

/** Points along a polyline [[x, y], ...], at most GROUND_STEP apart and `lift` metres above the terrain; closed also draws the way back. */
function groundLine(path, terrain, lift, closed = false) {
  const points = [];
  const at = (x, y) => new THREE.Vector3(x, y, heightAt(terrain, x, y) + lift);
  const edges = closed ? path.length : path.length - 1;
  for (let i = 0; i < edges; i++) {
    const [x0, y0] = path[i], [x1, y1] = path[(i + 1) % path.length];
    const steps = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / GROUND_STEP));
    for (let k = 0; k < steps; k++) points.push(at(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps));
  }
  if (!closed) points.push(at(path[path.length - 1][0], path[path.length - 1][1]));
  return points;
}

function dashedLine(points, color) {
  const object = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineDashedMaterial({ color, dashSize: .1, gapSize: .06 }));
  object.computeLineDistances();
  return object;
}

const bead = (radius, color) => new THREE.Mesh(new THREE.SphereGeometry(radius, 14, 10), new THREE.MeshBasicMaterial({ color }));

/** A round badge with a number, always drawn on top, for the patrol waypoints. */
function labelSprite(text, color) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  const g = canvas.getContext('2d');
  g.fillStyle = 'rgba(17, 24, 32, .85)';
  g.beginPath();
  g.arc(32, 32, 28, 0, 2 * Math.PI);
  g.fill();
  g.lineWidth = 4;
  g.strokeStyle = color;
  g.stroke();
  g.fillStyle = color;
  g.font = '600 30px sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(String(text), 32, 34);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true, toneMapped: false }));
  sprite.scale.set(.2, .2, 1);
  sprite.renderOrder = 6;
  return sprite;
}

/** The closed patrol loop 2 cm above the ground, a marker and number per waypoint; the first one is green and larger. */
function routeObjects(route, terrain) {
  const group = new THREE.Group();
  group.add(line(groundLine(route, terrain, .02, true), COLOR.route, .9));
  route.forEach(([x, y], n) => {
    const first = n === 0, ground = heightAt(terrain, x, y);
    const marker = bead(first ? .06 : .04, first ? COLOR.rayHit : COLOR.route);
    marker.position.set(x, y, ground + .03);
    const label = labelSprite(n + 1, (first ? COLOR.rayHit : COLOR.route).getStyle());
    label.position.set(x, y, ground + .17);
    group.add(marker, label);
  });
  return group;
}

/** A visitor's path as a dashed line a few centimetres above the ground, with a marker where the visitor appears. */
function visitorPath(path, terrain) {
  const color = PATH_COLOR[path.kind] || COLOR.accent;
  const group = new THREE.Group();
  group.add(dashedLine(groundLine(path.points, terrain, .03), color));
  const [x, y] = path.points[0];
  const start = bead(.05, color);
  start.position.set(x, y, heightAt(terrain, x, y) + .05);
  group.add(start);
  return group;
}

/** One chicken, fox or person: its parts (boxes, balls, cylinders) around the actor's origin on the ground. */
function actorFigure(actor) {
  const group = new THREE.Group();
  for (const part of actor.parts) {
    const make = ACTOR_SHAPES[part.shape];
    if (!make) continue;
    const mesh = new THREE.Mesh(make(part), new THREE.MeshStandardMaterial({ color: part.color, roughness: .85, metalness: 0 }));
    mesh.position.fromArray(part.position);
    mesh.quaternion.fromArray(part.quaternion);
    mesh.castShadow = mesh.receiveShadow = true;
    group.add(mesh);
  }
  group.visible = false;  // the first state shows it, if it is present
  return group;
}

/** The fence coverage points as dots; paintCoverage colours the ones the camera has seen this lap. */
function coverageDots(points) {
  const positions = new Float32Array(points.length * 3), colors = new Float32Array(points.length * 3);
  points.forEach((point, n) => positions.set([point[0], point[1], point[2] || 0], n * 3));
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3).setUsage(THREE.DynamicDrawUsage));
  const dots = new THREE.Points(geometry, new THREE.PointsMaterial({ size: .06, vertexColors: true, sizeAttenuation: true }));
  dots.frustumCulled = false;
  return dots;
}

/** Where the behaviour thinks the fox is: a red disc on the ground with a cone pointing down at it. */
function foxEstimateMarker() {
  const group = new THREE.Group();
  group.add(new THREE.Mesh(new THREE.CircleGeometry(.15, 32), translucent(COLOR.alarm, .3)));
  group.add(line(circle(.15, 32), COLOR.alarm));
  const cone = new THREE.Mesh(new THREE.ConeGeometry(.045, .13, 14).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: COLOR.alarm }));
  cone.position.z = .22;
  group.add(cone);
  return group;
}

/** The point in front of the dock that the robot steers to before it drives in: a diamond over a ring. */
function approachPoint() {
  const group = new THREE.Group();
  const diamond = new THREE.Mesh(new THREE.OctahedronGeometry(.04), new THREE.MeshBasicMaterial({ color: COLOR.dock }));
  diamond.position.z = .08;
  group.add(diamond, line(circle(.08, 32), COLOR.dock));
  return group;
}

/** Remove everything from a group and free its geometry, materials and label textures. */
function emptyGroup(group) {
  for (const child of [...group.children]) {
    group.remove(child);
    child.traverse(node => {
      if (node.geometry) node.geometry.dispose();
      for (const material of [].concat(node.material || [])) {
        if (material.map) material.map.dispose();
        material.dispose();
      }
    });
  }
}

// Dynamic line batches for sensor overlays: one geometry, refilled after every state.

function lineBatch(capacity) {
  const positions = new Float32Array(capacity * 3), colors = new Float32Array(capacity * 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3).setUsage(THREE.DynamicDrawUsage));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3).setUsage(THREE.DynamicDrawUsage));
  geometry.setDrawRange(0, 0);
  const object = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ vertexColors: true }));
  object.frustumCulled = false;
  let used = 0;
  return {
    object,
    clear() { used = 0; },
    add(a, b, color) {
      if (used + 2 > capacity) return;
      positions.set(a, used * 3);
      positions.set(b, used * 3 + 3);
      colors.set(color, used * 3);
      colors.set(color, used * 3 + 3);
      used += 2;
    },
    commit() {
      geometry.setDrawRange(0, used);
      geometry.attributes.position.needsUpdate = true;
      geometry.attributes.color.needsUpdate = true;
    },
  };
}

function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

const unit = v => { const n = Math.hypot(...v) || 1; return v.map(c => c / n); };

/** The view cone of a camera: apex plus the four corners of its far rectangle, turned with the camera's roll. */
function drawFrustum(batch, reading) {
  const origin = reading.pose.position, forward = unit(reading.pose.forward);
  const reference = reading.pose.up || (Math.abs(forward[2]) > .98 ? [1, 0, 0] : [0, 0, 1]);
  const right = unit(cross(forward, reference)), up = cross(right, forward);
  const tan = Math.tan(THREE.MathUtils.degToRad(reading.fov) / 2);
  const length = Math.min(FRUSTUM_LENGTH, FRUSTUM_MAX_HALF / tan);
  const halfHeight = length * tan, halfWidth = halfHeight * reading.width / reading.height;
  const corner = (sx, sy) => origin.map((o, n) => o + forward[n] * length + right[n] * halfWidth * sx + up[n] * halfHeight * sy);
  const corners = [corner(-1, 1), corner(1, 1), corner(1, -1), corner(-1, -1)];
  corners.forEach((c, n) => {
    batch.add(origin, c, CAMERA_LINE);
    batch.add(c, corners[(n + 1) % 4], CAMERA_LINE);
  });
}

// Robot meshes

const meshCache = new Map();

function parseMesh(url) {
  const extension = url.split('?')[0].split('.').pop().toLowerCase();
  if (extension === 'obj') return new OBJLoader().loadAsync(url);
  if (extension === 'stl') {
    return import('three/addons/loaders/STLLoader.js').then(async ({ STLLoader }) => new THREE.Mesh(await new STLLoader().loadAsync(url)));
  }
  if (extension === 'dae') {
    return import('three/addons/loaders/ColladaLoader.js').then(async ({ ColladaLoader }) => (await new ColladaLoader().loadAsync(url)).scene);
  }
  if (extension === 'glb' || extension === 'gltf') {
    return import('three/addons/loaders/GLTFLoader.js').then(async ({ GLTFLoader }) => (await new GLTFLoader().loadAsync(url)).scene);
  }
  return Promise.reject(new Error(`The 3D view cannot draw .${extension} meshes`));
}

async function loadMesh(url) {
  if (!meshCache.has(url)) {
    const promise = parseMesh(url);
    meshCache.set(url, promise);
    promise.catch(() => meshCache.delete(url));
  }
  return (await meshCache.get(url)).clone(true);  // clones share the parsed geometry
}

function materialize(object, color) {
  object.traverse(child => {
    if (!child.isMesh) return;
    child.material = new THREE.MeshStandardMaterial({ color, roughness: .42, metalness: .12 });
    child.castShadow = true;
    child.receiveShadow = true;
  });
}

function visualColor(visual) {
  if (visual.color) return new THREE.Color(visual.color[0], visual.color[1], visual.color[2]);
  const link = visual.link;
  return /knee|cover|head|neck/.test(link) ? '#eab94f' : /shoulder/.test(link) ? '#333d46' : /board|imu/.test(link) ? '#355c43' : '#5d6c76';
}

const numbers = text => String(text).trim().split(/\s+/).map(Number);

async function makeVisual(visual) {
  let object;
  if (visual.type === 'mesh') {
    object = await loadMesh(visual.url);
    object.scale.fromArray(visual.scale);
  } else if (visual.type === 'box') {
    object = new THREE.Mesh(new THREE.BoxGeometry(...numbers(visual.size)));
  } else if (visual.type === 'sphere') {
    object = new THREE.Mesh(new THREE.SphereGeometry(Number(visual.radius), 32, 24));
  } else if (visual.type === 'cylinder') {
    const geometry = new THREE.CylinderGeometry(Number(visual.radius), Number(visual.radius), Number(visual.length), 32);
    geometry.rotateX(Math.PI / 2);  // URDF cylinders stand along z
    object = new THREE.Mesh(geometry);
  } else {
    throw new Error('Unsupported URDF visual: ' + visual.type);
  }
  materialize(object, visualColor(visual));
  object.position.fromArray(visual.position);
  object.quaternion.fromArray(visual.quaternion);
  return object;
}

function disposeMaterials(object) {
  object.traverse(child => {
    if (child.isMesh) (Array.isArray(child.material) ? child.material : [child.material]).forEach(m => m && m.dispose());
  });
}

function disposeAll(object) {
  object.traverse(child => {
    if (child.geometry) child.geometry.dispose();
  });
  disposeMaterials(object);
}

const noop = () => {};
// Without WebGL nothing is drawn; pick() ends at once (after the caller has stored its stop function).
const STUB = {
  setModel: noop, update: noop, setOverlay: noop, setShadows: noop, setFollow: noop, topView: noop, resetView: noop,
  pick: (onPoint, hint, onEnd) => { if (onEnd) setTimeout(onEnd, 0); return noop; },
};

/** container: the element that gets the canvas; overlay: an element for "Loading…" and error messages. */
export function createViewport(container, overlay) {
  const notify = (text, isError = false) => {
    overlay.hidden = !text;
    overlay.textContent = text || '';
    overlay.classList.toggle('error', isError);
  };

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (error) {
    notify('The 3D view needs WebGL, which this browser could not start. The rest of the dashboard still works.', true);
    return STUB;
  }

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(LIGHT.day.background);
  const camera = new THREE.PerspectiveCamera(42, 1, .02, 300);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  container.prepend(renderer.domElement);
  const canvas = renderer.domElement;

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.minDistance = .15;
  controls.maxDistance = 80;
  controls.maxPolarAngle = Math.PI / 2 - .02;

  // The sun doubles as the moon at night (same shadow window, other colour and strength).
  const hemisphere = new THREE.HemisphereLight(LIGHT.day.sky, LIGHT.day.ground, 1.7);
  scene.add(hemisphere);
  const sun = new THREE.DirectionalLight(LIGHT.day.sun, 2.8);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -.0003;
  sun.shadow.normalBias = .002;
  scene.add(sun, sun.target);
  // The detector camera's infrared LEDs (night only) and the glow of the deterrent. Both stay in the scene and are
  // switched through their intensity: adding or hiding a light would recompile the shader of every material.
  const irLight = new THREE.SpotLight(0xeaf2ff, 0, 0, Math.PI / 6, .7, 1);
  const deterLight = new THREE.PointLight(0xff7a45, 0, 1.2, 2);
  scene.add(irLight, irLight.target, deterLight);

  const overlays = { rays: true, camera: true, heading: true, start: true, route: true, actors: true, paths: true, coverage: true, dock: true };
  const rays = lineBatch(4096), frusta = lineBatch(1024);
  const dotPositions = new Float32Array(64 * 3);
  const dotGeometry = new THREE.BufferGeometry();
  dotGeometry.setAttribute('position', new THREE.BufferAttribute(dotPositions, 3).setUsage(THREE.DynamicDrawUsage));
  dotGeometry.setDrawRange(0, 0);
  const dots = new THREE.Points(dotGeometry, new THREE.PointsMaterial({ color: COLOR.rayHit, size: 7, sizeAttenuation: false, depthTest: false }));
  dots.frustumCulled = false;
  dots.renderOrder = 4;
  const arrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), .3, COLOR.accent.getHex(), .09, .05);
  for (const part of [arrow.line, arrow.cone]) part.material.depthTest = false;
  arrow.renderOrder = 5;
  scene.add(rays.object, dots, frusta.object, arrow);

  // Layers that are emptied and refilled when the model changes, and the markers that move with the state.
  const routeLayer = new THREE.Group(), pathsLayer = new THREE.Group(), coverageLayer = new THREE.Group();
  const actorsLayer = new THREE.Group(), figures = new THREE.Group(), dockLayer = new THREE.Group(), dockZone = new THREE.Group();
  const foxMarker = foxEstimateMarker(), approachMarker = approachPoint();
  foxMarker.visible = false;
  actorsLayer.add(figures, foxMarker);
  dockLayer.add(dockZone, approachMarker);
  const deterRing = new THREE.Mesh(new THREE.RingGeometry(.88, 1, 48), new THREE.MeshBasicMaterial({
    color: COLOR.alarm, transparent: true, opacity: .6, depthWrite: false, side: THREE.DoubleSide,
  }));
  deterRing.visible = false;
  const pickLayer = new THREE.Group();
  const pickCursor = new THREE.Mesh(new THREE.RingGeometry(.03, .045, 32), new THREE.MeshBasicMaterial({ color: COLOR.rayHit, depthTest: false, side: THREE.DoubleSide }));
  pickCursor.visible = false;
  pickCursor.renderOrder = 7;
  scene.add(routeLayer, pathsLayer, coverageLayer, actorsLayer, dockLayer, deterRing, pickLayer, pickCursor);

  let model = null, latest = null, world = null, start = null, terrain = null, specs = {};
  let following = false, dirty = true;
  const robotRoot = new THREE.Group();
  scene.add(robotRoot);
  const robotLinks = new Map();
  const robotPosition = new THREE.Vector3();
  let robotSignature = '', robotToken = 0;
  const figureOf = new Map();  // actor id -> its group
  let coverage = null, coverageKey = null, approachKey = '';
  let night = false, irRange = 0, irCamera = null, deterring = false;

  const applyOverlays = () => {
    rays.object.visible = dots.visible = overlays.rays;
    frusta.object.visible = overlays.camera;
    arrow.visible = overlays.heading;
    if (start) start.visible = overlays.start;
    routeLayer.visible = overlays.route;
    pathsLayer.visible = overlays.paths;
    actorsLayer.visible = overlays.actors;
    coverageLayer.visible = overlays.coverage;
    dockLayer.visible = overlays.dock;
    dirty = true;
  };

  // Day and night

  /** Daylight, or a dark bluish night with a dim moon (strength from the moonlight setting) and the camera's infrared light. */
  function applyEnvironment(next) {
    const environment = next.scenario.environment || {};
    night = environment.time_of_day === 'night';
    const preset = night ? LIGHT.night : LIGHT.day;
    const moon = clamp(Number(environment.moonlight) || 0, 0, 1);
    scene.background.set(preset.background);
    hemisphere.color.set(preset.sky);
    hemisphere.groundColor.set(preset.ground);
    hemisphere.intensity = night ? .3 + 2.2 * moon : 1.7;
    sun.color.set(preset.sun);
    sun.intensity = night ? .25 + 3 * moon : 2.8;
    irRange = night && environment.ir_light ? Number(environment.ir_range) || 0 : 0;
    irLight.distance = irRange + IR_BACK;
    if (!irRange) irLight.intensity = 0;
    const cameras = next.sensors.filter(sensor => sensor.type === 'camera');
    const wanted = next.scenario.detector && next.scenario.detector.camera;
    irCamera = (cameras.find(sensor => sensor.id === wanted) || cameras[0] || {}).id || null;
    dirty = true;
  }

  /** The infrared light follows the detector camera; without a reading it is off. */
  function poseIr(sensors) {
    const reading = irRange > 0 && irCamera ? sensors[irCamera] : null;
    if (!reading || !reading.pose) {
      irLight.intensity = 0;
      return;
    }
    const { position, forward } = reading.pose;
    irLight.position.set(position[0] - forward[0] * IR_BACK, position[1] - forward[1] * IR_BACK, position[2] - forward[2] * IR_BACK);
    irLight.target.position.set(position[0] + forward[0], position[1] + forward[1], position[2] + forward[2]);
    irLight.angle = THREE.MathUtils.degToRad(clamp((reading.fov || 60) / 2 * 1.15, 5, 80));
    irLight.intensity = IR_INTENSITY;
  }

  // Scene building

  /** The area that matters (fenced run, dock, start, mud) with a margin, for the camera and the shadow window. */
  function framing() {
    const xs = [], ys = [];
    const add = (x, y) => { xs.push(x); ys.push(y); };
    model.world.run.corners.forEach(([x, y]) => add(x, y));
    add(model.world.dock.position[0], model.world.dock.position[1]);
    add(...model.scenario.robot.start.position);
    for (const m of model.scenario.mud) {
      add(m.center[0] - m.radius, m.center[1] - m.radius);
      add(m.center[0] + m.radius, m.center[1] + m.radius);
    }
    const margin = .5;
    const x0 = Math.min(...xs) - margin, x1 = Math.max(...xs) + margin, y0 = Math.min(...ys) - margin, y1 = Math.max(...ys) + margin;
    return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, width: x1 - x0, height: y1 - y0 };
  }

  function fitShadow() {
    const f = framing(), half = Math.max(f.width, f.height) / 2 * 1.25;
    sun.target.position.set(f.cx, f.cy, 0);
    sun.position.set(f.cx - half * .5, f.cy - half * .35, half * 1.4);
    Object.assign(sun.shadow.camera, { left: -half, right: half, top: half, bottom: -half, near: .1, far: half * 5 });
    sun.shadow.camera.updateProjectionMatrix();
  }

  function buildWorld(next) {
    if (world) {
      scene.remove(world);
      disposeAll(world);
    }
    world = new THREE.Group();
    const mesh = terrainMesh(next.world.terrain);
    const low = next.world.terrain.heights.reduce((a, b) => Math.min(a, b), 0);
    const base = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: '#161f1a', roughness: 1 }));
    base.position.set(0, 0, low - .03);
    world.add(mesh, base);
    for (const box of next.world.boxes) world.add(boxMesh(box));
    scene.add(world);
  }

  function buildStart(next) {
    if (start) {
      scene.remove(start);
      disposeAll(start);
    }
    start = startMarker(next.scenario.robot.start, next.world.terrain);
    start.visible = overlays.start;
    scene.add(start);
  }

  /** Route, visitor paths, actors, coverage points and the dock zone: all geometry, built once per model. */
  function buildScenery(next) {
    const actors = next.actors || { actors: [], paths: [] };
    emptyGroup(routeLayer);
    const route = next.scenario.patrol && next.scenario.patrol.route;
    if (route && route.length) routeLayer.add(routeObjects(route, terrain));
    emptyGroup(pathsLayer);
    for (const path of actors.paths) pathsLayer.add(visitorPath(path, terrain));
    emptyGroup(figures);
    figureOf.clear();
    for (const actor of actors.actors) {
      const figure = actorFigure(actor);
      figureOf.set(actor.id, figure);
      figures.add(figure);
    }
    emptyGroup(coverageLayer);
    coverageKey = null;  // paint the new dots even if the set of seen points is empty
    coverage = coverageDots(next.coverage_points || []);
    coverageLayer.add(coverage);
    emptyGroup(dockZone);
    dockZone.add(dockMarker(next.world.dock));
    approachKey = '';
    if (latest) {  // the new geometry takes over the pose of the latest state
      poseActors(latest.actors || []);
      paintCoverage(latest.coverage_seen || []);
      showBehaviour(latest.behaviour);
    }
  }

  async function buildRobot(visuals, label) {
    const signature = JSON.stringify(visuals);
    if (signature === robotSignature) return;
    robotSignature = signature;
    const token = ++robotToken;
    notify(`Loading ${label} model…`);
    let built;
    try {
      built = await Promise.all(visuals.map(async visual => ({ link: visual.link, object: await makeVisual(visual) })));
    } catch (error) {
      if (token === robotToken) {
        robotSignature = '';
        notify('Could not draw the robot: ' + error.message, true);
      }
      return;
    }
    if (token !== robotToken) {
      built.forEach(item => disposeMaterials(item.object));
      return;
    }
    for (const group of robotLinks.values()) {
      robotRoot.remove(group);
      disposeMaterials(group);
    }
    robotLinks.clear();
    for (const { link, object } of built) {
      if (!robotLinks.has(link)) {
        const group = new THREE.Group();
        robotRoot.add(group);
        robotLinks.set(link, group);
      }
      robotLinks.get(link).add(object);
    }
    notify(null);
    if (latest) poseRobot(latest.robot.transforms);
    dirty = true;
  }

  function poseRobot(transforms) {
    for (const [link, group] of robotLinks) {
      const pose = transforms[link];
      if (!pose) continue;
      group.position.fromArray(pose[0]);
      group.quaternion.fromArray(pose[1]);
    }
  }

  // Per-state updates: only poses and colours change here

  function poseActors(states) {
    for (const actor of states) {
      const figure = figureOf.get(actor.id);
      if (!figure) continue;
      figure.visible = actor.present;  // a visitor is hidden until it appears and after it has left
      if (!actor.present) continue;
      figure.position.fromArray(actor.position);
      figure.rotation.z = THREE.MathUtils.degToRad(actor.heading);
    }
  }

  /** Seen points green, the others grey; recoloured only when the set of seen points changed. */
  function paintCoverage(seen) {
    if (!coverage) return;
    const key = seen.join(',');
    if (key === coverageKey) return;
    coverageKey = key;
    const colors = coverage.geometry.attributes.color;
    for (let n = 0; n < colors.count; n++) colors.setXYZ(n, COLOR.unseen.r, COLOR.unseen.g, COLOR.unseen.b);
    for (const n of seen) if (n < colors.count) colors.setXYZ(n, COLOR.rayHit.r, COLOR.rayHit.g, COLOR.rayHit.b);
    colors.needsUpdate = true;
  }

  /** The dock's approach point, the fox estimate and the deterrent's glow from the behaviour reading. */
  function showBehaviour(behaviour) {
    if (!behaviour || !terrain) return;
    const approach = behaviour.approach;
    if (approach && `${approach[0]},${approach[1]}` !== approachKey) {
      approachKey = `${approach[0]},${approach[1]}`;
      approachMarker.position.set(approach[0], approach[1], heightAt(terrain, approach[0], approach[1]) + .01);
    }
    const estimate = behaviour.fox_estimate;
    foxMarker.visible = Boolean(estimate);
    if (estimate) foxMarker.position.set(estimate[0], estimate[1], heightAt(terrain, estimate[0], estimate[1]) + .01);
    const active = Boolean(behaviour.deterring);
    if (active !== deterring) {
      deterring = active;
      deterRing.visible = active;
      if (!active) deterLight.intensity = 0;
    }
  }

  /** The deterrent pulses about 1.5 times a second, around the robot. */
  function pulse(now) {
    const wave = .5 + .5 * Math.sin(now / 1000 * 2 * Math.PI * 1.5);
    deterRing.scale.setScalar(.14 + .12 * wave);
    deterRing.material.opacity = .85 - .5 * wave;
    deterLight.intensity = (night ? .35 : .2) * (.4 + .6 * wave);
  }

  // Views

  function resetView() {
    const f = framing();
    const target = new THREE.Vector3(f.cx, f.cy, 0);
    const distance = clamp(Math.hypot(f.width, f.height) / 2 * 2.2, 1, 80);
    camera.position.copy(target).addScaledVector(new THREE.Vector3(.45, -1, .8).normalize(), distance);
    controls.target.copy(target);
    controls.update();
    dirty = true;
  }

  function topView() {
    const f = framing();
    const target = following ? robotPosition.clone().setZ(0) : new THREE.Vector3(f.cx, f.cy, 0);
    const half = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    const distance = following ? 1.2 : Math.max(f.height, f.width / camera.aspect) / (2 * half) * 1.08;
    camera.position.set(target.x, target.y - distance * .002, distance);  // a hair south of straight above keeps north up
    controls.target.copy(target);
    controls.update();
    dirty = true;
  }

  // Sensor overlays

  function drawSensors(readings) {
    rays.clear();
    frusta.clear();
    let dotCount = 0;
    for (const [id, reading] of Object.entries(readings)) {
      if (reading.type === 'tof' && reading.origin && reading.rays) {
        const reach = specs[id] ? specs[id].range : Infinity;
        for (const end of reading.rays) {
          const length = Math.hypot(end[0] - reading.origin[0], end[1] - reading.origin[1], end[2] - reading.origin[2]);
          rays.add(reading.origin, end, length < reach - .003 ? RAY_HIT : RAY_MISS);
        }
        if (reading.hit && dotCount < 64) dotPositions.set(reading.hit.point, dotCount++ * 3);
      } else if (reading.type === 'camera' && reading.pose && reading.fov) {
        drawFrustum(frusta, reading);
      }
    }
    rays.commit();
    frusta.commit();
    dotGeometry.setDrawRange(0, dotCount);
    dotGeometry.attributes.position.needsUpdate = true;
  }

  // Pick mode: a click on the ground (press and release within PICK_DRAG pixels, so orbit drags still work) is reported

  const aim = new THREE.Raycaster(), ndc = new THREE.Vector2();
  const pickHint = h('div', { class: 'pick-hint', role: 'status', hidden: true });
  pickHint.style.cssText = 'position:absolute;left:50%;bottom:34px;transform:translateX(-50%);z-index:4;max-width:90%;text-align:center;'
    + 'background:#111820e6;border:1px solid var(--accent);color:var(--accent);border-radius:6px;padding:6px 12px;font-size:12px;pointer-events:none;';
  container.append(pickHint);
  let picking = null, pressed = null;

  /** The point of the terrain under the pointer, or null (over the sky, or beyond the edge of the terrain). */
  function groundAt(event) {
    if (!terrain) return null;
    const box = canvas.getBoundingClientRect();
    ndc.set((event.clientX - box.left) / box.width * 2 - 1, -(event.clientY - box.top) / box.height * 2 + 1);
    camera.updateMatrixWorld();
    aim.setFromCamera(ndc, camera);
    return intersectTerrain(terrain, aim.ray);
  }

  /** Markers and a line for the points clicked in the running pick, so the user sees them before they are applied anywhere. */
  function showPicked(points) {
    emptyGroup(pickLayer);
    for (const [x, y] of points) {
      const marker = bead(.03, COLOR.rayHit);
      marker.position.set(x, y, heightAt(terrain, x, y) + .03);
      pickLayer.add(marker);
    }
    if (points.length > 1) pickLayer.add(line(groundLine(points, terrain, .03), COLOR.rayHit, .9, false));
    dirty = true;
  }

  canvas.addEventListener('pointerdown', event => {
    pressed = picking && event.isPrimary && event.button === 0 ? { x: event.clientX, y: event.clientY } : null;
  });
  canvas.addEventListener('pointercancel', () => { pressed = null; });
  canvas.addEventListener('pointerup', event => {
    const down = pressed;
    pressed = null;
    if (!picking || !down || event.button !== 0 || Math.hypot(event.clientX - down.x, event.clientY - down.y) > PICK_DRAG) return;
    const point = groundAt(event);
    if (!point) return;
    const session = picking;
    session.points.push([point.x, point.y]);
    showPicked(session.points);
    try {
      session.onPoint([Math.round(point.x * 100) / 100, Math.round(point.y * 100) / 100]);
    } catch (error) {
      console.error(error);
    }
  });
  canvas.addEventListener('pointermove', event => {
    if (!picking || event.buttons) return;  // not while orbiting or panning
    const point = groundAt(event);
    pickCursor.visible = Boolean(point);
    if (point) {
      pickCursor.position.set(point.x, point.y, point.z + .01);
      pickCursor.scale.setScalar(Math.max(.6, camera.position.distanceTo(point) / 6));
    }
    dirty = true;
  });
  canvas.addEventListener('pointerleave', () => {
    pickCursor.visible = false;
    dirty = true;
  });

  /**
   * Pick points on the ground: onPoint([x, y]) gets every click in metres rounded to 0.01. `hint` is shown over the
   * view. Esc, the returned stop() or another pick() ends it; onEnd (optional) runs when it has ended, whatever the cause.
   */
  function startPick(onPoint, hint, onEnd) {
    if (picking) picking.stop();
    const session = { ended: false, points: [], onPoint };
    const onKey = event => { if (event.key === 'Escape') session.stop(); };
    session.stop = () => {
      if (session.ended) return;
      session.ended = true;
      if (picking === session) picking = null;
      document.removeEventListener('keydown', onKey);
      canvas.style.cursor = '';
      pickHint.hidden = true;
      pickCursor.visible = false;
      emptyGroup(pickLayer);
      dirty = true;
      if (onEnd) onEnd();
    };
    picking = session;
    document.addEventListener('keydown', onKey);
    canvas.style.cursor = 'crosshair';
    pickHint.textContent = hint || 'Click the ground to pick points · Esc to stop';
    pickHint.hidden = false;
    return session.stop;
  }

  // Render loop: draws only when something changed, so a paused simulation costs next to nothing.

  controls.addEventListener('change', () => { dirty = true; });
  new ResizeObserver(() => {
    const width = container.clientWidth, height = container.clientHeight;
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    dirty = true;
  }).observe(container);

  let last = performance.now();
  function frame(now) {
    requestAnimationFrame(frame);
    const dt = Math.min((now - last) / 1000, .1);
    last = now;
    if (following) {
      const step = robotPosition.clone().sub(controls.target).multiplyScalar(1 - Math.exp(-dt * 6));
      if (step.lengthSq() > 1e-10) {
        controls.target.add(step);
        camera.position.add(step);
        dirty = true;
      }
    }
    if (deterring) {  // the pulse needs a frame of its own, between two states
      pulse(now);
      dirty = true;
    }
    controls.update();
    if (dirty) {
      dirty = false;
      renderer.render(scene, camera);
    }
  }
  requestAnimationFrame(frame);

  return {
    setModel(next) {
      const first = !model;
      model = next;
      terrain = next.world.terrain;
      specs = Object.fromEntries(next.sensors.map(sensor => [sensor.id, sensor]));
      applyEnvironment(next);
      try {
        buildWorld(next);
        buildStart(next);
        fitShadow();
      } catch (error) {
        console.error(error);
        notify('Could not draw the scene: ' + error.message, true);
      }
      try {
        buildScenery(next);
      } catch (error) {
        console.error(error);
        toast('Could not draw the route, actors and coverage points: ' + error.message, true);
      }
      buildRobot(next.robot.visuals, /bittle/i.test(next.scenario.robot.model) ? 'Bittle' : 'robot');
      if (first) resetView();
      applyOverlays();
    },

    update(state) {
      latest = state;
      const robot = state.robot;
      poseRobot(robot.transforms);
      robotPosition.fromArray(robot.position);
      const heading = THREE.MathUtils.degToRad(robot.heading);
      const direction = new THREE.Vector3(Math.cos(heading), Math.sin(heading), 0);
      arrow.position.copy(robotPosition).addScaledVector(direction, .08).add(new THREE.Vector3(0, 0, .03));
      arrow.setDirection(direction);
      if (terrain) deterRing.position.set(robotPosition.x, robotPosition.y, heightAt(terrain, robotPosition.x, robotPosition.y) + .02);
      deterLight.position.set(robotPosition.x, robotPosition.y, robotPosition.z + .2);
      drawSensors(state.sensors);
      poseActors(state.actors || []);
      showBehaviour(state.behaviour);
      paintCoverage(state.coverage_seen || []);
      poseIr(state.sensors);
      dirty = true;
    },

    /** name: rays, camera, heading, start, route, actors (also the fox estimate), paths (visitors), coverage, dock (zone and approach point). */
    setOverlay(name, on) {
      overlays[name] = on;
      applyOverlays();
    },

    setShadows(on) {
      sun.castShadow = on;
      dirty = true;
    },

    setFollow(on) {
      following = on;
    },

    topView: () => model && topView(),
    resetView: () => model && resetView(),
    pick: startPick,
  };
}
