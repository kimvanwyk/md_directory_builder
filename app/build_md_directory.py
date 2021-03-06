import filter_and_build

import copy
from datetime import datetime
import glob
import os, os.path
import itertools


import db_handler


# char for a LaTeX non-breaking space
LEFT_COLUMN_WIDTH = 60
BRIGHTSIGHT_LEFT_COLUMN_WIDTH = 20
RIGHT_COLUMN_WIDTH = 40
NON_BREAKING_CHAR_PLACEHOLDER = "~"
NON_BREAKING_SPACE = r"\ "

MAX_PER_PAGE_OFFICERS = 6


def get_md_officers(data):
    offs = []
    for off in data.struct.officers:
        if "Council Chairperson" == off.title:
            offs.append(off)
            break
    dgs = []
    vdgs = []
    titles = {"District Governor": dgs, "First Vice District Governor": vdgs}
    while data.next_district():
        for off in data.district.officers:
            if off.title in titles:
                o = copy.copy(off)
                o.title = f"{off.title}, District {data.district.name}"
                titles[off.title].append(o)
    offs.extend(dgs)
    offs.extend(vdgs)
    for off in data.struct.officers:
        if "Council Chairperson" != off.title:
            offs.append(off)
    return offs


class Outputs(object):
    def __init__(self):
        self.outputs = []

    def add_output(self, output):
        self.outputs.append(output)

    def build(self):
        for output in self.outputs:
            output.build()

    def newpage(self, first_only=False):
        self.outputs[0].newpage()
        if not first_only:
            for output in self.outputs[1:]:
                output.newpage()

    def __getattr__(self, name):
        def method(*args, **kwds):
            ret = getattr(self.outputs[0], name)(*args, **kwds)
            if len(self.outputs) > 1:
                ret = getattr(self.outputs[-1], name)(*args, **kwds)
            return ret

        return method


