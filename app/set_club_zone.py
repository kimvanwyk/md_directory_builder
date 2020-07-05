import db_handler

ZONE_MAPPING = {
    27721: 3,
    27767: 9,
    -2: 7,
    45041: 8,
    27723: 3,
    -6: 5,
    27724: 5,
    115_092: 5,
    33130: 5,
    27770: 2,
    27726: 5,
    61204: 4,
    117_928: 4,
    30754: 9,
    35673: 8,
    27774: 8,
    27775: 8,
    110_924: 8,
    130_226: 12,
    27779: 12,
    33401: 12,
    27730: 3,
    -7: 3,
    27781: 7,
    30407: 12,
    27783: 12,
    27784: 11,
    104_884: 1,
    27746: 3,
    57333: 10,
    29349: 7,
    29192: 7,
    122_767: 3,
    27790: 2,
    27791: 12,
    30913: 9,
    27745: 2,
    27792: 9,
    29725: 12,
    27788: 11,
    27747: 1,
    27796: 7,
    27748: 6,
    27750: 2,
    39796: 6,
    48149: 4,
    27753: 6,
    116_362: 7,
    27814: 8,
    27754: 6,
    111_197: 11,
    29439: 11,
    27804: 11,
    27805: 11,
    27807: 10,
    97579: 2,
    105_249: 4,
    52963: 4,
    27757: 4,
    45984: 10,
    46497: 7,
    109_971: 1,
    27759: 1,
    27760: 1,
    29586: 10,
    102_613: 10,
    29241: 5,
    27764: 2,
    27742: 3,
    27812: 11,
    128_919: 7,
    27766: 3,
    27816: 7,
    44342: 1,
    27818: 9,
    46134: 1,
}


def get_zones(struct, year=2020):
    data = db_handler.get_data_object_from_db(year, struct)
    clubs = [
        c for c in data.get_district_clubs(include_officers=False) if not c.is_closed
    ]
    clubs.sort(key=lambda x: x.name)
    d = {}
    for club in clubs:
        z_id = int(input(f"{club.name}: "))
        d[club.id] = z_id
    print(d)


def insert_zone_mapping(struct, year=2020):
    data = db_handler.get_data_object_from_db(year, struct)
    tc = data.db.tables["clubzone"]
    vals = [
        {"year": 2020, "club_id": k, "zone_id": 32 + v} for (k, v) in ZONE_MAPPING.items()
    ]
    data.db.conn.execute(tc.insert(vals))


insert_zone_mapping("410E")
