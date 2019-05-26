from collections import defaultdict
import configparser
from enum import Enum
import operator

import attr
from sqlalchemy import create_engine, Table, MetaData, and_, or_, select

from utilities import get_current_year

HANDLE_EXC = True
TABLE_PREFIX = "md_directory"


class ClubType(Enum):
    lions = 1
    branch = 2
    leos = 3
    lioness = 4


@attr.s
class MultipleDistrict(object):
    id = attr.ib(factory=int)
    name = attr.ib(default=None)
    website = attr.ib(default=None)
    is_in_use = attr.ib(default=False)
    officers = attr.ib(factory=list)

    def __attrs_post_init__(self):
        self.long_name = f"Multiple District {self.name}"


@attr.s
class District(MultipleDistrict):
    parent = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.name = "%s%s" % (self.parent.name if self.parent else "", self.name)
        self.long_name = f"District {self.name}"


@attr.s
class BrightsightOffice(object):
    id = attr.ib(factory=int)
    struct = attr.ib(default=None)
    physical_address = attr.ib(factory=list)
    postal_address = attr.ib(factory=list)
    ph = attr.ib(default=None)
    fax = attr.ib(default=None)
    email = attr.ib(default=None)
    website = attr.ib(default=None)
    contact_person = attr.ib(default=None)
    manager = attr.ib(default=None)


@attr.s
class BrightsightOfficeManager(object):
    name = attr.ib(default=None)
    ph = attr.ib(default=None)
    email = attr.ib(default=None)


@attr.s
class Region(object):
    id = attr.ib(factory=int)
    name = attr.ib(default=None)
    chair = attr.ib(default=None)
    district = attr.ib(default=None)


@attr.s
class Zone(Region):
    region = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.long_name = f"{self.name}, {self.region.name}"


@attr.s
class Club(object):
    id = attr.ib(factory=int)
    club_type = attr.ib(default=ClubType.lions)
    struct = attr.ib(default=None)
    prev_struct = attr.ib(default=None)
    name = attr.ib(default=None)
    parent = attr.ib(default=None)
    meeting_time = attr.ib(default=None)
    meeting_address = attr.ib(factory=list)
    postal_address = attr.ib(factory=list)
    charter_year = attr.ib(factory=int)
    website = attr.ib(default=None)
    is_suspended = attr.ib(default=False)
    zone = attr.ib(default=None)
    is_closed = attr.ib(default=False)
    officers = attr.ib(factory=list)


@attr.s
class Member(object):
    id = attr.ib(factory=int)
    first_name = attr.ib(default=None)
    last_name = attr.ib(default=None)
    is_deceased = attr.ib(default=False)
    is_resigned = attr.ib(default=False)
    partner = attr.ib(default=None)
    is_partner_lion = attr.ib(default=False)
    join_date = attr.ib(factory=int)
    home_ph = attr.ib(default=None)
    bus_ph = attr.ib(default=None)
    fax = attr.ib(default=None)
    cell_ph = attr.ib(default=None)
    email = attr.ib(default=None)
    club = attr.ib(default=None)
    title = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.name = "%s %s" % (self.first_name, self.last_name)
        if self.partner:
            self.long_name = "%s (%s)" % (self.name, self.partner)
        else:
            self.long_name = self.name


@attr.s
class Officer(object):
    title = attr.ib(default=None)
    member = attr.ib(default=None)
    committee = attr.ib(factory=list)


@attr.s
class PastOfficer(object):
    year = attr.ib(factory=int)
    end_month = attr.ib(default=12)
    member = attr.ib(default=None)


@attr.s
class PastDG(PastOfficer):
    previous_district = attr.ib(default=None)


