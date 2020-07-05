import db_handler

import json

data = db_handler.get_data_object_from_db(2019, '410')

clubs = []

while data.next_district():
    clubs.extend([c for c in data.get_district_clubs(include_officers=False) if not c.is_closed])

with open('club_sites.json', 'r') as fh:
    current_sites = json.load(fh)

for c in clubs:
    site = current_sites.get(c.name)
    if site and site != c.website: 
        # data.db.set_club_website(c.id, site)
        print(c.full_name, c.website, site)

