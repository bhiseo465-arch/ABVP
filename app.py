from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st


APP_TITLE = "ABVP Thane Mahanagar Karyalay"
DATA_DIR = Path("data")

COLLEGES = [
    "Bedekar College",
    "B. N. Bandodkar College",
    "K. G. Joshi College",
    "Smt. C. H. M. College",
    "Satish Pradhan Dnyanasadhana College",
    "Vaze Kelkar College",
    "Other",
]

BHAGS = ["Thane East", "Thane West", "Kalwa", "Mumbra", "Kopri", "Wagle Estate", "Other"]

STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]

GRIEVANCE_COLUMNS = [
    "id",
    "created_at",
    "student_name",
    "phone",
    "college",
    "issue_type",
    "description",
    "priority",
    "status",
    "assigned_to",
    "follow_up_date",
    "resolution_notes",
]

MEMBER_COLUMNS = [
    "id",
    "created_at",
    "name",
    "phone",
    "college",
    "course",
    "year",
    "bhag",
    "role",
    "membership_fee",
    "receipt_no",
]

MEETING_COLUMNS = [
    "id",
    "created_at",
    "meeting_date",
    "title",
    "venue",
    "agenda",
    "attendees",
    "decisions",
    "tasks",
]

TASK_COLUMNS = [
    "id",
    "created_at",
    "task",
    "owner",
    "related_area",
    "deadline",
    "priority",
    "status",
    "notes",
]

INVENTORY_COLUMNS = [
    "id",
    "created_at",
    "item",
    "category",
    "quantity",
    "minimum_required",
    "location",
    "last_updated",
    "notes",
]

LETTER_COLUMNS = [
    "id",
    "created_at",
    "letter_type",
    "recipient_name",
    "recipient_designation",
    "institution",
    "subject",
    "body",
    "prepared_by",
]


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📋", layout="wide")
    ensure_storage()
    render_header()

    page = st.sidebar.radio(
        "Workspace",
        [
            "Dashboard",
            "Student Help Desk",
            "Membership",
            "Meetings & MoM",
            "Letters / Nivedan",
            "Inventory",
            "Task Tracker",
            "Data Export",
        ],
    )
    render_sidebar_delete_tools()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Student Help Desk":
        render_help_desk()
    elif page == "Membership":
        render_membership()
    elif page == "Meetings & MoM":
        render_meetings()
    elif page == "Letters / Nivedan":
        render_letters()
    elif page == "Inventory":
        render_inventory()
    elif page == "Task Tracker":
        render_tasks()
    else:
        render_export()


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    ensure_csv("grievances.csv", GRIEVANCE_COLUMNS)
    ensure_csv("members.csv", MEMBER_COLUMNS)
    ensure_csv("meetings.csv", MEETING_COLUMNS)
    ensure_csv("tasks.csv", TASK_COLUMNS)
    ensure_csv("inventory.csv", INVENTORY_COLUMNS)
    ensure_csv("letters.csv", LETTER_COLUMNS)


def ensure_csv(filename: str, columns: Iterable[str]) -> None:
    path = DATA_DIR / filename
    if not path.exists():
        pd.DataFrame(columns=list(columns)).to_csv(path, index=False)


