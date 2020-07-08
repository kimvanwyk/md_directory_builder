import db_handler

from collections import defaultdict
import sys

import sqlalchemy as sa
from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
)


STRUCT = "410W"
YEAR = 2020


def get_members(club_id=None, struct=STRUCT, year=YEAR):
    data = db_handler.get_data_object_from_db(year, struct)
    tm = data.db.tables["member"]
    tc = data.db.tables["club"]
    wheres = [
        tm.c.club_id == tc.c.id,
        tc.c.struct_id == data.struct_id,
        tc.c.closed_b == False,
        tc.c.type == 0,
    ]
    if club_id:
        wheres.append(tc.c.id == club_id)
    res = data.db.conn.execute(
        sa.select([tm, tc.c.name.label("club")], sa.and_(*wheres))
    ).fetchall()
    members = [
        (m["last_name"], m["first_name"], m["id"], m["club_id"], m["club"]) for m in res
    ]
    members.sort()
    return members


def build_members_dict():
    members = get_members()
    d = defaultdict(list)
    for m in members:
        if m[-1]:
            d[m[-1]].append(m)
    return d


class Form(QDialog):
    def __init__(self, parent=None, club_index=-1):
        super(Form, self).__init__(parent)
        self.setWindowTitle("Officer Selector")
        self.setMinimumSize(400, 200)
        self.members_dict = build_members_dict()
        self.clubs = list(self.members_dict.keys())
        self.clubs.sort()
        self.club_index = club_index

        layout = QVBoxLayout()
        self.club_label = QLabel("")
        layout.addWidget(self.club_label)
        self.combos = []
        for name in ("president", "secretary", "treasurer"):
            inner = QHBoxLayout()
            layout.addLayout(inner)
            inner.addWidget(QLabel(name.capitalize()))
            c = QComboBox()
            c.setMinimumSize(300, 30)
            setattr(self, f"{name}_combo", c)
            self.combos.append(c)
            inner.addWidget(c)
        self.next_btn = QPushButton("Next Club")
        self.next_btn.clicked.connect(self.insert_officers)
        layout.addWidget(self.next_btn)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        self.setLayout(layout)

        self.next_club()

        self.db = db_handler.get_data_object_from_db(YEAR, STRUCT).db
        self.officer_table = self.db.tables["clubofficer"]

    def next_club(self):
        self.club_index += 1
        if self.club_index == len(self.clubs):
            raise IndexError
        self.club = self.clubs[self.club_index]
        self.members = self.members_dict[self.club]
        self.club_label.setText(self.club)
        self.set_combos()
        self.president_combo.setFocus()

    def set_combos(self):
        for c in self.combos:
            c.clear()
            c.addItems([f"{m[0]}, {m[1]}" for m in self.members])
            c.addItem("NONE")

    def refresh(self):
        self.members = get_members(club_id=self.members[0][-2])
        self.set_combos()

    def insert_officers(self):
        vals = []
        for (n, name) in enumerate(("president", "secretary", "treasurer"), 1):
            c = getattr(self, f"{name}_combo")
            i = c.currentIndex()
            if i < len(self.members):
                m = self.members[i]
                vals.append(
                    {
                        "year": YEAR,
                        "club_id": m[-2],
                        "member_id": m[-3],
                        "office_id": n,
                        "email": "",
                        "add1": "",
                        "add2": "",
                        "add3": "",
                        "add4": "",
                        "po_code": "",
                        "phone": "",
                        "fax": "",
                    }
                )
        if vals:
            print(vals)
            self.db.conn.execute(self.officer_table.insert(vals))
            self.next_club()


def main():
    app = QApplication(sys.argv)
    form = Form(club_index=3)
    form.show()
    sys.exit(app.exec_())


main()
