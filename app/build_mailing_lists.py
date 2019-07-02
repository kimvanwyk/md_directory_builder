from collections import defaultdict
from datetime import date

import db_handler

dt = date.today()
data = db_handler.get_data_object_from_db(2019, '410')

OFFICER_MAP = {'Club President': 'pres',
               'Club Secretary': 'sec',
               'Club Treasurer': 'treas',
               'Club Membership Chairperson': 'mem_chair'}

def build_mailing_list(struct, officer, lines):
    with open(f'{dt:%y%m%d}_{struct}_{officer}_emails.txt', 'w') as fh:
        fh.write('\n'.join(lines))

all_emails = defaultdict(list)
while data.next_district():
    emails = defaultdict(list)
    # PDGs
    emails['pdg'] = [f'{o.member.name} <{o.member.email}>' for o in data.get_past_dgs() + data.get_past_foreign_dgs() if o.member.email and o.member.is_active]
    all_emails['pdg'].extend(emails)

    # club officers
    for club in data.get_district_clubs():
        for off in club.officers:
            title = OFFICER_MAP.get(off.title, None)
            if title and off.member and off.member.email:
                emails[title].append(f'{off.member.name} <{off.member.email}>')
                all_emails[title].append(off.member.email)

    for (k,v) in emails.items():
        build_mailing_list(data.district.file_name, k, v)

for (k,v) in all_emails.items():
    build_mailing_list(data.struct.file_name, k, v)