def read_table(filename: str, columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / filename
    df = pd.read_csv(path, dtype=str).fillna("")
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df[columns]


def write_table(filename: str, df: pd.DataFrame) -> None:
    df.to_csv(DATA_DIR / filename, index=False)


def append_row(filename: str, columns: list[str], row: dict[str, object]) -> None:
    df = read_table(filename, columns)
    row_with_defaults = {column: str(row.get(column, "")) for column in columns}
    write_table(filename, pd.concat([df, pd.DataFrame([row_with_defaults])], ignore_index=True))


def next_id(df: pd.DataFrame, prefix: str) -> str:
    if df.empty:
        return f"{prefix}-001"
    numeric_ids = (
        df["id"]
        .astype(str)
        .str.extract(r"(\d+)$")[0]
        .dropna()
        .astype(int)
    )
    next_number = 1 if numeric_ids.empty else int(numeric_ids.max()) + 1
    return f"{prefix}-{next_number:03d}"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def render_header() -> None:
    st.title(APP_TITLE)
    st.caption("Local-first automation tool for karyalay administration, student follow-up, and reporting.")


def render_dashboard() -> None:
    grievances = read_table("grievances.csv", GRIEVANCE_COLUMNS)
    members = read_table("members.csv", MEMBER_COLUMNS)
    tasks = read_table("tasks.csv", TASK_COLUMNS)
    inventory = read_table("inventory.csv", INVENTORY_COLUMNS)

    open_grievances = grievances[~grievances["status"].isin(["Resolved", "Closed"])]
    open_tasks = tasks[~tasks["status"].isin(["Resolved", "Closed", "Done"])]
    low_stock = inventory[
        pd.to_numeric(inventory["quantity"], errors="coerce").fillna(0)
        <= pd.to_numeric(inventory["minimum_required"], errors="coerce").fillna(0)
    ]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Open grievances", len(open_grievances))
    metric_cols[1].metric("Total members", len(members))
    metric_cols[2].metric("Open tasks", len(open_tasks))
    metric_cols[3].metric("Low stock items", len(low_stock))

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Grievances by Status")
        if grievances.empty:
            st.info("No grievances recorded yet.")
        else:
            st.bar_chart(grievances["status"].value_counts())

        st.subheader("Membership by College")
        if members.empty:
            st.info("No members recorded yet.")
        else:
            st.bar_chart(members["college"].value_counts().head(10))

    with right:
        st.subheader("Urgent Follow-ups")
        urgent = open_grievances[
            open_grievances["priority"].isin(["High", "Urgent"])
        ][["id", "student_name", "college", "priority", "assigned_to", "follow_up_date"]]
        st.dataframe(urgent, use_container_width=True, hide_index=True)

        st.subheader("Inventory Alerts")
        st.dataframe(
            low_stock[["item", "category", "quantity", "minimum_required", "location"]],
            use_container_width=True,
            hide_index=True,
        )


def get_datasets() -> dict[str, tuple[str, list[str]]]:
    return {
        "Grievances": ("grievances.csv", GRIEVANCE_COLUMNS),
        "Members": ("members.csv", MEMBER_COLUMNS),
        "Meetings": ("meetings.csv", MEETING_COLUMNS),
        "Tasks": ("tasks.csv", TASK_COLUMNS),
        "Inventory": ("inventory.csv", INVENTORY_COLUMNS),
        "Letters": ("letters.csv", LETTER_COLUMNS),
    }


def render_sidebar_delete_tools() -> None:
    with st.sidebar.expander("Delete stored data"):
        datasets = get_datasets()
        selected_dataset = st.selectbox("Dataset", list(datasets.keys()), key="sidebar_delete_dataset")
        filename, columns = datasets[selected_dataset]
        df = read_table(filename, columns)

        if df.empty:
            st.caption("No records in this dataset.")
            return

        selected_id = st.selectbox(
            "Record",
            df["id"].astype(str).tolist(),
            key="sidebar_delete_record",
        )
        confirm_record = st.checkbox(
            f"Confirm deleting {selected_id}",
            key="sidebar_confirm_record_delete",
        )
        if st.button("Delete selected", disabled=not confirm_record, key="sidebar_delete_selected"):
            write_table(filename, df[df["id"].astype(str) != selected_id])
            st.success("Record deleted.")
            st.rerun()

        confirm_all = st.text_input("Type DELETE ALL to clear dataset", key="sidebar_confirm_all_delete")
        if st.button("Clear dataset", disabled=confirm_all != "DELETE ALL", key="sidebar_clear_dataset"):
            write_table(filename, pd.DataFrame(columns=columns))
            st.success("Dataset cleared.")
            st.rerun()


def render_help_desk() -> None:
    st.header("Student Help Desk")
    grievances = read_table("grievances.csv", GRIEVANCE_COLUMNS)

    with st.form("new_grievance", clear_on_submit=True):
        st.subheader("Register Student Grievance")
        col1, col2, col3 = st.columns(3)
        student_name = col1.text_input("Student name")
        phone = col2.text_input("Phone")
        college = col3.selectbox("College", COLLEGES)

        col4, col5, col6 = st.columns(3)
        issue_type = col4.selectbox(
            "Issue type",
            ["Admission", "Exam", "Fees", "Scholarship", "Transport", "Campus", "Other"],
        )
        priority = col5.selectbox("Priority", PRIORITIES, index=1)
        assigned_to = col6.text_input("Assigned to")

        description = st.text_area("Issue details")
        follow_up_date = st.date_input("Follow-up date", value=date.today() + timedelta(days=2))
        submitted = st.form_submit_button("Save grievance")

        if submitted:
            if not student_name or not phone or not description:
                st.error("Student name, phone, and issue details are required.")
            else:
                append_row(
                    "grievances.csv",
                    GRIEVANCE_COLUMNS,
                    {
                        "id": next_id(grievances, "GRV"),
                        "created_at": now_text(),
                        "student_name": student_name,
                        "phone": phone,
                        "college": college,
                        "issue_type": issue_type,
                        "description": description,
                        "priority": priority,
                        "status": "Assigned" if assigned_to else "Open",
                        "assigned_to": assigned_to,
                        "follow_up_date": follow_up_date.isoformat(),
                    },
                )
                st.success("Grievance saved.")
                st.rerun()

    st.subheader("Update Grievance")
    if grievances.empty:
        st.info("No grievances to update.")
    else:
        selected_id = st.selectbox("Select grievance", grievances["id"].tolist())
        selected = grievances[grievances["id"] == selected_id].iloc[0]
        with st.form("update_grievance"):
            col1, col2, col3 = st.columns(3)
            status = col1.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(selected["status"]) if selected["status"] in STATUSES else 0,
            )
            priority = col2.selectbox(
                "Priority",
                PRIORITIES,
                index=PRIORITIES.index(selected["priority"]) if selected["priority"] in PRIORITIES else 1,
            )
            assigned_to = col3.text_input("Assigned to", selected["assigned_to"])
            resolution_notes = st.text_area("Resolution notes", selected["resolution_notes"])
            update = st.form_submit_button("Update selected grievance")

            if update:
                mask = grievances["id"] == selected_id
                grievances.loc[mask, "status"] = status
                grievances.loc[mask, "priority"] = priority
                grievances.loc[mask, "assigned_to"] = assigned_to
                grievances.loc[mask, "resolution_notes"] = resolution_notes
                write_table("grievances.csv", grievances)
                st.success("Grievance updated.")
                st.rerun()

    st.subheader("Grievance Register")
    render_filterable_table(grievances, ["status", "college", "priority"])
    render_delete_controls("grievances.csv", GRIEVANCE_COLUMNS, "grievance")


