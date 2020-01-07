#!/usr/bin/python

# This needs to be run in the elogapp directory, which gunicorn/systemd
# seesm to do automatically, so these aren't really needed:
#   import sys; sys.path.insert(0, '/auto/www')
#   from elogapp.app import create_app

from app import create_app

app = create_app()
if __name__ == "__main__":
	app.run()


