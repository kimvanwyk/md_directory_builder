import csv

import db_handler

import pyperclip

OFFICERS = {
    "Club President": 1,
    "Club Secretary": 2,
    "Club Treasurer": 3,
    "Club Membership Chairperson": 4,
}

MAPPINGS = {"club_id": "Club ID", "member_id": "Member ID"}


def extract_rows(csv_file, year):
    rows = []
    with open(csv_file, "r") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["Title"] in OFFICERS:
                rows.append({k: int(row[v]) for (k, v) in MAPPINGS.items()})
                rows[-1]["office_id"] = OFFICERS[row["Title"]]
                rows[-1]["year"] = year
                for k in (
                    "add1",
                    "add2",
                    "add3",
                    "add4",
                    "po_code",
                    "phone",
                    "fax",
                    "email",
                ):
                    rows[-1][k] = ""
    return rows


def insert_rows(rows, year):
    db = db_handler.get_data_object_from_db(year, "410").db
    tm = db.tables["clubofficer"]
    db.conn.execute(tm.insert(rows))


def find_missing_members(csv_file, year):
    data = db_handler.get_data_object_from_db(year, "410")
    members = data.db.get_members()
    with open(csv_file, "r") as fh:
        reader = csv.DictReader(fh)
        seen = []
        new_members = []
        for row in reader:
            m_id = int(row["Member ID"])
            if m_id not in members and m_id not in seen:
                seen.append(m_id)
                nm = [row["Member ID"], row["Club ID"]]
                for k in ("First Name", "Last Name", "Email", "Cell Phone"):
                    nm.append(f'"{row[k]}"')
                spouse = row["Spouse Name"].split(" ")[0]
                nm.append(f'"{spouse}"')
                new_members.append(nm)
        out = [
            "INSERT INTO md_directory_members (id, club_id, first_name, last_name, email, cell_ph, partner) VALUES"
        ]
        for nm in new_members:
            out.append(f'({", ".join(nm)}),')
    pyperclip.copy("\n".join(out))


def find_missing_clubs(csv_file, year):
    data = db_handler.get_data_object_from_db(year, "410")
    clubs = data.db.get_clubs()
    with open(csv_file, "r") as fh:
        reader = csv.DictReader(fh)
        seen = []
        for row in reader:
            c_id = int(row["Club ID"])
            if c_id not in clubs and c_id not in seen:
                seen.append(c_id)
                print(f"{c_id} {row['Club Name']}")


FN = "/home/kimv/src/md_directory/data/2023/mylci_datadownload_20230624_081613.csv"
rows = extract_rows(FN, 2023)
if 1:
    print(rows[:10])
    print(rows[-10:])
    insert_rows(rows, 2023)
if 0:
    sql = find_missing_members(FN, 2023)
    print(sql)
if 0:
    find_missing_clubs(FN, 2023)
