''' Tests for db_handler classes and methods
'''

from pprint import pprint

import db_handler

MEMBER_IDS = {'Kim': 2602128,
       'Vicki': 2352224,
       'Denis': 666898,
       'Alistair': 903648,
       'Avril': 4200750,
       'Trevor': 709888,
       'Phil': 2687992,
       'Yolandi': 3762497,
       'Barbara': 2680550,
       'Jacqui': 1399208,
       'Dave': 355357,
       'Neville': 3478783,
       'Beryl': 4040774,
       'Lyn': 349981,
       'Malcolm': 990112
       }

CLUB_IDS = {'North Durban': 27814,
            'Benoni Lakes': 115092
       }

sl = db_handler.get_struct_list()
print(sl)

### Tests for the data class

data = db_handler.Data(2019, sl[2])
print(data.struct.long_name)
while data.next_district():
    print(data.district.long_name)
data.reset()

offs = []
for off in data.struct.officers:
    if 'Council Chairperson' == off.title:
        offs.append(off)
        break
dgs = []
vdgs = []
while data.next_district():
    for off in data.district.officers:
        if off.title == 'District Governor':
            dgs.append(off)
        if off.title == 'First Vice District Governor':
            vdgs.append(off)
offs.extend(dgs)
offs.extend(vdgs)
for off in data.struct.officers:
    if 'Council Chairperson' != off.title:
        offs.append(off)

pprint([(o.title, o.member.long_name) for o in offs])


# pprint([(o.title, o.member.long_name) for o in data.struct.officers])
# while data.next_district():
#     pprint([(o.title, o.member.long_name) for o in data.district.officers[:2]])



# pprint([(po.year, po.end_month, po.member.long_name) for po in data.get_past_ccs()][-10:])
# data.reset()
# data.next_district()
# pprint([(po.year, po.end_month, po.previous_district.name, po.member.long_name) for po in data.get_past_dgs()][-10:])
# data.reset()
# data.next_district()
# pprint([c.name for c in data.get_district_clubs()][-5:])

### Tests for the db class

# db = data.db
# for (k,v) in MEMBER_IDS.items():
#     print db.get_member(v)

# for (k,v) in CLUB_IDS.items():
#     print db.get_club(v, include_officers=True)

# print db.get_struct(5)
# print db.get_struct(9, include_officers=True)

# pprint(db.get_md_districts(5))

# print db.get_region(3)
# print db.get_region(4)

# print db.get_zone(49)
# print db.get_zone(50)

# pprint(db.get_region_zones(4))
# pprint(db.get_zone_clubs(41))

# pprint([(c.name, (c.zone.name, c.zone.region.name) if c.zone else 'No Zone') for c in db.get_district_clubs(9) if not c.is_closed])
# pprint([r.name for r in db.get_district_regions(9)])
# pprint([z.name for z in db.get_district_zones(9)])

# pprint([(po.year, po.end_month, po.member.first_name, po.member.last_name) for po in db.get_past_ccs(5)])
# pprint([(po.year, po.end_month, po.previous_district.name, po.member.first_name, po.member.last_name) for po in db.get_past_dgs(9)])

# pprint([(po.year, po.end_month, po.previous_district.name, po.member.first_name, po.member.last_name) for po in db.get_past_foreign_dgs(9)])
# pprint([(po.year, po.end_month, po.previous_district.name, po.member.first_name, po.member.last_name) for po in db.get_past_foreign_dgs(10)])