def render_membership() -> None:
    st.header("Membership")
    members = read_table("members.csv", MEMBER_COLUMNS)

    with st.form("new_member", clear_on_submit=True):
        st.subheader("Add Member")
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("Name")
        phone = col2.text_input("Phone")
        college = col3.selectbox("College", COLLEGES)

        col4, col5, col6 = st.columns(3)
        course = col4.text_input("Course")
        year = col5.selectbox("Year", ["FY", "SY", "TY", "PG", "Other"])
        bhag = col6.selectbox("Bhag", BHAGS)

        col7, col8, col9 = st.columns(3)
        role = col7.selectbox("Role", ["Member", "College Karyakarta", "College Pramukh", "Bhag Team", "Mahanagar Team"])
        membership_fee = col8.number_input("Membership fee", min_value=0, value=10)
        receipt_no = col9.text_input("Receipt no.")

        submitted = st.form_submit_button("Save member")
        if submitted:
            if not name or not phone:
                st.error("Name and phone are required.")
            else:
                append_row(
                    "members.csv",
                    MEMBER_COLUMNS,
                    {
                        "id": next_id(members, "MEM"),
                        "created_at": now_text(),
                        "name": name,
                        "phone": phone,
                        "college": college,
                        "course": course,
                        "year": year,
                        "bhag": bhag,
                        "role": role,
                        "membership_fee": membership_fee,
                        "receipt_no": receipt_no,
                    },
                )
                st.success("Member saved.")
                st.rerun()

    st.subheader("Membership Register")
    render_filterable_table(members, ["college", "bhag", "role", "year"])
    render_delete_controls("members.csv", MEMBER_COLUMNS, "member")


