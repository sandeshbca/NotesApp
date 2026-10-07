# Notelet

A modern personal notes app built with Flask, SQLite, HTML, CSS, and vanilla JavaScript.

## Features

- User registration and secure password hashing
- Login/logout with protected user sessions
- Personal dashboard with user-scoped notes
- Create, edit, delete, and search notes
- Five note color accents and responsive mobile UI

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

For production, set a strong `SECRET_KEY` environment variable before starting the app.
