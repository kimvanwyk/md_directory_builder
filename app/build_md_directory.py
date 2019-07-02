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

    def __getattr__(self, name):
        def method(*args, **kwds):
            getattr(self.outputs[0], name)(*args, **kwds)
            if len(self.outputs) > 1:
                getattr(self.outputs[-1], name)(*args, **kwds)

        return method


class Output(object):

    year = None
    dt = None

    """ Hold state for the output lines
    """

    def __init__(self, title):
        self.out = []
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
            if not any([e in f for e in ext_keep]):
                os.remove(f)

    def __output_aligned_left_column_row(self, left, right, align='l', left_column_width=LEFT_COLUMN_WIDTH):
        a = getattr(left, f"{align}just")
        if left:
            l = a(left_column_width,NON_BREAKING_CHAR_PLACEHOLDER).replace(NON_BREAKING_CHAR_PLACEHOLDER, NON_BREAKING_SPACE)
        else:
            l = left
        if right:
            r = right.ljust(RIGHT_COLUMN_WIDTH,NON_BREAKING_CHAR_PLACEHOLDER).replace(NON_BREAKING_CHAR_PLACEHOLDER, NON_BREAKING_SPACE)
        else:
            r = right
        self.out.append(
            f"|{l}|{r}|"
        )

    def __output_region_zone(self, children, chair, child_desc, chair_desc):
        if not chair:
            chair_rows = ["Position Vacant"]
        else:
            chair_rows = self.get_member_rows(chair, trail=False)
        self.__output_aligned_left_column_row(child_desc, chair_desc)
        self.out.append("|:----|:----|")
        for (child, cr) in itertools.zip_longest(
            [getattr(c, 'full_name', c.name) for c in children], chair_rows, fillvalue=""
        ):
            # self.__output_aligned_left_column_row(child, cr)
            self.out.append(f"|{child}|{cr}|")
        self.out.append("")

    def newpage(self):
        self.out.append(r"\newpage")

    def blank(self):
        self.out.append("")

    def vacant(self):
        self.out.extend(["Position Vacant", ""])

    def get_member_rows(self, member, trail=True, include_homeclub=True):
        if trail:
            t = " \\"
        else:
            t = ""
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
            out.append(f"**Email:** <{member.email}>{t}")
        if include_homeclub and member.club:
            out.append(f"**Home Club:** {member.club.name}{t}")
        return out

    def output_member(self, member):
        if member:
            self.out.extend(self.get_member_rows(member))

    def output_club(self, club):
        if club.name:
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
            if club.zone:
                s = f"{year}Part of {club.zone.long_name}."
            else:
                s = year
            if club.id > 0:
                s = f"{s} Club Number: {club.id}."
            if s:
                self.out.append(s)
            officers = []
            for off in club.officers:
                if "membership chair" not in off.title.lower():
                    if off.member:
                        l = [
                            off.title.replace("Club ", "").replace(
                                "Chairperson", "Chair"
                            ),
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
        if hasattr(off, "previous_district"):
            if off.previous_district:
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
            ["\\Begin{multicols}{2}", "\\setlength{\\columnseprule}{0.4pt}", ""]
        )

    def end_multicols(self):
        self.out.extend(["", "\\End{multicols}", ""])

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
        self.__output_aligned_left_column_row("Contact Person:", bso.contact_person, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        if bso.physical_address:
            self.__output_aligned_left_column_row("Physical Address:", bso.physical_address[0], 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
            for pa in bso.physical_address[1:]:
                self.__output_aligned_left_column_row("", pa, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        if bso.postal_address:
            self.__output_aligned_left_column_row("Postal Address:", bso.postal_address[0], 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
            for pa in bso.postal_address[1:]:
                self.__output_aligned_left_column_row("", pa, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        if bso.ph:
            self.__output_aligned_left_column_row("Telephone:", bso.ph, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        if bso.email:
            self.__output_aligned_left_column_row("Email:", f"<{bso.email}>", 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        if bso.website:
            self.__output_aligned_left_column_row("Website:", f"<{bso.website}>", 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
        self.out.append("")

        if bso.manager:
            self.out.append("### Manager")
            self.out.append("")
            self.out.append("|||")
            self.out.append("|----:|:----|")
            self.__output_aligned_left_column_row("Manager:", bso.manager.name, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
            if bso.manager.ph:
                self.__output_aligned_left_column_row("Phone:", bso.manager.ph, 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
            if bso.manager.email:
                self.__output_aligned_left_column_row("Email:", f"<{bso.manager.email}>", 'r', BRIGHTSIGHT_LEFT_COLUMN_WIDTH)
            self.out.append("")


def get_outputs(year, struct_name):
    data = db_handler.get_data_object_from_db(year, struct_name)
    Output.year = year
    Output.dt = datetime.now()
    outputs = Outputs()
    if data.md:
        outputs.add_output(Output(f"Multiple District {data.struct.name}"))
        outputs.output_struct_preamble(data.struct)
        outputs.output_heading(2, "Multiple District Council")
        outputs.start_multicols()
        for off in get_md_officers(data):
            outputs.output_officer(off)
        outputs.end_multicols()
        outputs.output_website(data.struct.website)
        bso = data.get_brightsight_offices()
        if bso:
            outputs.output_brightsight_office(bso)
        past_ccs = data.get_past_ccs()
        if past_ccs:
            outputs.output_heading(2, "Past Council Chairs")
            outputs.start_multicols()
            for po in past_ccs:
                outputs.output_past_officer(po)
            outputs.end_multicols()

    data.reset()
    while data.next_district():
        outputs.outputs[0].newpage()
        outputs.add_output(Output(f"District {data.district.name}"))
        outputs.output_struct_preamble(data.district)
        outputs.output_heading(2, "District Cabinet")
        outputs.start_multicols()
        for off in data.district.officers:
            outputs.output_officer(off)
        outputs.end_multicols()

        if data.district.website:
            outputs.output_website(data.district.website)

        if data.regions:
            outputs.output_heading(2, "Regions")
            while data.next_region():
                outputs.output_heading(3, data.region.name)
                zones = data.get_region_zones(include_officers=False)
                if zones or data.region.chair:
                    outputs.output_region(zones, data.region.chair)

        if data.zones:
            outputs.output_heading(2, "Zones")
            while data.next_zone():
                name = data.zone.name
                if data.zone.region:
                    name =f"{name} ({data.zone.region.name})"
                outputs.output_heading(3, name)
                clubs = data.get_zone_clubs(include_officers=False)
                if clubs or data.zone.chair:
                    outputs.output_zone(clubs, data.zone.chair)
        data.reset_district()

        clubs = [club for club in data.get_district_clubs() if not club.is_closed]
        if clubs:
            outputs.output_heading(2, "Clubs")
            for club in clubs:
                outputs.output_club(club)

        past_dgs = data.get_past_dgs()
        if past_dgs:
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
    parser = argparse.ArgumentParser("build_md_directory", description="Build a directory for a specified MD or District")
    parser.add_argument("md_or_dist", help='The name of the MD or district to use, eg "410"')
    parser.add_argument("--year", type=int, default=year, help=f'The year to build directories for. Defaults to {year}/{year+1}')
    args = parser.parse_args()
    outputs = get_outputs(args.year, args.md_or_dist)
    outputs.build()
