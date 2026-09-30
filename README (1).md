# Flask + SQLite3 on AWS EC2

A Flask app served by Apache (mod_wsgi) on Ubuntu 24.04 that lets users register, log back in, and upload a text file whose word count is shown on their profile.

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

## Deploy on the EC2 instance
```bash
sudo apt-get update
sudo apt-get install apache2 libapache2-mod-wsgi-py3 python3-pip python3-flask sqlite3 -y
chmod 755 /home/ubuntu/
# copy this folder to /home/ubuntu/flaskapp, then:
sudo ln -sT ~/flaskapp /var/www/html/flaskapp
# add the lines from apache-000-default.conf.snippet to /etc/apache2/sites-enabled/000-default.conf
sudo systemctl restart apache2
```
The database (`users.db`) and `uploads/` folder are created automatically on first request.
Troubleshoot with `sudo tail /var/log/apache2/error.log`.
