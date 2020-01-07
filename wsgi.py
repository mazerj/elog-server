#!/usr/bin/python

import sys; sys.path.insert(0, '/auto/www')

from elogapp.app import create_app
from app import create_app

app = create_app()
if __name__ == "__main__":
	app.run()


