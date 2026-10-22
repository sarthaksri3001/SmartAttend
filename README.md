# SmartAttend

A role-based attendance management system built with **Python, Flask, SQLite, HTML, CSS, and JavaScript**.

## Demo workspaces
- **Director / Admin:** campus overview, student directory, subject catalogue, attendance reports, CSV export, and below-75% alerts.
- **Faculty:** mark and save attendance, search students, and review attendance reports.
- **Student:** view personal attendance, subject-wise percentages, and warnings for subjects below 75%.

The opening screen lets you select a workspace. This is a demo role selector, not production authentication.

## Features
- Dashboard with student count, subject count, overall attendance, and students below 75%.
- Current-day attendance snapshot.
- Attendance marking by subject and date, including bulk Present/Absent controls.
- Student directory with search, add, and admin delete actions.
- Subject catalogue with add-subject support.
- Individual attendance reports and CSV export.
- SQLite persistence and duplicate-safe attendance records.
- 30 fictional students, 4 sample subjects, and 10 days of sample attendance created on first run.
- Responsive interface with animations and reduced-motion support.

## Run locally
Python 3.10 or newer is recommended.

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. The database file `smartattend.db` is created automatically on first run and is excluded from Git.

## Project structure
```
SmartAttend/
├── app.py
├── requirements.txt
├── templates/index.html
├── static/app.js
├── static/style.css
└── README.md
```

## API
- `GET /api/bootstrap` returns students, subjects, records, and dashboard metrics.
- `POST /api/attendance` creates or updates attendance for a subject and date.
- `POST /api/students` adds a student.
- `DELETE /api/students/<roll>` removes a student and associated attendance.
- `POST /api/subjects` adds a subject.

## Security note
This is a local academic prototype. The role selector is only a UI convenience and does not enforce permissions on the server. Before public deployment or use with real student records, add proper authentication, server-side role authorization, CSRF protection, stronger validation, and HTTPS. All included student data is fictional.
