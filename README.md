# Racker

Blender plugin to create 19-inch rack drawings.

Generate complete rack drawings with top, bottom, and sides.
Define material depth and thickness.
When entering the number of rack units (U), the side height is calculated.

## Installation

### Python virtual environment (optional, for local dev)

1. Create a venv with Make (dev tooling/tests): `make venv`
2. Or create it manually: `python3 -m venv .venv`
3. Activate it (only needed for local dev):
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\\Scripts\\activate`
4. Upgrade pip (optional): `python -m pip install --upgrade pip`

### Blender add-on

1. Install into Blender: `make install`
2. Open Blender and ensure the add-on named "Racker" is enabled.
