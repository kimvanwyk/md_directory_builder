import db_handler
import pyperclip

from rich import print

data = db_handler.get_data_object_from_db(2026, "410")

offs = []
for off in data.struct.officers:
    offs.append(
        (
            off.title.upper(),
            f"{off.member.first_name} {off.member.last_name}",
            off.member.club.name,
            off.member.club.zone.district.name,
            off.member.email,
        )
    )

out = []
for position, name, club, district, email in offs:
    out.append(
        f'<tr><td class="body-item mbr-fonts-style display-7">{position}</td><td class="body-item mbr-fonts-style display-7">{name}</td><td class="body-item mbr-fonts-style display-7">{club}</td><td class="body-item mbr-fonts-style display-7">{district}</td><td class="body-item mbr-fonts-style display-7"><a href="mailto:{email}" class="text-black">Email</a></td></tr>'
    )

pyperclip.copy("\n".join(out))
