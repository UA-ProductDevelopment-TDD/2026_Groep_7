// The real robot: the Bluetooth/USB link of Bittle Link (OpenCat protocol), plus the motor layout that turns the
// 3D robot's joint angles into servo angles and back: servo = joint x direction + zero offset.
import { createLink } from '/web/bittle-link/link.js';

const SEND_EVERY_MS = 50;  // at most 20 poses a second: Bluetooth carries about that many 20-byte packets

export function createRobot() {
  const link = createLink();
  let layout = null;         // {joint: {servo, sign, offset}}
  let pending = null, sending = false, lastSent = 0, timer = 0;
  let mirror = false;        // true while the robot's real joint angles drive the 3D robot
  const listeners = { pose: [] };

  const toServo = (joint, angle) => {
    const entry = layout?.[joint];
    return entry ? Math.max(-125, Math.min(125, Math.round(angle * entry.sign + entry.offset))) : null;
  };
  const toJoint = (joint, servoAngle) => {
    const entry = layout[joint];
    return (servoAngle - entry.offset) / entry.sign;
  };

  /** Send a pose (joint degrees) as one binary I packet; poses that come faster than the link replace each other. */
  function sendPose(pose) {
    if (!link.connected || !layout) return;
    pending = pose;
    if (sending || timer) return;
    const wait = Math.max(0, lastSent + SEND_EVERY_MS - performance.now());
    timer = setTimeout(flush, wait);
  }

  async function flush() {
    timer = 0;
    if (!pending || !link.connected) return;
    const pose = pending;
    pending = null;
    const pairs = [];
    for (const [joint, angle] of Object.entries(pose)) {
      const servo = layout[joint]?.servo, value = toServo(joint, angle);
      if (servo !== undefined && value !== null) pairs.push(servo, value);
    }
    if (!pairs.length) return;
    sending = true;
    lastSent = performance.now();
    try {
      link.cancelStream();
      await link.sendPose(pairs.slice(0, 18), 'Platform');  // 9 joints fill one BLE packet
    } catch (error) {
      link.dispatchEvent(new CustomEvent('log', { detail: { kind: 'ERROR', message: error.message } }));
    } finally {
      sending = false;
      if (pending) sendPose(pending);
    }
  }

  // The robot reports its 16 servo angles after j (read positions): give them to whoever mirrors them.
  link.addEventListener('joints', ({ detail }) => {
    if (!layout) return;
    const pose = {};
    for (const joint of Object.keys(layout)) {
      const angle = detail.angles[layout[joint].servo];
      if (Number.isFinite(angle)) pose[joint] = toJoint(joint, angle);
    }
    for (const listener of listeners.pose) listener(pose, mirror);
  });

  return {
    link,
    get connected() { return link.connected; },
    setLayout(value) { layout = value; },
    get layout() { return layout; },
    toServo,
    sendPose,
    onPose(listener) { listeners.pose.push(listener); },
    async command(text) { await link.press(text, 'Platform'); },
    /** Read the legs once (servos go soft for a moment), or keep reading so the legs can be moved by hand. */
    async readOnce() { mirror = true; await link.press('fp', 'Poten lezen'); },
    async readLive() { mirror = true; await link.press('fP', 'Live meelezen'); },
    /** Stop reading: the servos switch on again and hold the pose the legs were moved to. */
    async stopReading() {
      mirror = false;
      if (link.connected) await link.press('#on', 'Live meelezen stoppen');
    },
    get mirroring() { return mirror; },
  };
}
