# Pizza Orders

A small Flask app for managing pizza orders. Users can create an account, log
in, submit pizza orders, view/edit/delete their own orders, and log out.

## Features

- Account creation with hashed passwords (Werkzeug's `generate_password_hash`)
- Session-based login/logout via Flask-Login
- Pizza order form built with Flask-WTF / WTForms, including validation
- Full CRUD on pizza orders, scoped to the logged-in user (you can only see,
  edit, or delete your own orders)
- SQLite database created automatically on first run

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Recommended) set a real secret key
export SECRET_KEY="replace-with-a-random-secret-string"   # Windows: set SECRET_KEY=...

# 4. Run the app
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

The first request creates `pizza.db` (a SQLite file) in the project
directory automatically — no migration step needed.

## Project layout

```
pizza_app/
├── app.py            # Flask app factory + all routes
├── config.py          # App configuration (secret key, database URI)
├── extensions.py       # SQLAlchemy / LoginManager instances
├── models.py           # User and PizzaOrder database models
├── forms.py             # WTForms: RegistrationForm, LoginForm, PizzaOrderForm
├── requirements.txt
└── templates/
    ├── base.html
    ├── register.html
    ├── login.html
    ├── orders.html
    ├── order_form.html
    └── error.html
```

## How it works

- **Create an account** — `/register`. Validates that the username/email
  aren't already taken and that the password is confirmed. Passwords are
  hashed before being stored, never saved in plain text.
- **Log in** — `/login`. Verifies credentials and starts a Flask-Login
  session; supports a "stay signed in" (remember me) option.
- **View orders** — `/orders`. Lists only the current user's orders, newest
  first.
- **Submit a new order** — `/orders/new`. A WTForms form with size, crust,
  toppings, quantity, and notes fields.
- **Update / delete an order** — `/orders/<id>/edit` and
  `/orders/<id>/delete`. Each checks that the order belongs to the logged-in
  user before allowing changes (returns 403 otherwise).
- **Log out** — `/logout`. Ends the session and redirects to the login page.

## Notes for production use

This is a learning/demo-scale app. Before deploying it for real use, you'd
want to, at minimum:
- Set `SECRET_KEY` from a secure environment variable (never commit it)
- Switch to a production database (Postgres/MySQL) instead of SQLite
- Serve behind a production WSGI server (e.g. gunicorn) rather than the Flask
  dev server
- Add rate limiting on login/registration and consider CSRF token rotation
  settings (Flask-WTF already provides CSRF protection by default)