def render_meetings() -> None:
    st.header("Meetings & Minutes")
    meetings = read_table("meetings.csv", MEETING_COLUMNS)

    with st.form("new_meeting", clear_on_submit=True):
        st.subheader("Create Meeting Record")
        col1, col2 = st.columns(2)
        meeting_date = col1.date_input("Meeting date", value=date.today())
        title = col2.text_input("Title", placeholder="Mahanagar Baithak")
        venue = st.text_input("Venue", placeholder="ABVP Thane Karyalay")
        agenda = st.text_area("Agenda points", placeholder="1. Membership review\n2. College issues\n3. Upcoming program")
        attendees = st.text_area("Attendees", placeholder="Names separated by commas")
        decisions = st.text_area("Decisions taken")
        tasks = st.text_area("Tasks assigned", placeholder="Task - Owner - Deadline")
        submitted = st.form_submit_button("Save minutes")

        if submitted:
            if not title or not agenda:
                st.error("Title and agenda are required.")
            else:
                append_row(
                    "meetings.csv",
                    MEETING_COLUMNS,
                    {
                        "id": next_id(meetings, "MTG"),
                        "created_at": now_text(),
                        "meeting_date": meeting_date.isoformat(),
                        "title": title,
                        "venue": venue,
                        "agenda": agenda,
                        "attendees": attendees,
                        "decisions": decisions,
                        "tasks": tasks,
                    },
                )
                st.success("Meeting saved.")
                st.rerun()

    st.subheader("Meeting Notice Generator")
    col1, col2, col3 = st.columns(3)
    notice_title = col1.text_input("Notice title", "Mahanagar Baithak")
    notice_date = col2.date_input("Notice date", value=date.today() + timedelta(days=1))
    notice_time = col3.time_input("Notice time")
    notice_venue = st.text_input("Notice venue", "ABVP Thane Karyalay")
    notice_agenda = st.text_area("Notice agenda", "1. Review pending student issues\n2. Membership planning\n3. Upcoming programs")
    notice = build_meeting_notice(notice_title, notice_date, notice_time, notice_venue, notice_agenda)
    st.text_area("Copy-ready meeting notice", notice, height=180)

    st.subheader("Meeting Register")
    st.dataframe(meetings, use_container_width=True, hide_index=True)
    render_delete_controls("meetings.csv", MEETING_COLUMNS, "meeting")


def render_letters() -> None:
    st.header("Letters / Nivedan")
    letters = read_table("letters.csv", LETTER_COLUMNS)

    with st.form("letter_form"):
        st.subheader("Generate Formal Letter")
        col1, col2 = st.columns(2)
        letter_type = col1.selectbox(
            "Letter type",
            ["Student grievance", "Fee issue", "Exam issue", "Transport issue", "Permission request", "Other"],
        )
        prepared_by = col2.text_input("Prepared by", "ABVP Thane Mahanagar")

        col3, col4 = st.columns(2)
        recipient_name = col3.text_input("Recipient name")
        recipient_designation = col4.text_input("Designation", placeholder="Principal / Officer / Manager")
        institution = st.text_input("Institution / Office")
        subject = st.text_input("Subject")
        body = st.text_area(
            "Main points",
            placeholder="Write the issue, student impact, requested action, and deadline.",
            height=160,
        )
        submitted = st.form_submit_button("Save letter")

        if submitted:
            if not recipient_designation or not institution or not subject or not body:
                st.error("Designation, institution, subject, and main points are required.")
            else:
                append_row(
                    "letters.csv",
                    LETTER_COLUMNS,
                    {
                        "id": next_id(letters, "LTR"),
                        "created_at": now_text(),
                        "letter_type": letter_type,
                        "recipient_name": recipient_name,
                        "recipient_designation": recipient_designation,
                        "institution": institution,
                        "subject": subject,
                        "body": body,
                        "prepared_by": prepared_by,
                    },
                )
                st.success("Letter saved.")
                st.rerun()

    if not letters.empty:
        latest = letters.iloc[-1]
        st.subheader("Latest Letter Draft")
        draft = build_letter(latest)
        st.text_area("Copy to Word / print on letterhead", draft, height=420)
        st.download_button(
            "Download latest letter as text",
            draft,
            file_name=f"{latest['id']}_{slugify(latest['subject'])}.txt",
            mime="text/plain",
        )

    st.subheader("Letter Register")
    st.dataframe(letters, use_container_width=True, hide_index=True)
    render_delete_controls("letters.csv", LETTER_COLUMNS, "letter")


