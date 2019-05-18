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
        
    def get_member_rows(self, member, trail=True):
        if trail:
            t = ' \\'
        else:
            t = ''
        out = []
        out.append(f"{member.long_name}{t}")
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
        if member.club:
            out.append(f"**Home Club:** {member.club.name}{t}")
        return out

    def output_member(self, member):
        if member:
            self.out.extend(self.get_member_rows(member))

    def output_officer(self, off):
        self.out.append(f"### {off.title}")
        self.output_member(off.member)
        self.out.append('\\ ')
        self.out.append('')

    def output_past_officer(self, off):
        year = f"{off.year-1}/{off.year}"
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
        
    def output_subtitle(self, title):
        self.out.extend([f"## {title}", ''])

    def output_subsubtitle(self, title):
        self.out.extend([f"### {title}", ''])

    def output_subsubsubtitle(self, title):
        self.out.extend([f"#### {title}", ''])

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
output.output_subtitle("Multiple District Council")
output.start_multicols()
for off in get_md_officers():
    output.output_officer(off)
output.end_multicols()
output.output_website(data.struct.website)
bso = data.get_brightsight_offices()
if bso:
    output.output_brightsight_office(bso)
output.output_subtitle("District Cabinet")
output.start_multicols()
for po in data.get_past_ccs():
    output.output_past_officer(po)
output.end_multicols()

data.reset()
while data.next_district():
    output.newpage()
    output.output_struct_preamble(data.district)
    output.start_multicols()
    for off in data.district.officers:
        output.output_officer(off)
    output.end_multicols()

    if data.district.website:
        output.output_website(data.district.website)

    if data.zones:
        output.output_subtitle("Regions")
        while data.next_region():
            output.output_subsubtitle(data.region.name)
            zones = data.get_region_zones(include_officers=False)
            if zones or data.region.chair:
                output.output_region(zones, data.region.chair)

    if data.zones:
        output.output_subtitle("Zones")
        while data.next_zone():
            output.output_subsubtitle(data.zone.name)
            clubs = data.get_zone_clubs(include_officers=False)
            if clubs or data.zone.chair:
                output.output_zone(clubs, data.zone.chair)
    data.reset_district()

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(output.out))
    
filter_and_build.build_pdf('output.txt')
