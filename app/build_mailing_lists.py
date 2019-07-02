from datetime import date

import db_handler

dt = date.today()
data = db_handler.get_data_object_from_db(2019, '410')

# PDGs
all_emails = []
while data.next_district():
    emails = [f'{o.member.name} <{o.member.email}>' for o in data.get_past_dgs() + data.get_past_foreign_dgs() if o.member.email and o.member.is_active]
    with open(f'{dt:%y%m%d}_{data.district.file_name}_pdg_emails.txt', 'w') as fh:
        fh.write('\n'.join(emails))
    all_emails.extend(emails)
with open(f'{dt:%y%m%d}_{data.struct.file_name}_pdg_emails.txt', 'w') as fh:
    fh.write(';'.join(all_emails))


