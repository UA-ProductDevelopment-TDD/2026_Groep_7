"""Battery and power: what the boards and the servos draw, and what the dock charges.

The servo model is deliberately simple: a servo draws a small idle current plus a current in proportion to its torque,
up to its stall current at the scenario's servo torque limit (a DC motor's current follows its torque). Holding a
pose therefore costs energy too, as it does on the real robot. All values are assumptions until measured.
"""
from coop.hub import Module, check


class Battery(Module):
    kind = 'energy'
    publishes = ('energy/battery',)
    limitations = (
        'Servo current is idle current plus a share of the stall current in proportion to torque; real servos also '
        'draw current to accelerate and lose energy in their gears and control electronics.',
        'The battery voltage stays constant until it is empty: no voltage sag, no capacity loss with cold or age.',
        'The boards draw a constant power; the camera, Wi-Fi and infrared LEDs do not vary with what they do.',
        'Charging adds a constant power until full, with no slower constant-voltage phase at the end.',
    )

    def __init__(self, settings, environment, servos):
        super().__init__('energy', 'Battery & power')
        self.settings, self.environment, self.servos = settings, environment, servos
        self.reset()

    def reset(self):
        s = self.settings
        self.charge = s['start_charge'] * s['battery_wh']  # Wh in the battery
        self.used = 0.       # Wh drawn since the start
        self.charged = 0.    # Wh put in by the dock
        self.power = self.base_power()
        self.lowest = self.state_of_charge()

    def configure(self, settings, environment):
        self.settings, self.environment = settings, environment

    def ir_on(self):
        e = self.environment
        return e['time_of_day'] == 'night' and e['ir_light']

    def base_power(self):
        return self.settings['base_power'] + (self.settings['ir_power'] if self.ir_on() else 0.)

    def servo_power(self, torques, limit):
        """Watts drawn by the servos for a set of joint torques (Nm) and the servo torque limit (Nm)."""
        s = self.settings
        current = sum(s['servo_idle_current'] + s['servo_stall_current'] * min(1., abs(t) / limit) for t in torques)
        return s['voltage'] * current

    def drain(self, dt, torques, limit):
        """Run the robot for dt seconds with these joint torques; returns the power in watts."""
        self.power = self.base_power() + self.servo_power(torques, limit)
        energy = self.power * dt / 3600
        self.used += energy
        self.charge = max(0., self.charge - energy)
        self.lowest = min(self.lowest, self.state_of_charge())
        return self.power

    def charge_for(self, dt):
        """Docked: the dock powers the robot and charges the battery."""
        room = self.settings['battery_wh'] - self.charge
        energy = min(room, self.settings['charge_power'] * dt / 3600)
        self.charge += energy
        self.charged += energy
        self.power = 0.

    def state_of_charge(self):
        return self.charge / self.settings['battery_wh']

    def empty(self):
        return self.charge <= 0.

    def status(self):
        return 'ok' if not self.empty() else 'error'

    def reading(self):
        return {'state_of_charge': round(self.state_of_charge(), 4), 'charge_wh': round(self.charge, 4),
                'used_wh': round(self.used, 4), 'charged_wh': round(self.charged, 4), 'power_w': round(self.power, 3),
                'lowest': round(self.lowest, 4), 'ir_on': self.ir_on()}

    def config(self):
        return {**self.settings, 'servos': self.servos}

    def self_test(self):
        s = self.settings
        holding = self.base_power() + self.servo_power([0.] * self.servos, 1.)
        hours = s['battery_wh'] / max(holding, 1e-9)
        full = s['battery_wh'] / s['charge_power'] if s['charge_power'] else float('inf')
        return [
            check('State of charge is between 0 and 100 %', 0 <= self.state_of_charge() <= 1,
                  f'{self.state_of_charge():.0%}'),
            check('Standing still lasts at least 10 minutes', hours * 60 >= 10,
                  f'{holding:.1f} W without load: {hours * 60:.0f} min on a full battery'),
            check('The dock can charge the battery', s['charge_power'] > 0, f'empty to full in {full * 60:.0f} min'
                  if s['charge_power'] else 'charging power is 0'),
        ]
