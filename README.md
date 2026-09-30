# fusion-robot-plop

Flask web dashboard for debugging the LAFVIN 4WD robot's Fusion HAT — battery, ADC channels, and motor control.

![Dashboard](templates/index.html)

## Hardware

- LAFVIN 4WD robot with SunFounder Fusion HAT on Raspberry Pi
- 4 motors: M0 (RF), M1 (LF), M2 (LB), M3 (RB)

## Quick Start

Requires the `fusion_hat` library installed on the Raspberry Pi:

```bash
git clone https://github.com/aivijay/fusion-robot-plop.git
cd fusion-robot-plop
pip install fusion-hat flask
sudo python3 fusion_dashboard.py
```

Dashboard available at: `http://192.168.1.180:8000`

> **Note:** Must run as root (`sudo`) to access GPIO/PWM hardware.

## Motor Layout

| Motor | Position | Notes |
|-------|----------|-------|
| M0 | Right Front (RF) | Polarity reversed |
| M1 | Left Front (LF) | Normal |
| M2 | Left Back (LB) | Polarity reversed |
| M3 | Right Back (RB) | Normal |

The `MOTOR_FLIP` map compensates for M0 and M2 having reversed physical polarity — UI forward maps to actual forward on all motors.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/sensors` | GET | Battery, ADC, motor states |
| `/api/motor/<name>` | POST | Set motor power (-100 to +100) |
| `/api/motor/<name>/stop` | POST | Stop single motor |
| `/api/stop` | POST | Stop all motors |

### `/api/sensors` Response

```json
{
  "battery": {
    "capacity": 85,
    "voltage": 7.92,
    "is_charging": false,
    "status": "Discharging"
  },
  "adc": [3.21, 0.0, 0.12, 5.01],
  "motors": {"M0": 0, "M1": 0, "M2": 0, "M3": 0},
  "timestamp": 1713001234.56
}
```

### Set Motor Power

```bash
curl -X POST http://192.168.1.180:8000/api/motor/M0 \
  -H "Content-Type: application/json" \
  -d '{"power": 50}'
```

## Project Structure

```
fusion-robot-plop/
├── fusion_dashboard.py   # Flask app + motor/patch logic
├── templates/
│   └── index.html         # Dashboard UI
└── README.md
```

## Tech Stack

- Python 3
- Flask
- `fusion_hat` library (SunFounder)
- Vanilla JS (no build step)
