import filter_and_build

import copy
import itertools

import db_handler

def get_md_officers():
    offs = []
    for off in data.struct.officers:
        if 'Council Chairperson' == off.title:
            offs.append(off)
            break
    dgs = []
    vdgs = []
    titles = {'District Governor': dgs,
              'First Vice District Governor': vdgs}
    while data.next_district():
        for off in data.district.officers:
            if off.title in titles:
                o = copy.copy(off)
                o.title = f"{off.title}, District {data.district.name}"
                titles[off.title].append(o)
    offs.extend(dgs)
    offs.extend(vdgs)
    for off in data.struct.officers:
        if 'Council Chairperson' != off.title:
            offs.append(off)
    return offs

class Output(object):
    ''' Hold state for the output lines
    '''
    def __init__(self):
        self.out = []

    def __output_region_zone(self, children, chair, child_desc, chair_desc):
        if not chair:
            chair_rows = ['Position Vacant']
        else:
            chair_rows = self.get_member_rows(chair, trail=False)
        self.out.append(f'|{child_desc}|{chair_desc}|')
        self.out.append('|:----|:----|')
        for (child,cr) in itertools.zip_longest([c.name for c in children], chair_rows, fillvalue=''):
            self.out.append(f'|{child}|{cr}|')
        self.out.append('')

    def newpage(self):
        self.out.append(r'\newpage')
        
    def blank(self):
        self.out.append('')
        
    def vacant(self):
        self.out.extend(['Position Vacant', ''])
        
    def get_member_rows(self, member, trail=True, include_homeclub=True):
        if trail:
            t = ' \\'
        else:
            t = ''
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
                parent = f"Club of {club.parent.name}" if club.parent else ''
                name = f"{name} ({club.club_type.name.capitalize()} {parent})"
            self.output_heading(3, name)
            if club.charter_year:
                title = 'Chartered' if club.club_type == db_handler.ClubType.lions else 'Established'
                year = f"{title}: {club.charter_year}. "
            else:
                year = ''
            if club.zone:
                s = f"{year}Part of {club.zone.long_name}."
            else:
                s = ''
            if s:
                self.out.append(s)
            officers = []
            for off in club.officers:
                if 'membership chair' not in off.title.lower():
                    if off.member:
                        l = [off.title.replace('Club ', '').replace('Chairperson', 'Chair'), '--']
                        l.extend(self.get_member_rows(off.member, trail=False, include_homeclub=False))
                        officers.append(l)
            if officers:
                self.blank()
                for row in itertools.zip_longest(*officers, fillvalue=''):
                    self.out.append(f"|{'|'.join(row)}|")
            meeting = []
            if club.meeting_time:
                meeting.append(club.meeting_time)
            if club.meeting_address:
                meeting.append(', '.join(club.meeting_address))
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
        self.out.append('\\ ')
        self.out.append('')

    def output_past_officer(self, off):
        year = f"{off.year-1}/{off.year}"
        if hasattr(off, 'previous_district'):
            if off.previous_district:
                year = f"{year} (xxSI {off.previous_district.long_name})"
        self.out.append(f"### {year} {{-}}")
        self.output_member(off.member)
        self.out.append('\\ ')
        self.out.append('')

    def output_region(self, clubs, chair):
        self.__output_region_zone(clubs, chair, 'Zones',  'Region Chair')

    def output_zone(self, clubs, chair):
        self.__output_region_zone(clubs, chair, 'Clubs', 'Zone Chair')

    def start_multicols(self):
        self.out.extend(['\\Begin{multicols}{2}', '\\setlength{\\columnseprule}{0.4pt}', ''])

    def end_multicols(self):
        self.out.extend(['', '\\End{multicols}', ''])

    def output_struct_preamble(self, struct): 
        self.out.extend([f"# {struct.long_name}", ''])
        
    def output_heading(self, level, heading):
        self.out.extend([f"{'#' * level } {heading}", ''])

    def output_md_past_council_chairs_header(self):
        self.out.extend([f"## Past Council Chairpersons", ''])

    def output_website(self, website):
        self.out.append('## Website')
        self.out.append(f"<{website}>")
        self.out.append('')

    def output_brightsight_office(self, bso):
        self.out.append('## Lions Brightsight Office')
        self.out.append('')
        self.out.append('### Contact Details')
        self.out.append('')
        self.out.append('|||')
        self.out.append('|----:|:----|')
        self.out.append(f'|Contact Person:|{bso.contact_person}|')
        if bso.physical_address:
            self.out.append(f'|Physical Address:|{bso.physical_address[0]}|')
            for pa in bso.physical_address[1:]:
                self.out.append(f'||{pa}|')
        if bso.postal_address:
            self.out.append(f'|Postal Address:|{bso.postal_address[0]}|')
            for pa in bso.postal_address[1:]:
                self.out.append(f'||{pa}|')
        if bso.ph:
            self.out.append(f'|Telephone:|{bso.ph}|')
        if bso.email:
            self.out.append(f'|Email:|<{bso.email}>|')
        if bso.website:
            self.out.append(f'|Website:|<{bso.website}>|')
        self.out.append('')

        if bso.manager:
            self.out.append('### Manager')
            self.out.append('')
            self.out.append('|||')
            self.out.append('|----:|:----|')
            self.out.append(f'|Manager:|{bso.manager.name}|')
            if bso.manager.ph:
                self.out.append(f'|Phone:|{bso.manager.ph}|')
            if bso.manager.email:
                self.out.append(f'|Email:|<{bso.manager.email}>|')
            self.out.append('')
        