class DBHandler(object):
    def __init__(self, username, password, schema, host, port, db_type, year=None):
        if not year:
            year = get_current_year()
        self.year = year
        engine = create_engine(
            "%s://%s:%s@%s:%s/%s" % (db_type, username, password, host, port, schema),
            echo=False,
        )
        metadata = MetaData()
        metadata.bind = engine
        self.conn = engine.connect()
        tables = [
            t[0]
            for t in self.conn.execute("SHOW TABLES").fetchall()
            if TABLE_PREFIX in t[0]
        ]
        self.tables = {}
        for t in tables:
            self.tables[t.split(TABLE_PREFIX)[-1].strip("_")] = Table(
                t, metadata, autoload=True, schema=schema
            )

        self.officer_titles = {}
        to = self.tables["officertitle"]
        res = self.conn.execute(to.select()).fetchall()
        for r in res:
            year = self.year
            office_id = r.id
            if r.ip_id:
                year -= 1
                office_id = r.ip_id
            self.officer_titles[r.id] = (r.title, office_id, year)

        self.merged_structs = defaultdict(list)
        t = self.tables["structmerge"]
        res = self.conn.execute(t.select()).fetchall()
        for r in res:
            self.merged_structs[r.current_struct_id].append(r.previous_struct_id)

        self.struct_ids = {}
        t = self.tables["struct"]
        res = self.conn.execute(t.select(t.c.in_use_b == 1)).fetchall()
        for r in res:
            s = self.get_struct(r.id)
            self.struct_ids[s.name] = r.id

    def __db_lookup(self, lookup_id, table, mapping, exclude=[], lookup_field="id"):
        t = self.tables[table]
        res = self.conn.execute(
            t.select(getattr(t.c, lookup_field) == lookup_id)
        ).fetchone()
        map = {}
        if res:
            for (k, v) in list(res.items()):
                if k not in exclude:
                    map[mapping.get(k, k)] = bool(v) if "_b" in k else v
        return (map, res)

    def __get_district_child(self, struct_id, table, order_field, getter, kwds={}):
        t = self.tables[table]
        res = db.conn.execute(
            t.select(t.c.struct_id == struct_id).order_by(getattr(t.c, order_field))
        ).fetchall()
        return [getter(r.id, **kwds) for r in res]

    def get_struct_list(self):
        k = list(self.struct_ids.keys())
        k.sort()
        return k

    def get_title(
        self,
        member_id,
        struct_officers=(
            (19, 0, operator.eq, "IP"),
            (19, -1, operator.eq, "PIP"),
            (21, 0, operator.eq, "ID"),
            (21, -1, operator.eq, "ID"),
            (11, 0, operator.eq, "CC"),
            (5, 0, operator.eq, "DG"),
            (11, -1, operator.le, "PCC"),
            (13, 0, operator.eq, "CCE"),
            (5, -1, operator.eq, "IPDG"),
            (7, 0, operator.eq, "1VDG"),
            (8, 0, operator.eq, "2VDG"),
            (5, -2, operator.le, "PDG"),
            (14, 0, operator.eq, "CS"),
            (15, 0, operator.eq, "CT"),
            (9, 0, operator.eq, "DCS"),
            (10, 0, operator.eq, "DCT"),
        ),
        club_officers=(
            (1, 0, operator.eq, "LP"),
            (2, 0, operator.eq, "LS"),
            (3, 0, operator.eq, "LT"),
            (1, -1, operator.le, "PLP"),
        ),
    ):
        """ Return a title for the supplied member_id, or None
        if none found
        """

        def search_officers(member_id, table, mapping):
            title = None
            t = self.tables[table]
            res = db.conn.execute(t.select(t.c.member_id == member_id)).fetchall()
            index = 100
            for (n, (office_id, addition, op, ttl)) in enumerate(mapping):
                for r in res:
                    if all(
                        (
                            (office_id == r.office_id),
                            (op(r.year, self.year + addition)),
                            (n < index),
                        )
                    ):
                        index = n
                        title = ttl
                        break
            return title

        title = search_officers(member_id, "structofficer", struct_officers)
        if not title:
            for (table, ttl) in (("regionchair", "RC"), ("zonechair", "ZC")):
                t = self.tables[table]
                res = db.conn.execute(
                    t.select(and_(t.c.member_id == member_id, t.c.year == self.year))
                ).fetchall()
                if res:
                    title = ttl
                    break
        if not title:
            for (type_id, ttl) in ((1, "MDC"), (0, "DC")):
                t = self.tables["struct"]
                structs = db.conn.execute(t.select(t.c.type_id == type_id)).fetchall()
                t = self.tables["structchair"]
                for struct in structs:
                    res = db.conn.execute(
                        t.select(
                            and_(
                                t.c.member_id == member_id,
                                t.c.year == self.year,
                                t.c.struct_id == struct.id,
                            )
                        )
                    ).fetchall()
                    if res:
                        title = ttl
                        break
                if title:
                    break
        if not title:
            title = search_officers(member_id, "clubofficer", club_officers)
        return title

    def get_member(
        self,
        member_id,
        mapping={
            "deceased_b": "is_deceased",
            "resigned_b": "is_resigned",
            "partner_lion_b": "is_partner_lion",
        },
        exclude=("club_id",),
        email=None,
    ):
        (map, res) = self.__db_lookup(member_id, "member", mapping, exclude)
        if res["club_id"]:
            map["club"] = self.get_club(res["club_id"])
        map["title"] = self.get_title(member_id)
        if email:
            map["email"] = email
        m = Member(**map)
        return m

    def get_club(
        self,
        club_id,
        mapping={
            "suspended_b": "is_suspended",
            "closed_b": "is_closed",
            "meet_time": "meeting_time",
        },
        exclude=(
            "parent_id",
            "struct_id",
            "prev_struct_id",
            "type",
            "add1",
            "add2",
            "add3",
            "add4",
            "add5",
            "po_code",
            "postal",
            "postal1",
            "postal2",
            "postal3",
            "postal4",
            "postal5",
            "zone_id",
        ),
        office_ids={
            ClubType.lions: (1, 2, 3, 4),
            ClubType.branch: (16, 1, 2, 3),
            ClubType.lioness: (16, 1, 2, 3),
            ClubType.leos: (20, 1, 2, 3),
        },
        club_type_mapping={
            0: ClubType.lions,
            1: ClubType.branch,
            2: ClubType.lioness,
            3: ClubType.leos,
        },
        include_officers=False,
    ):
        (map, res) = self.__db_lookup(club_id, "club", mapping, exclude)
        if not res:
            return None
        map["meeting_address"] = [
            res["add%s" % i] for i in range(1, 6) if res["add%s" % i]
        ]
        map["postal_address"] = [
            res["postal%s" % i] for i in range(1, 6) if res["postal%s" % i]
        ]
        if res["po_code"]:
            map["postal_address"].append(res["po_code"])
        map["club_type"] = club_type_mapping[res["type"]]

        if res["parent_id"]:
            map["parent"] = self.get_club(res["parent_id"], include_officers=False)
        if include_officers:
            ts = self.tables["clubofficer"]
            map["officers"] = []
            for office_id_index in office_ids[map["club_type"]]:
                (title, office_id, year) = self.officer_titles[office_id_index]
                res = self.conn.execute(
                    ts.select(
                        and_(
                            ts.c.club_id == club_id,
                            ts.c.year == year,
                            ts.c.office_id == office_id,
                        )
                    )
                ).fetchone()
                if res:
                    map["officers"].append(
                        Officer(title, self.get_member(res.member_id, email=res.email))
                    )

        t = self.tables["clubzone"]
        res = db.conn.execute(
            t.select(and_(t.c.club_id == club_id, t.c.year == self.year))
        ).fetchone()
        if res:
            map["zone"] = self.get_zone(res.zone_id, include_officers=include_officers)

        c = Club(**map)
        return c

    def get_region(self, region_id, exclude=("struct_id",), include_officers=False):
        (map, res) = self.__db_lookup(region_id, "region", {}, exclude)
        map["district"] = self.get_struct(
            res["struct_id"], include_officers=include_officers
        )
        if include_officers:
            t = self.tables["regionchair"]
            res = db.conn.execute(
                t.select(and_(t.c.parent_id == res["id"], t.c.year == self.year))
            ).fetchone()
            if res:
                map["chair"] = self.get_member(res["member_id"], email=res["email"])
        r = Region(**map)
        return r

    def get_region_zones(self, region_id, include_officers=False):
        t = self.tables["zone"]
        res = db.conn.execute(
            t.select(and_(t.c.region_id == region_id, t.c.in_region_b == 1)).order_by(
                t.c.id
            )
        ).fetchall()
        return [self.get_zone(r.id, include_officers=include_officers) for r in res]

    def get_zone(
        self,
        zone_id,
        exclude=("struct_id", "in_region_b", "region_id"),
        include_officers=False,
    ):
        (map, res) = self.__db_lookup(zone_id, "zone", {}, exclude)
        map["district"] = self.get_struct(
            res["struct_id"], include_officers=include_officers
        )
        if res["in_region_b"]:
            map["region"] = self.get_region(
                res["region_id"], include_officers=include_officers
            )
        if include_officers:
            t = self.tables["zonechair"]
            res = db.conn.execute(
                t.select(and_(t.c.parent_id == res["id"], t.c.year == self.year))
            ).fetchone()
            if res:
                map["chair"] = self.get_member(res["member_id"], email=res["email"])
        z = Zone(**map)
        return z

    def get_zone_clubs(self, zone_id, include_officers=False):
        t = self.tables["clubzone"]
        res = db.conn.execute(
            t.select(and_(t.c.zone_id == zone_id, t.c.year == self.year))
        ).fetchall()
        clubs = [
            self.get_club(r.club_id, include_officers=include_officers) for r in res
        ]
        clubs.sort(key=lambda x: x.name)
        return clubs

    def get_struct(
        self,
        struct_id,
        mapping={"in_use_b": "is_in_use"},
        class_map={
            0: (District, (5, 6, 7, 8, 9, 10)),
            1: (MultipleDistrict, (11, 12, 13, 14, 15)),
        },
        exclude=("parent_id", "type_id"),
        include_officers=False,
    ):
        (map, res) = self.__db_lookup(struct_id, "struct", mapping, exclude)
        if res.parent_id:
            map["parent"] = self.get_struct(res.parent_id)
        (cls, office_ids) = class_map[res["type_id"]]

        if include_officers:
            ts = self.tables["structofficer"]
            map["officers"] = []
            for office_id_index in office_ids:
                (title, office_id, year) = self.officer_titles[office_id_index]
                res = self.conn.execute(
                    ts.select(
                        and_(
                            ts.c.struct_id == struct_id,
                            ts.c.year == year,
                            ts.c.office_id == office_id,
                        )
                    )
                ).fetchone()
                if res:
                    map["officers"].append(
                        Officer(title, self.get_member(res.member_id, email=res.email))
                    )
            t = self.tables["structchair"]
            res = self.conn.execute(
                t.select(and_(t.c.struct_id == struct_id, t.c.year == year)).order_by(
                    t.c.office
                )
            ).fetchall()
            if res:
                for r in res:
                    if r.member_id:
                        map["officers"].append(
                            Officer(
                                r.office,
                                self.get_member(r.member_id, email=r.email),
                                committee=r.committee_members.split(",")
                                if r.committee_members
                                else [],
                            )
                        )
        s = cls(**map)
        return s

    def get_brightsight_offices(
        self,
        struct_id,
        mapping={"tel": "ph"},
        exclude=(
            "struct_id",
            "manager",
            "manager_email",
            "manager_cell_ph",
            "add1",
            "add2",
            "add3",
            "add4",
            "add5",
            "po_code",
            "postal",
            "postal1",
            "postal2",
            "postal3",
            "postal4",
            "postal5",
        ),
    ):
        (map, res) = self.__db_lookup(
            struct_id, "brightsightoffice", mapping, exclude, lookup_field="struct_id"
        )
        map["physical_address"] = [
            res["add%s" % i] for i in range(1, 6) if res["add%s" % i]
        ]
        map["postal_address"] = [
            res["postal%s" % i] for i in range(1, 6) if res["postal%s" % i]
        ]
        if res["po_code"]:
            map["postal_address"].append(res["po_code"])
        map["manager"] = BrightsightOfficeManager(
            res["manager"], res["manager_cell_ph"], res["manager_email"]
        )
        map["struct"] = self.get_struct(struct_id)
        return BrightsightOffice(**map)

    def get_md_districts(self, struct_id, include_officers=False):
        t = self.tables["struct"]
        return [
            self.get_struct(r.id, include_officers=include_officers)
            for r in db.conn.execute(
                t.select(and_(t.c.parent_id == struct_id, t.c.in_use_b == 1)).order_by(
                    t.c.name
                )
            ).fetchall()
        ]

    def get_district_clubs(self, struct_id, include_officers=False):
        return self.__get_district_child(
            struct_id,
            "club",
            "name",
            self.get_club,
            {"include_officers": include_officers},
        )

    def get_district_regions(self, struct_id, include_officers=False):
        return self.__get_district_child(
            struct_id,
            "region",
            "id",
            self.get_region,
            {"include_officers": include_officers},
        )

    def get_district_zones(self, struct_id, include_officers=False):
        return self.__get_district_child(
            struct_id,
            "zone",
            "id",
            self.get_zone,
            {"include_officers": include_officers},
        )

    def get_past_struct_officers(
        self, struct_id, office_id, cls_map={11: PastOfficer, 5: PastDG}
    ):
        to = self.tables["structofficer"]
        ts = self.tables["struct"]
        res = self.conn.execute(
            select(
                (to.c.year, to.c.end_month, to.c.member_id, ts.c.id, ts.c.in_use_b),
                and_(
                    to.c.struct_id.in_(
                        [struct_id] + self.merged_structs.get(struct_id, [])
                    ),
                    to.c.office_id == office_id,
                    to.c.year < self.year,
                    to.c.struct_id == ts.c.id,
                ),
            ).order_by(to.c.year, to.c.end_month, ts.c.name)
        ).fetchall()
        offs = []
        for r in res:
            offs.append(
                cls_map[office_id](r.year, r.end_month, self.get_member(r.member_id))
            )
            if r.in_use_b == 0:
                offs[-1].previous_district = self.get_struct(r.id)
        return offs

    def get_past_foreign_dgs(self, struct_id, office_id=5):
        to = self.tables["structofficer"]
        ts = self.tables["struct"]
        tm = self.tables["member"]
        tc = self.tables["club"]
        res = self.conn.execute(
            select(
                (to.c.year, to.c.end_month, to.c.member_id, ts.c.id),
                and_(
                    to.c.struct_id.notin_(
                        [struct_id] + self.merged_structs.get(struct_id, [])
                    ),
                    to.c.office_id == office_id,
                    to.c.year < self.year,
                    to.c.struct_id == ts.c.id,
                    tm.c.id == to.c.member_id,
                    tm.c.club_id == tc.c.id,
                    tc.c.struct_id == struct_id,
                ),
            ).order_by(to.c.year, to.c.end_month, ts.c.name)
        ).fetchall()
        return [
            PastDG(
                r.year,
                r.end_month,
                self.get_member(r.member_id),
                previous_district=self.get_struct(r.id),
            )
            for r in res
        ]

    def get_past_ccs(self, struct_id):
        return self.get_past_struct_officers(struct_id, 11)

    def get_past_dgs(self, struct_id):
        return self.get_past_struct_officers(struct_id, 5)


