# Intro to Cloud Computing (CS 5165) project 2

A Flask app for project 2 served by Apache (mod_wsgi) on Ubuntu 24.04 that lets users register, log back in, and upload a text file whose word count is shown on their profile.

## Features
- Registration (username, password) with first name, last name, email, and address, stored in SQLite3
- Profile page showing the saved details after registering or logging in
- Log-in page that checks the username and password (passwords are hashed)
- .txt upload on the registration form or the profile page, with word count and a download button

## Files
- `flaskapp.py`: the Flask application
- `flaskapp.wsgi`: entry point for mod_wsgi
- `templates/`: HTML pages
- `apache-000-default.conf.snippet`: lines added to Apache's site config

## Deployed on a EC2 instance