data = db_handler.Data(2019, '410')
output = Output()
output.output_struct_preamble(data.struct)
output.output_heading(2, "Multiple District Council")
output.start_multicols()
for off in get_md_officers():
    output.output_officer(off)
output.end_multicols()
output.output_website(data.struct.website)
bso = data.get_brightsight_offices()
if bso:
    output.output_brightsight_office(bso)
past_ccs = data.get_past_ccs()
if past_ccs:
    output.output_heading(2, "Past Council Chairs")
    output.start_multicols()
    for po in past_ccs:
        output.output_past_officer(po)
    output.end_multicols()

data.reset()
while data.next_district():
    output.newpage()
    output.output_struct_preamble(data.district)
    output.output_heading(2, "District Cabinet")
    output.start_multicols()
    for off in data.district.officers:
        output.output_officer(off)
    output.end_multicols()

    if data.district.website:
        output.output_website(data.district.website)

    if data.zones:
        output.output_heading(2, "Regions")
        while data.next_region():
            output.output_heading(3, data.region.name)
            zones = data.get_region_zones(include_officers=False)
            if zones or data.region.chair:
                output.output_region(zones, data.region.chair)

    if data.zones:
        output.output_heading(2, "Zones")
        while data.next_zone():
            output.output_heading(3, data.zone.name)
            clubs = data.get_zone_clubs(include_officers=False)
            if clubs or data.zone.chair:
                output.output_zone(clubs, data.zone.chair)
    data.reset_district()
    
    clubs = [club for club in data.get_district_clubs() if not club.is_closed]
    if clubs:
        output.output_heading(2, "Clubs")
        for club in clubs:
            output.output_club(club)

    past_dgs = data.get_past_dgs()
    if past_dgs:
        output.output_heading(2, "Past District Governors")
        output.start_multicols()
        for po in past_dgs:
            output.output_past_officer(po)
        output.end_multicols()

    past_dgs = data.get_past_foreign_dgs()
    if past_dgs:
        output.output_heading(2, "Past District Governors From Other Districts")
        output.start_multicols()
        for po in past_dgs:
            if not po.member.is_resigned:
                output.output_past_officer(po)
        output.end_multicols()

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(output.out))
    
filter_and_build.build_pdf('output.txt')
