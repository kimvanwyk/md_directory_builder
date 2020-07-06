import db_handler

from collections import defaultdict

import sqlalchemy as sa

STRUCT = "410W"


def get_members(club_id=None, struct=STRUCT, year=2020):
    data = db_handler.get_data_object_from_db(year, struct)
    tm = data.db.tables["member"]
    tc = data.db.tables["club"]
    wheres = [tm.c.club_id == tc.c.id, tc.c.struct_id == data.struct_id]
    if club_id:
        wheres.append(tc.c.id == club_id)
    res = data.db.conn.execute(
        sa.select([tm, tc.c.name.label("club")], sa.and_(*wheres))
    ).fetchall()
    members = [
        (m["last_name"], m["first_name"], m["id"], m["club_id"], m["club"]) for m in res
    ]
    members.sort()
    return members


def build_members_dict():
    members = get_members()
    d = defaultdict(list)
    for m in members:
        if m[-1]:
            d[m[-1]].append(m)
    return d


d = build_members_dict()
clubs = list(d.keys())
clubs.sort()
for club in clubs:
    members = d[club]
    print("\n".join([f"{m[0]}, {m[1]}" for m in members]))
    print()
    print()
    members = members[:2]
    print("\n".join([f"{m[0]}, {m[1]}" for m in members]))
    members = get_members(club_id=members[0][-2])
    print()
    print()
    print("\n".join([f"{m[0]}, {m[1]}" for m in members]))
    break