class Output(object):

    year = None
    dt = None

    """ Hold state for the output lines
    """

    def __init__(self, title, newpage=False):
        self.out = []
        if newpage:
            self.newpage()
        self.title = f"{self.year}/{self.year+1} {title} Directory"
        self.fn = (
            f"{self.year}{self.year+1}_{title.lower().replace(' ', '_')}_directory.txt"
        )

    def build(self, ext_keep=(".pdf", ".tex")):
        with open(self.fn, "w") as fh:
            fh.write("\n".join(self.out))

        filter_and_build.build_pdf(
            self.fn, self.title, f"compiled on {self.dt:%A %d %b %Y at %H:%M}"
        )

        for f in glob.glob(f"{os.path.splitext(self.fn)[0]}.*"):
            if all(e not in f for e in ext_keep):
                os.remove(f)

    def __output_aligned_left_column_row(
        self, left, right, align="l", left_column_width=LEFT_COLUMN_WIDTH
    ):
        a = getattr(left, f"{align}just")
        if left:
            l = a(left_column_width, NON_BREAKING_CHAR_PLACEHOLDER).replace(
                NON_BREAKING_CHAR_PLACEHOLDER, NON_BREAKING_SPACE
            )
        else:
            l = left
        if right:
            r = right.ljust(RIGHT_COLUMN_WIDTH, NON_BREAKING_CHAR_PLACEHOLDER).replace(
                NON_BREAKING_CHAR_PLACEHOLDER, NON_BREAKING_SPACE
            )
        else:
            r = right
        self.out.append(f"|{l}|{r}|")

    def __output_region_zone(self, children, chair, child_desc, chair_desc):
        if not chair:
            chair_rows = ["Position Vacant"]
        else:
            chair_rows = self.get_member_rows(chair, trail=False)
        self.__output_aligned_left_column_row(child_desc, chair_desc)
        self.out.append("|:----|:----|")
        for (child, cr) in itertools.zip_longest(
            [getattr(c, "full_name", c.name) for c in children],
            chair_rows,
            fillvalue="",
        ):
            # self.__output_aligned_left_column_row(child, cr)
            self.out.append(f"|{child}|{cr}|")
        self.out.append("")

    def newpage(self):
        self.out.append(r"\newpage")

    def columnbreak(self):
        self.out.append(r"\columnbreak")
        self.out.append("")

    def blank(self):
        self.out.append("")

    def vacant(self):
        self.out.extend(["Position Vacant", ""])

    def get_member_rows(self, member, trail=True, include_homeclub=True):
        t = " \\" if trail else ""
        out = []
        title = member.title
        if not title:
            title = "Lion"
        out.append(f"{title} {member.long_name}{t}")
        if member.is_deceased:
            out.append(f"**Called to Higher Service**{t}")
            return out
        if member.is_resigned:
            out.append(f"**Resigned**{t}")
            return out
        if member.cell_ph:
            out.append(f"**Cell:** {member.cell_ph}{t}")
        if member.email:
            out.append(f"<{member.email}>{t}")
        if include_homeclub and member.club:
            out.append(f"**Home Club:** {member.club.name}{t}")
        return out

    def output_member(self, member):
        if member:
            self.out.extend(self.get_member_rows(member))

    def output_club(self, club):
        n = 0
        if club.name:
            n += 1
            name = club.name
            if club.club_type != db_handler.ClubType.lions:
                parent = f"Club of {club.parent.name}" if club.parent else ""
                name = f"{name} ({club.club_type.name.capitalize()} {parent})"
            self.output_heading(3, name)
            if club.charter_year:
                title = (
                    "Chartered"
                    if club.club_type == db_handler.ClubType.lions
                    else "Established"
                )
                year = f"{title}: {club.charter_year}. "
            else:
                year = ""
            s = f"{year}Part of {club.zone.long_name}." if club.zone else year
            if club.id > 0:
                s = f"{s} Club Number: {club.id}."
            if s:
                self.out.append(s)
            officers = []
            for off in club.officers:
                if "membership chair" not in off.title.lower() and off.member:
                    l = [
                        off.title.replace("Club ", "").replace("Chairperson", "Chair"),
                        "--",
                    ]
                    l.extend(
                        self.get_member_rows(
                            off.member, trail=False, include_homeclub=False
                        )
                    )
                    officers.append(l)
            self.blank()
            if officers:
                n += 1
                self.blank()
                for row in itertools.zip_longest(*officers, fillvalue=""):
                    self.out.append(f"|{'|'.join(row)}|")
            else:
                self.out.append("*No club officer information available.*")
            meeting = []
            if club.meeting_time:
                meeting.append(club.meeting_time)
            if club.meeting_address:
                meeting.append(", ".join(club.meeting_address))
            if any((meeting, club.postal_address, club.website)):
                n += 1
            if meeting:
                self.blank()
                self.out.append(f"Meetings: {'. '.join(meeting)}")
            if club.postal_address:
                self.blank()
                self.out.append(f"Postal Address: {', '.join(club.postal_address)}")
            if club.website:
                self.blank()
                self.out.append(f"Website: <{club.website}>")
            self.blank()
        return n

    def output_officer(self, off):
        self.out.append(f"### {off.title}")
        self.output_member(off.member)
        self.out.append("")
        self.out.append("")
        if off.committee:
            self.out.append(
                f'**Committee:** {", ".join([c.strip() for c in off.committee])}'
            )
        self.out.append("\\ ")
        self.out.append("")

    def output_past_officer(self, off):
        year = f"{off.year}/{off.year+1}"
        if hasattr(off, "previous_district") and off.previous_district:
            year = f"{year} (xxSI {off.previous_district.long_name})"
        self.out.append(f"### {year} {{-}}")
        self.output_member(off.member)
        self.out.append("\\ ")
        self.out.append("")

    def output_region(self, clubs, chair):
        self.__output_region_zone(clubs, chair, "Zones", "Region Chair")

    def output_zone(self, clubs, chair):
        self.__output_region_zone(clubs, chair, "Clubs", "Zone Chair")

    def start_multicols(self):
        self.out.extend(
            ["\\Begin{multicols*}{2}", "\\setlength{\\columnseprule}{0.4pt}", ""]
        )

    def end_multicols(self):
        self.out.extend(["", "\\End{multicols*}", ""])

    def output_struct_preamble(self, struct):
        self.out.extend([f"# {struct.long_name}", ""])

    def output_heading(self, level, heading):
        self.out.extend([f"{'#' * level } {heading}", ""])

    def output_md_past_council_chairs_header(self):
        self.out.extend([f"## Past Council Chairpersons", ""])

    def output_website(self, website):
        self.out.append("## Website")
        self.out.append(f"<{website}>")
        self.out.append("")

    def output_brightsight_office(self, bso):
        self.out.append("## Lions Brightsight Office")
        self.out.append("")
        self.out.append("### Contact Details")
        self.out.append("")
        self.out.append("|||")
        self.out.append("|----:|:----|")
        self.__output_aligned_left_column_row(
            "Manager:", bso.contact_person, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
        )
        if bso.physical_address:
            self.__output_aligned_left_column_row(
                "Physical Address:",
                bso.physical_address[0],
                "r",
                BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
            )
            for pa in bso.physical_address[1:]:
                self.__output_aligned_left_column_row(
                    "", pa, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
                )
        if bso.postal_address:
            self.__output_aligned_left_column_row(
                "Postal Address:",
                bso.postal_address[0],
                "r",
                BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
            )
            for pa in bso.postal_address[1:]:
                self.__output_aligned_left_column_row(
                    "", pa, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
                )
        if bso.ph:
            self.__output_aligned_left_column_row(
                "Telephone:", bso.ph, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        if bso.email:
            self.__output_aligned_left_column_row(
                "Email:", f"<{bso.email}>", "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        if bso.website:
            self.__output_aligned_left_column_row(
                "Website:", f"<{bso.website}>", "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        self.out.append("")
        self.out.append(
            f"**Please submit scripts via the Brightsight website: <{bso.website}>**"
        )
        self.out.append("")

    def output_district_office(self, distoffice):
        self.out.append("## District Office")
        self.out.append("")
        self.out.append("|||")
        self.out.append("|----:|:----|")
        self.__output_aligned_left_column_row(
            "Contact Person:",
            distoffice.contact_person,
            "r",
            BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
        )
        if distoffice.physical_address:
            self.__output_aligned_left_column_row(
                "Physical Address:",
                distoffice.physical_address[0],
                "r",
                BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
            )
            for pa in distoffice.physical_address[1:]:
                self.__output_aligned_left_column_row(
                    "", pa, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
                )
        if distoffice.postal_address:
            self.__output_aligned_left_column_row(
                "Postal Address:",
                distoffice.postal_address[0],
                "r",
                BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
            )
            for pa in distoffice.postal_address[1:]:
                self.__output_aligned_left_column_row(
                    "", pa, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
                )
        if distoffice.ph:
            self.__output_aligned_left_column_row(
                "Telephone:", distoffice.ph, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        if distoffice.email:
            self.__output_aligned_left_column_row(
                "Email:", f"<{distoffice.email}>", "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        if distoffice.hours:
            self.__output_aligned_left_column_row(
                "Hours:", distoffice.hours, "r", BRIGHTSIGHT_LEFT_COLUMN_WIDTH
            )
        if distoffice.website:
            self.__output_aligned_left_column_row(
                "Website:",
                f"<{distoffice.website}>",
                "r",
                BRIGHTSIGHT_LEFT_COLUMN_WIDTH,
            )
        self.out.append("")


def get_outputs(year, struct_name):
    data = db_handler.get_data_object_from_db(year, struct_name)
    Output.year = year
    Output.dt = datetime.now()
    outputs = Outputs()
    if data.md:
        outputs.add_output(
            Output(f"Multiple District {data.struct.name}", newpage=True)
        )
        outputs.output_struct_preamble(data.struct)
        outputs.output_heading(2, "Multiple District Council")
        outputs.start_multicols()
        for (n, off) in enumerate(get_md_officers(data), 1):
            outputs.output_officer(off)
            if n and not (n % MAX_PER_PAGE_OFFICERS):
                outputs.columnbreak()
        outputs.end_multicols()
        outputs.output_website(data.struct.website)
        bso = data.get_brightsight_offices()
        if bso:
            outputs.output_brightsight_office(bso)
        past_ccs = data.get_past_ccs()
        if past_ccs:
            outputs.newpage()
            outputs.output_heading(2, "Past Council Chairs")
            outputs.start_multicols()
            for po in past_ccs:
                outputs.output_past_officer(po)
            outputs.end_multicols()

    data.reset()
    while data.next_district():
        outputs.add_output(Output(f"District {data.district.name}", newpage=True))
        outputs.output_struct_preamble(data.district)
        outputs.output_heading(2, "District Cabinet")
        outputs.start_multicols()
        for (n, off) in enumerate(data.district.officers, 1):
            outputs.output_officer(off)
            if n and not (n % MAX_PER_PAGE_OFFICERS):
                outputs.columnbreak()
        outputs.end_multicols()

        if data.district.website:
            outputs.output_website(data.district.website)
        distoffice = data.get_district_offices()
        if distoffice:
            outputs.output_district_office(distoffice)
        if data.regions:
            outputs.newpage()
            outputs.output_heading(2, "Regions")
            n = 0
            while data.next_region():
                outputs.output_heading(3, data.region.name)
                zones = data.get_region_zones(include_officers=False)
                if zones or data.region.chair:
                    n += 1
                    outputs.output_region(zones, data.region.chair)
                    if n and not (n % 5):
                        outputs.newpage()

        if data.zones:
            outputs.newpage()
            outputs.output_heading(2, "Zones")
            n = 0
            while data.next_zone():
                name = data.zone.name
                if data.zone.region:
                    name = f"{name} ({data.zone.region.name})"
                outputs.output_heading(3, name)
                clubs = data.get_zone_clubs(include_officers=False)
                if clubs or data.zone.chair:
                    outputs.output_zone(clubs, data.zone.chair)
                    n += 1
                    if n and not (n % 3):
                        outputs.newpage()
        data.reset_district()

        clubs = [club for club in data.get_district_clubs() if not club.is_closed]
        if clubs:
            outputs.newpage()
            outputs.output_heading(2, "Clubs")
            n = 0
            for club in clubs:
                n += outputs.output_club(club)
                if n >= 9:
                    outputs.newpage()
                    n = 0

        past_dgs = data.get_past_dgs()
        if past_dgs:
            outputs.newpage()
            outputs.output_heading(2, "Past District Governors")
            outputs.start_multicols()
            for po in past_dgs:
                outputs.output_past_officer(po)
            outputs.end_multicols()

        past_dgs = data.get_past_foreign_dgs()
        if past_dgs:
            outputs.output_heading(2, "Past District Governors From Other Districts")
            outputs.start_multicols()
            for po in past_dgs:
                if not po.member.is_resigned:
                    outputs.output_past_officer(po)
            outputs.end_multicols()
    return outputs


def get_default_year():
    dt = datetime.now()
    year = dt.year
    if dt.month <= 4:
        year -= 1
    return year


if __name__ == "__main__":
    import argparse

    year = get_default_year()
    parser = argparse.ArgumentParser(
        "build_md_directory",
        description="Build a directory for a specified MD or District",
    )
    parser.add_argument(
        "md_or_dist", help='The name of the MD or district to use, eg "410"'
    )
    parser.add_argument(
        "--year",
        type=int,
        default=year,
        help=f"The year to build directories for. Defaults to {year}/{year+1}",
    )
    args = parser.parse_args()
    import time

    outputs = get_outputs(args.year, args.md_or_dist)
    print(f"Get outputs: {time.process_time():.3}")
    outputs.build()
    print(f"outputs built: {time.process_time():.3}")
