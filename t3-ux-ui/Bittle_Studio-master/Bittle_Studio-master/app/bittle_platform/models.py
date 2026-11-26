"""Robot models the 3D twin can show: the stock Bittle and the team's crab legs (front knees forward).

The crab model is the URDF the leg-design code writes (coop/legs.py); the page loads it like the stock file and works
out the leg positions itself (forward kinematics), so the twin needs no physics.
"""
from coop import config
from coop import legs as leg_design
from engine import asset_url

DESCRIPTIONS = {
    'stock': ('Bittle (standaard)', 'Bittle X zoals geleverd: alle knieën naar achter.'),
    'crab': ('Krabpoten', 'Langere poten, voorknieën naar voor en achterknieën naar achter, 15° naar buiten.'),
}


def models():
    """[{id, name, description, urdf}] with the URL of each model's URDF (the crab file is written when missing)."""
    files = {'stock': leg_design.BITTLE / 'bittle.urdf', 'crab': leg_design.generate(config.LEG_PRESETS['crab']['legs'])}
    return [{'id': key, 'name': name, 'description': text, 'urdf': asset_url(files[key])}
            for key, (name, text) in DESCRIPTIONS.items()]
