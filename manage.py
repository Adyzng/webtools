#!/usr/bin/env python
import os

from web.webapp import create_app
from flask_script import Manager, Shell

# Manager app 
app = create_app(os.getenv('FLASK_CONFIG'))
manager = Manager(app)

def make_shell_context():
	return dict(app=app)

manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def deploy():
	"""Run deployment tasks."""
	pass

if __name__ == '__main__':
	manager.run()