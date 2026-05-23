#!/usr/bin/env python3
"""Fusion HAT debug dashboard"""
from flask import Flask, jsonify, render_template, request
from fusion_hat.adc import ADC
from fusion_hat.battery import Battery
from fusion_hat.motor import Motor as _Motor
import time

app = Flask(__name__)

# Monkey-patch Motor.power to preserve signed power
_orig_power = _Motor.power
def _patched_power(self, power=None):
    if power is None:
        return getattr(self, '_signed_power', 0)
    signed = max(-100, min(100, float(power)))
    abs_p = abs(signed)
    dir_ = 1 if power >= 0 else 0
    if self.is_reversed:
        dir_ ^= 1
    if dir_ == 1:
        self.pwm_a.pulse_width_percent(int(abs_p))
        self.pwm_b.pulse_width_percent(0)
    else:
        self.pwm_a.pulse_width_percent(0)
        self.pwm_b.pulse_width_percent(int(abs_p))
    self._power = int(abs_p)
    self._signed_power = signed

_Motor.power = _patched_power

orig_stop = _Motor.stop
def _patched_stop(self):
    self.pwm_a.pulse_width_percent(0)
    self.pwm_b.pulse_width_percent(0)
    self._power = 0
    self._signed_power = 0

_Motor.stop = _patched_stop

# M0 (RF) and M2 (LB) have reversed physical polarity
# is_reversed=True means power(+50) = REV, power(-50) = FWD
# So to make UI FWD = physical FWD, we negate the power for these motors
MOTOR_FLIP = {'M0': -1, 'M1': 1, 'M2': -1, 'M3': 1}
MOTOR_REV_FLAG = {'M0': False, 'M1': False, 'M2': False, 'M3': False}

motors = {name: _Motor(name, is_reversed=MOTOR_REV_FLAG[name]) for name in ['M0', 'M1', 'M2', 'M3']}

motor_signed_power = {'M0': 0, 'M1': 0, 'M2': 0, 'M3': 0}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sensors')
def sensors():
    b = Battery()
    return jsonify({
        'battery': {
            'capacity': b.capacity,
            'voltage': round(b.voltage, 2),
            'is_charging': b.is_charging,
            'status': b.status,
        },
        'adc': [round(ADC(ch).read_voltage(), 3) for ch in range(4)],
        'motors': dict(motor_signed_power),
        'timestamp': time.time(),
    })

@app.route('/api/motor/<name>', methods=['POST'])
def set_motor(name):
    if name not in motors:
        return jsonify({'error': 'unknown motor'}), 404
    power = request.json.get('power', 0) if request.is_json else 0
    signed = max(-100, min(100, int(power)))
    flipped = signed * MOTOR_FLIP[name]
    motors[name].power(flipped)
    # Store original signed power for display (don't use motor's _signed_power which stores flipped value)
    motor_signed_power[name] = signed
    return jsonify({'motor': name, 'power': signed})

@app.route('/api/motor/<name>/stop', methods=['POST'])
def stop_motor(name):
    if name not in motors:
        return jsonify({'error': 'unknown motor'}), 404
    motors[name].stop()
    motor_signed_power[name] = 0
    return jsonify({'motor': name, 'power': 0})

@app.route('/api/stop', methods=['POST'])
def stop_all():
    for m in motors.values():
        m.stop()
    for k in motor_signed_power:
        motor_signed_power[k] = 0
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    print('Fusion HAT Dashboard http://192.168.1.180:8000')
    app.run(host='0.0.0.0', port=8000, threaded=True)