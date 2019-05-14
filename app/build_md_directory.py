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
    out.append(f"### {off.year}")
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

out.append('## Past Council Chairpersons')
out.append('')
out.extend(['\Begin{multicols}{2}', '\setlength{\columnseprule}{0.4pt}', ''])
out.append('')
for po in data.get_past_ccs():
    output_past_officer(po)
out.extend(['', '\End{multicols}', ''])

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(out))
    



