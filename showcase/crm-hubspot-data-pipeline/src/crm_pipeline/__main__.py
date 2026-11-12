import argparse
import json
from .generate_demo import build
from .pipeline import run
from .hubspot_adapter import read_fixture, get_contacts

p=argparse.ArgumentParser(description='Pipeline CRM démonstratif')
p.add_argument('command',choices=['generate','run','hubspot-fixture','hubspot-api'])
a=p.parse_args()
if a.command=='generate': print(build())
elif a.command=='run': print(json.dumps(run(),ensure_ascii=False,indent=2))
elif a.command=='hubspot-fixture': print(len(read_fixture(__import__('pathlib').Path('data/hubspot_fixture.json'))))
else: print(f'{len(get_contacts())} contacts lus en mode API (lecture seule)')
