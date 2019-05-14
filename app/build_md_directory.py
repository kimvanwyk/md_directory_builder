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

def output_officer(off):
    out.append(f"### {off.title}")
    out.append(f"{off.member.long_name} \\")
    if off.member.cell_ph:
        out.append(f"**Cell:** {off.member.cell_ph} \\")
    if off.member.email:
        out.append(f"**Email:** <{off.member.email}> \\")
    if off.member.club:
        out.append(f"**Home Club:** {off.member.club.name} \\")
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

with open('output.txt', 'w') as fh:
    fh.write('\n'.join(out))
    