def render_inventory() -> None:
    st.header("Inventory")
    inventory = read_table("inventory.csv", INVENTORY_COLUMNS)

    with st.form("new_inventory", clear_on_submit=True):
        st.subheader("Add / Record Material")
        col1, col2, col3 = st.columns(3)
        item = col1.text_input("Item", placeholder="Flags, banners, receipt books")
        category = col2.selectbox("Category", ["Stationery", "Campaign", "Event", "Books", "Technical", "Other"])
        location = col3.text_input("Storage location", placeholder="Main cupboard")
        col4, col5 = st.columns(2)
        quantity = col4.number_input("Quantity", min_value=0, value=0)
        minimum_required = col5.number_input("Minimum required", min_value=0, value=10)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save item")

        if submitted:
            if not item:
                st.error("Item name is required.")
            else:
                append_row(
                    "inventory.csv",
                    INVENTORY_COLUMNS,
                    {
                        "id": next_id(inventory, "INV"),
                        "created_at": now_text(),
                        "item": item,
                        "category": category,
                        "quantity": quantity,
                        "minimum_required": minimum_required,
                        "location": location,
                        "last_updated": date.today().isoformat(),
                        "notes": notes,
                    },
                )
                st.success("Inventory item saved.")
                st.rerun()

    st.subheader("Material Register")
    if inventory.empty:
        st.info("No inventory recorded yet.")
    else:
        edited = st.data_editor(
            inventory,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="inventory_editor",
        )
        if st.button("Save inventory changes"):
            edited["last_updated"] = date.today().isoformat()
            write_table("inventory.csv", edited)
            st.success("Inventory updated.")
            st.rerun()
    render_delete_controls("inventory.csv", INVENTORY_COLUMNS, "inventory item")


