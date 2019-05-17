import filter_and_build

import copy

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

    def output_member(self, member):
        self.out.append(f"{member.long_name} \\")
        if member.is_deceased:
            self.out.append(f"**Called to Higher Service** \\")
            return
        if member.is_resigned:
            self.out.append(f"**Resigned** \\")
            return
        if member.cell_ph:
            self.out.append(f"**Cell:** {member.cell_ph} \\")
        if member.email:
            self.out.append(f"**Email:** <{member.email}> \\")
        if member.club:
            self.out.append(f"**Home Club:** {member.club.name} \\")

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

    def start_multicols(self):
        self.out.extend(['\\Begin{multicols}{2}', '\\setlength{\\columnseprule}{0.4pt}', ''])

    def end_multicols(self):
        self.out.extend(['', '\\End{multicols}', ''])

    def output_md_preamble(self, md): 
        self.out.extend([f"# {md.long_name}", ''])
        
    def output_md_council_header(self):
        self.out.extend([f"## Multiple District Council", ''])

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
output.output_md_preamble(data.struct)
output.output_md_council_header()
output.start_multicols()
for off in get_md_officers():
    output.output_officer(off)
output.end_multicols()
output.output_website(data.struct.website)
bso = data.get_brightsight_offices()
if bso:
    output.output_brightsight_office(bso)
output.output_md_past_council_chairs_header()
output.start_multicols()
for po in data.get_past_ccs():
    output.output_past_officer(po)
output.end_multicols()

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(output.out))
    
filter_and_build.build_pdf('output.txt')
