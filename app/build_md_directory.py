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

def output_member(member):
    out.append(f"{member.long_name} \\")
    if member.is_deceased:
        out.append(f"**Called to Higher Service** \\")
        return
    if member.is_resigned:
        out.append(f"**Resigned** \\")
        return
    if member.cell_ph:
        out.append(f"**Cell:** {member.cell_ph} \\")
    if member.email:
        out.append(f"**Email:** <{member.email}> \\")
    if member.club:
        out.append(f"**Home Club:** {member.club.name} \\")

def output_officer(off):
    out.append(f"### {off.title}")
    output_member(off.member)
    out.append('\\ \\ ')
    out.append('')

def output_past_officer(off):
    year = f"{off.year-1}/{off.year}"
    out.append(f"### {year} {{-}}")
    output_member(off.member)
    out.append('\\ \\ ')
    out.append('')

data = db_handler.Data(2019, '410')
 
out = [f"# {data.struct.long_name}", '', '## Multiple District Council', '',
       '\Begin{multicols}{2}', '\setlength{\columnseprule}{0.4pt}', '']

for off in get_md_officers():
    output_officer(off)

out.extend(['', '\End{multicols}', ''])

out.append('## Website')
out.append(f"<{data.struct.website}>")
out.append('')

bso = data.get_brightsight_offices()
if bso:
    out.append('## Lions Brightsight Office')
    out.append('')
    out.append('### Contact Details')
    out.append('')
    out.append('|||')
    out.append('|----:|:----|')
    out.append(f'|Contact Person|{bso.contact_person}|')
    if bso.physical_address:
        out.append(f'|Physical Address|{bso.physical_address[0]}|')
        for pa in bso.physical_address[1:]:
            out.append(f'||{pa}|')
    if bso.postal_address:
        out.append(f'|Postal Address|{bso.postal_address[0]}|')
        for pa in bso.postal_address[1:]:
            out.append(f'||{pa}|')
    if bso.ph:
        out.append(f'|Telephone|{bso.ph}|')
    if bso.email:
        out.append(f'|Email|<{bso.email}>|')
    if bso.website:
        out.append(f'|Website|<{bso.website}>|')
    out.append('')

    if bso.manager:
        out.append('### Manager')
        out.append('')
        out.append('|||')
        out.append('|----:|:----|')
        out.append(f'|Manager|{bso.manager.name}|')
        if bso.manager.ph:
            out.append(f'|Phone|{bso.manager.ph}|')
        if bso.manager.email:
            out.append(f'|Email|<{bso.manager.email}>|')
        out.append('')


out.append('## Past Council Chairpersons')
out.append('')
out.extend(['\Begin{multicols}{2}', '\setlength{\columnseprule}{0.4pt}', ''])
out.append('')
for po in data.get_past_ccs():
    output_past_officer(po)
out.extend(['', '\End{multicols}', ''])

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(out))
    