def render_tasks() -> None:
    st.header("Task Tracker")
    tasks = read_table("tasks.csv", TASK_COLUMNS)

    with st.form("new_task", clear_on_submit=True):
        st.subheader("Add Task")
        col1, col2, col3 = st.columns(3)
        task = col1.text_input("Task")
        owner = col2.text_input("Owner")
        related_area = col3.selectbox(
            "Related area",
            ["Grievance", "Membership", "Meeting", "Event", "Inventory", "Letter", "Other"],
        )
        col4, col5, col6 = st.columns(3)
        deadline = col4.date_input("Deadline", value=date.today() + timedelta(days=3))
        priority = col5.selectbox("Priority", PRIORITIES, index=1)
        status = col6.selectbox("Status", ["Open", "In Progress", "Blocked", "Done"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save task")

        if submitted:
            if not task or not owner:
                st.error("Task and owner are required.")
            else:
                append_row(
                    "tasks.csv",
                    TASK_COLUMNS,
                    {
                        "id": next_id(tasks, "TSK"),
                        "created_at": now_text(),
                        "task": task,
                        "owner": owner,
                        "related_area": related_area,
                        "deadline": deadline.isoformat(),
                        "priority": priority,
                        "status": status,
                        "notes": notes,
                    },
                )
                st.success("Task saved.")
                st.rerun()

    st.subheader("Task Register")
    if tasks.empty:
        st.info("No tasks recorded yet.")
    else:
        edited = st.data_editor(
            tasks,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="task_editor",
        )
        if st.button("Save task changes"):
            write_table("tasks.csv", edited)
            st.success("Tasks updated.")
            st.rerun()
    render_delete_controls("tasks.csv", TASK_COLUMNS, "task")


def render_export() -> None:
    st.header("Data Export")
    datasets = get_datasets()

    for label, (filename, columns) in datasets.items():
        df = read_table(filename, columns)
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"Download {label} CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
        )

    st.divider()
    st.subheader("Delete Stored Data")
    selected_dataset = st.selectbox("Dataset", list(datasets.keys()))
    filename, columns = datasets[selected_dataset]
    render_delete_controls(filename, columns, selected_dataset.lower(), expanded=True)


def render_filterable_table(df: pd.DataFrame, filter_columns: list[str]) -> None:
    if df.empty:
        st.info("No records yet.")
        return

    filtered = df.copy()
    filter_widgets = st.columns(min(len(filter_columns), 4))
    for index, column in enumerate(filter_columns):
        values = sorted(value for value in filtered[column].dropna().unique().tolist() if value)
        selected = filter_widgets[index % len(filter_widgets)].multiselect(column.replace("_", " ").title(), values)
        if selected:
            filtered = filtered[filtered[column].isin(selected)]

    st.dataframe(filtered, use_container_width=True, hide_index=True)


def render_delete_controls(
    filename: str,
    columns: list[str],
    record_label: str,
    expanded: bool = False,
) -> None:
    df = read_table(filename, columns)
    title = f"Delete {record_label} data"

    with st.expander(title, expanded=expanded):
        if df.empty:
            st.info(f"No {record_label} records to delete.")
            return

        id_options = df["id"].astype(str).tolist()
        selected_id = st.selectbox(
            f"Select {record_label} to delete",
            id_options,
            key=f"{filename}_{record_label}_delete_id",
        )

        selected_rows = df[df["id"].astype(str) == selected_id]
        if not selected_rows.empty:
            preview_columns = [column for column in columns if column in selected_rows.columns][:6]
            st.dataframe(selected_rows[preview_columns], use_container_width=True, hide_index=True)

        delete_selected = st.checkbox(
            f"I confirm deleting {selected_id}",
            key=f"{filename}_{record_label}_confirm_selected",
        )
        if st.button(
            f"Delete selected {record_label}",
            disabled=not delete_selected,
            key=f"{filename}_{record_label}_delete_selected",
        ):
            updated = df[df["id"].astype(str) != selected_id]
            write_table(filename, updated)
            st.success(f"Deleted {selected_id}.")
            st.rerun()

        st.divider()
        confirmation = st.text_input(
            f"Type DELETE ALL to clear all {record_label} records",
            key=f"{filename}_{record_label}_confirm_all",
        )
        if st.button(
            f"Delete all {record_label} records",
            disabled=confirmation != "DELETE ALL",
            key=f"{filename}_{record_label}_delete_all",
        ):
            write_table(filename, pd.DataFrame(columns=columns))
            st.success(f"Deleted all {record_label} records.")
            st.rerun()


def build_meeting_notice(title: str, meeting_date: date, meeting_time, venue: str, agenda: str) -> str:
    return (
        f"ABVP Thane Mahanagar\n"
        f"{title}\n\n"
        f"Date: {meeting_date.strftime('%d %b %Y')}\n"
        f"Time: {meeting_time.strftime('%I:%M %p')}\n"
        f"Venue: {venue}\n\n"
        f"Agenda:\n{agenda}\n\n"
        f"All concerned karyakartas are requested to attend on time.\n"
        f"- Karyalay Mantri, ABVP Thane Mahanagar"
    )


def build_letter(row: pd.Series) -> str:
    recipient_line = row["recipient_designation"]
    if row["recipient_name"]:
        recipient_line = f"{row['recipient_name']}, {recipient_line}"

    return (
        f"ABVP Thane Mahanagar\n"
        f"Date: {date.today().strftime('%d %b %Y')}\n\n"
        f"To,\n"
        f"{recipient_line}\n"
        f"{row['institution']}\n\n"
        f"Subject: {row['subject']}\n\n"
        f"Respected Sir/Madam,\n\n"
        f"{row['body']}\n\n"
        f"We request you to kindly look into the matter and take necessary action at the earliest.\n\n"
        f"Thanking you,\n\n"
        f"{row['prepared_by']}\n"
        f"ABVP Thane Mahanagar"
    )


def slugify(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "_" for character in value)
    return "_".join(part for part in cleaned.split("_") if part)[:50] or "letter"


if __name__ == "__main__":
    main()
