import json
import os
import random
import subprocess
import platform

from jinja2 import Template
from flask import abort, make_response, redirect, render_template, request, send_file, url_for

from webapp import app


@app.route('/')
def frontpage():
	conf_path = app.basedir + "/config.json"
	print(conf_path := conf_path.replace("\\", "/"))
	with open(conf_path, 'r') as conf:
		config = json.load(conf)

	# if config["secrets"]["psw_hash"] == "":
	# 	return redirect(url_for("setup"))

	projects = config["projects"]

	if platform.system() == "Linux":
		# command that only works on Linux
		for project in projects.keys():
			output = subprocess.run(['/bin/systemctl', 'status', project], capture_output=True)
			try:
				status_split = output.stdout.decode('utf-8').splitlines()
				print(len(status_split))
				status_line = status_split[2]
			except IndexError:
				print("error")
				return str(str(len(status_split)) + " " + str(status_split))
			status = int("Active: inactive (dead)" in status_line)
			projects[project]["status"] = status

			if not status:
				uptime = status_line[status_line.index("; ") + 2:-5]
				projects[project]["uptime"] = uptime
	else:
		# emulating command output when not running on Linux
		for project in projects.keys():
			status = random.choice([0, 1])
			projects[project]["status"] = status

			if not status:
				uptime = "4h 20m"
				projects[project]["uptime"] = uptime

	return render_template(
		'frontpage.html',
		css="frontpage.css",
		projects=projects,
		hostname=platform.node()
	)


@app.route("/setup", methods=['GET', 'POST'])
def setup():
	if request.method == 'GET':
		return render_template("setup.html")


@app.route("/update/<string:project>")
def update(project):
	conf_path = app.basedir + "/config.json"
	print(conf_path := conf_path.replace("\\", "/"))
	with open(conf_path, 'r') as conf:
		config = json.load(conf)
	projects = config["projects"]
	if project in projects.keys():
		output = subprocess.run(['git', '-C', projects[project]["path"], 'pull'])
		return redirect(url_for('frontpage'))
	else:
		abort(404)


@app.route("/<string:command>/<string:project>")
def start(command, project):
	valid_commands = ["start", "stop", "restart"]
	if command in valid_commands:
		conf_path = app.basedir + "/config.json"
		print(conf_path := conf_path.replace("\\", "/"))
		with open(conf_path, 'r') as conf:
			config = json.load(conf)
		projects = config["projects"]
		if project in projects.keys():
			cmd1 = subprocess.Popen(['echo', config["secrets"]["sudo_psw"]], stdout=subprocess.PIPE)
			subprocess.run(['sudo', '-S', '/bin/systemctl', command, project], stdin=cmd1.stdout)
			return redirect(url_for('frontpage'))
		else:
			abort(404)
	else:
		abort(403)


@app.route("/test")
def test():
	with open(app.basedir + "/config_templates/service", "r") as file:
		t = Template(file.read())
	output = t.render(
		path="/home/mattl1598/flask-deployer",
		user="mattl1598",
		project_name="flask-deployer"
	)

	with open(app.basedir + "/test", "w") as file:
		file.write(output)
	return output
	# abort(404)


@app.route("/css/<string:filename>", methods=["GET"])
def css(filename):
	fp = app.basedir + '/webapp/static/css/' + filename
	response = make_response(send_file(fp.replace("\\", "/")))
	response.headers['mimetype'] = 'text/css'
	return response
