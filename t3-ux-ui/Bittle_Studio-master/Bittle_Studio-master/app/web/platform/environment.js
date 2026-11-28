// The surroundings in 3D around the twin: every scan photo stands where the camera saw it, at the depth the distance
// sensor measured. Each photo becomes a grid of points: a point of the picture lies along its own viewing ray, as
// deep as the depth grid says there (one cell for the SRF05: a flat wall; 8 x 8 for a ToF sensor later: a shaped
// surface), and where that ray reaches the floor first, the point lies on the floor. So the bottom of a photo
// (which shows the ground) folds onto the floor and the rest stands up as a wall.
//
// Neighbouring photos of a scan overlap; each one shows only its own slice (halfway to the photos either side), so the
// slices join into one ring round the robot. The robot stays at the centre of the 3D view facing +y: the map is turned
// and moved so that its robot pose (plus what the body turned during a running scan) lands there.
import * as THREE from 'three';

const SEGMENTS = 12;           // grid of a photo surface: enough to bend it onto the floor smoothly
const UNKNOWN_DEPTH = 2.;      // metres, for photos without a measurement while the scan has none at all
const FLOOR = .002;            // just above the 3D floor disc
const radians = THREE.MathUtils.degToRad;

/** depth grid (rows x columns over the picture) at picture fractions (0-1 across, 0-1 down) */
function sample(grid, across, down) {
  const rows = grid.length, columns = grid[0].length;
  const cell = (fraction, count) => Math.max(0, Math.min(count - 1, Math.floor(fraction * count)));
  return grid[cell(down, rows)][cell(across, columns)];
}

export function createEnvironment(twin) {
  const group = new THREE.Group();
  group.name = 'surroundings';
  twin.add(group);
  const loader = new THREE.TextureLoader();
  const textures = new Map();   // url -> texture, kept while the photo is shown
  let scans = [], pose = null, bodyTurn = 0, shown = true;

  function texture(url) {
    if (!textures.has(url)) {
      const loaded = loader.load(url, () => twin.invalidate());
      loaded.colorSpace = THREE.SRGBColorSpace;
      textures.set(url, loaded);
    }
    return textures.get(url);
  }

  // Map (x east, y north, headings counter-clockwise from east) to the 3D view (robot at 0, facing +y, z up).
  function toView() {
    const turn = radians(90 - (pose.heading + bodyTurn)), c = Math.cos(turn), s = Math.sin(turn);
    return {
      point: (x, y) => [(x - pose.x) * c - (y - pose.y) * s, (x - pose.x) * s + (y - pose.y) * c],
      angle: heading => heading + 90 - (pose.heading + bodyTurn),
    };
  }

  // The part of the turn round the camera that each photo shows: halfway to its neighbours (plus a little overlap).
  function slices(views) {
    const order = views.map((v, i) => [((v.heading % 360) + 360) % 360, i]).sort((a, b) => a[0] - b[0]);
    const result = new Array(views.length);
    order.forEach(([heading, index], k) => {
      const half = views[index].hfov / 2;
      if (order.length === 1) return void (result[index] = [half, half]);
      const next = order[(k + 1) % order.length][0], previous = order[(k - 1 + order.length) % order.length][0];
      const left = (((next - heading) % 360) + 360) % 360 / 2 + 1, right = (((heading - previous) % 360) + 360) % 360 / 2 + 1;
      result[index] = [Math.min(half, left), Math.min(half, right)];
    });
    return result;
  }

  function surface(scan, step, view, slice, fallback, map) {
    const [width, height] = view.size;
    const f = width / 2 / Math.tan(radians(view.hfov) / 2), cx = (width - 1) / 2, cy = (height - 1) / 2;
    const [left, right] = slice;
    const uLeft = Math.max(0, cx - f * Math.tan(radians(left))), uRight = Math.min(width - 1, cx + f * Math.tan(radians(right)));
    const heading = radians(map.angle(view.heading)), tilt = radians(view.tilt);
    const forward = new THREE.Vector3(Math.cos(tilt) * Math.cos(heading), Math.cos(tilt) * Math.sin(heading), -Math.sin(tilt));
    const leftAxis = new THREE.Vector3(-Math.sin(heading), Math.cos(heading), 0);
    const upAxis = new THREE.Vector3().crossVectors(forward, leftAxis);
    const [x, y] = map.point(view.x, view.y);
    const eye = new THREE.Vector3(x, y, view.z);
    const known = !!view.depth;
    const positions = [], uvs = [], index = [];
    for (let j = 0; j <= SEGMENTS; j++) {
      const v = (height - 1) * j / SEGMENTS;
      for (let i = 0; i <= SEGMENTS; i++) {
        const u = uLeft + (uRight - uLeft) * i / SEGMENTS;
        const depth = known ? sample(view.depth, u / width, v / height) : fallback;
        // The pinhole ray through (u, v), scaled so that it reaches `depth` along the view direction.
        const ray = forward.clone().addScaledVector(leftAxis, (cx - u) / f).addScaledVector(upAxis, (cy - v) / f);
        let point = eye.clone().addScaledVector(ray, depth);
        if (point.z < FLOOR && ray.z < 0) point = eye.clone().addScaledVector(ray, (eye.z - FLOOR) / -ray.z);
        positions.push(point.x, point.y, point.z);
        uvs.push(u / (width - 1), 1 - v / (height - 1));
      }
    }
    for (let j = 0; j < SEGMENTS; j++) {
      for (let i = 0; i < SEGMENTS; i++) {
        const a = j * (SEGMENTS + 1) + i, b = a + 1, c = a + SEGMENTS + 1, d = c + 1;
        index.push(a, c, b, b, c, d);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(index);
    const material = new THREE.MeshBasicMaterial({
      map: texture(`/api/scans/${scan.id}/files/${step.frame}`), side: THREE.DoubleSide,
      transparent: !known, opacity: known ? 1 : .55, depthWrite: known,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = known ? 0 : 1;
    return mesh;
  }

  function marker(map, object) {
    const [x, y] = map.point(object.x, object.y);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(.035, 16, 12), new THREE.MeshBasicMaterial({ color: '#f2a65a' }));
    ball.position.set(x, y, .05);
    return ball;
  }

  function build() {
    for (const child of [...group.children]) {
      group.remove(child);
      child.geometry?.dispose();
      child.material?.dispose();
    }
    const used = new Set();
    if (shown && pose) {
      const map = toView();
      for (const scan of scans) {
        const steps = scan.steps.filter(step => step.view);
        if (!steps.length) continue;
        const measured = steps.flatMap(step => (step.view.depth ? [step.view.depth[0][0]] : [])).sort((a, b) => a - b);
        const fallback = measured.length ? measured[Math.floor(measured.length / 2)] : UNKNOWN_DEPTH;
        const parts = slices(steps.map(step => step.view));
        steps.forEach((step, k) => {
          group.add(surface(scan, step, step.view, parts[k], fallback, map));
          used.add(`/api/scans/${scan.id}/files/${step.frame}`);
        });
        for (const object of scan.objects || []) group.add(marker(map, object));
      }
    }
    for (const [url, loaded] of textures) {
      if (!used.has(url)) {
        loaded.dispose();
        textures.delete(url);
      }
    }
    twin.invalidate();
  }

  return {
    /** The scans to show, and where the robot stands on their map ({x, y, heading}). */
    set(nextScans, robotPose, turned = 0) {
      scans = nextScans || [];
      pose = robotPose || null;
      bodyTurn = turned;
      build();
    },
    show(on) {
      shown = on;
      build();
    },
    get count() { return group.children.length; },
  };
}