class Data(object):
    def __init__(self, year, struct):
        self.db = db
        self.struct_id = self.db.struct_ids[struct]
        self.db.year = year
        self.struct = self.db.get_struct(self.struct_id, include_officers=True)
        self.__district_index = -1
        self.__region_index = -1
        self.__zone_index = -1
        if type(self.struct) == MultipleDistrict:
            self.md = True
            self.districts = self.db.get_md_districts(
                self.struct_id, include_officers=True
            )
            self.district = None
        else:
            self.md = False
            self.districts = []
            self.district = self.struct
            self.regions = []
            self.zones = []

    def next_district(self):
        if self.md:
            self.__district_index += 1
            if self.__district_index >= len(self.districts):
                self.district = False
                return False
            self.district = self.districts[self.__district_index]
            self.regions = self.db.get_district_regions(
                self.district.id, include_officers=True
            )
            self.zones = self.db.get_district_zones(
                self.district.id, include_officers=True
            )
        return True

    def next_region(self):
        if self.district:
            self.__region_index += 1
            if self.__region_index >= len(self.regions):
                self.region = False
                return False
            self.region = self.regions[self.__region_index]
        return True

    def next_zone(self):
        if self.district:
            self.__zone_index += 1
            if self.__zone_index >= len(self.zones):
                self.zone = False
                return False
            self.zone = self.zones[self.__zone_index]
        return True

    def reset(self):
        if self.md:
            self.district = None
            self.__district_index = -1

    def reset_district(self):
        if self.district:
            self.region = None
            self.__region_index = -1
            self.zone = None
            self.__zone_index = -1

    def get_past_ccs(self):
        return self.db.get_past_ccs(self.struct_id)

    def get_brightsight_offices(self):
        return self.db.get_brightsight_offices(self.struct_id)

    def get_past_dgs(self):
        if self.district:
            return self.db.get_past_dgs(self.district.id)
        return []

    def get_past_foreign_dgs(self):
        if self.district:
            return self.db.get_past_foreign_dgs(self.district.id)
        return []

    def get_district_clubs(self):
        if self.district:
            return self.db.get_district_clubs(self.district.id, include_officers=True)
        return []

    def get_district_regions(self):
        if self.district:
            return self.db.get_district_regions(self.district.id)
        return []

    def get_region_zones(self, include_officers=False):
        if self.region:
            zones = self.db.get_region_zones(
                self.region.id, include_officers=include_officers
            )
            return zones
        return []

    def get_zone_clubs(self, include_officers=False):
        if self.zone:
            clubs = self.db.get_zone_clubs(
                self.zone.id, include_officers=include_officers
            )
            return clubs
        return []


def get_db_settings(fn="db_settings.ini", sec="DB"):
    settings = {}
    cp = configparser.SafeConfigParser()
    with open(fn, "r") as fh:
        cp.readfp(fh)
    for opt in cp.options(sec):
        settings[opt] = cp.get(sec, opt)
    return settings


def get_struct_list():
    return db.get_struct_list()


db = DBHandler(**get_db_settings())
