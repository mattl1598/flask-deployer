import json
import os
import random
import subprocess
import platform
import time
from jinja2 import Template
from flask import abort, make_response, redirect, render_template, request, send_file, url_for

from webapp import app
from webapp.forms import AddNewProject

import os


def opener(path, flags):
	return os.open(path, flags, 0o777)


@app.route('/')
def frontpage():
	conf_path = app.basedir + "/config.json"
	print(conf_path := conf_path.replace("\\", "/"))
	with open(conf_path, 'r') as conf:
		config = json.load(conf)

	if config["secrets"]["psw_hash"] == "":
		return redirect(url_for("setup"))

	projects = config["projects"]

	if platform.system() == "Linux":
		# command that only works on Linux
		for project in projects.keys():
			output = subprocess.run(['/bin/systemctl', 'status', project], capture_output=True)
			try:
				status_split = output.stdout.decode('utf-8').splitlines()
				print(len(status_split))
				status_line = status_split[2]
				status = int("Active: inactive (dead)" in status_line)
			except IndexError:
				# print("error")
				# return str(str(len(status_split)) + " " + str(status_split))
				status = 1
			projects[project]["status"] = status

			if not status:
				uptime = status_line[status_line.index("; ") + 2:-4]
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
		hostname=app.config['HOSTNAME']
	)


@app.route("/add", methods=['GET', 'POST'])
def add_new():
	if request.method == 'GET':
		return render_template(
			"add_new.html",
			form=AddNewProject(),
			css="add_new.css",
			hostname=app.config['HOSTNAME']
		)
	elif request.method == "POST":
		# noinspection PyUnresolvedReferences
		conf_path = app.basedir + "/config.json"
		print(conf_path := conf_path.replace("\\", "/"))
		with open(conf_path, 'r') as conf:
			config = json.load(conf)
		projects = config["projects"]

		project_name = request.form.get("project_name")
		git_repo = request.form.get("git_repo")
		git_branch = request.form.get("git_branch")
		urls = request.form.get("urls").splitlines()

		if project_name in projects.keys():
			abort(500)
			# TODO: add transparent exception handling for duplicate project names

		# setup for sudo commands
		cmd1 = subprocess.Popen(['/bin/echo', config["secrets"]["sudo_psw"]], stdout=subprocess.PIPE)

		# clone into repo
		cmd = [
			"/usr/bin/git",
			"clone",
			"-b",
			git_branch,
			git_repo,
			f'{config["secrets"]["projects_folder"]}/{project_name}'
		]
		print(" ".join(cmd))
		subprocess.run(cmd, check=True)

		# configure venv
		cmd = [
			"/usr/bin/python3",
			"-m",
			"venv",
			f'{config["secrets"]["projects_folder"]}/{project_name}/venv'
		]
		print(" ".join(cmd))
		subprocess.run(cmd, check=True)

		cmd = [
			f'{config["secrets"]["projects_folder"]}/{project_name}/venv/bin/python3',
			"-m",
			"pip",
			"install",
			"-r",
			f'{config["secrets"]["projects_folder"]}/{project_name}/requirements.txt'
		]
		print(" ".join(cmd))
		subprocess.run(cmd, check=True)

		# add project to config
		config["projects"][project_name] = {
			"git_repo": git_repo,
			"branch": git_branch,
			"path": f'{config["secrets"]["projects_folder"]}/{project_name}',
			"urls": urls
		}

		with open(conf_path, 'w') as conf:
			json.dump(config, conf)

		# add service file
		with open(app.basedir + "/config_templates/service", "r") as file:
			t = Template(file.read())

		service_file = t.render(
			path=f'{config["secrets"]["projects_folder"]}/{project_name}',
			user=config["secrets"]["install_username"],
			project_name=project_name
		)

		os.umask(0)  # Without this, the created file will have 0o777 - 0o022 (default umask) = 0o755 permissions
		with open(f"/etc/systemd/system/{project_name}.service", "w", opener=opener) as f:
			f.write(service_file)

		# create nginx config
		with open(app.basedir + "/config_templates/nginx", "r") as file:
			t = Template(file.read())

		nginx_file = t.render(
			urls=" ".join(config["projects"][project_name]["urls"]),
			path=f'{config["secrets"]["projects_folder"]}/{project_name}',
			project_name=project_name
		)

		os.umask(0)  # Without this, the created file will have 0o777 - 0o022 (default umask) = 0o755 permissions
		with open(f'/etc/nginx/sites-available/{project_name}', "w", opener=opener) as f:
			f.write(nginx_file)

		# enable nginx site
		cmd = [
			'/usr/bin/sudo', '-S',
			"/bin/ln", "-s",
			f"/etc/nginx/sites-available/{project_name}",
			"/etc/nginx/sites-enabled"
		]
		subprocess.run(cmd, check=True, stdin=cmd1.stdout)

		return redirect(f"/start/{project_name}")


@app.route("/setup", methods=['GET', 'POST'])
def setup():
	if request.method == 'GET':
		return render_template(
			"setup.html",
			css="setup.css",
			hostname=app.config['HOSTNAME']
		)


@app.route("/<string:command>/<string:project>")
def start(command, project):
	valid_commands = ["start", "stop", "restart"]
	conf_path = app.basedir + "/config.json"
	print(conf_path := conf_path.replace("\\", "/"))
	with open(conf_path, 'r') as conf:
		config = json.load(conf)
	projects = config["projects"]

	if project in projects.keys():
		if command in valid_commands:
			cmd1 = subprocess.Popen(['/bin/echo', config["secrets"]["sudo_psw"]], stdout=subprocess.PIPE)
			subprocess.run(['/usr/bin/sudo', '-S', '/bin/systemctl', command, project], stdin=cmd1.stdout)
			return redirect(url_for('frontpage'))
		elif command == "update":
			output = subprocess.run(['/usr/bin/git', '-C', projects[project]["path"], 'pull'])

			cmd = [
				f'{projects[project]["path"]}/venv/bin/python3',
				"-m",
				"pip",
				"install",
				"-r",
				f'{projects[project]["path"]}/requirements.txt'
			]
			print(" ".join(cmd))
			subprocess.run(cmd, check=True)
			return redirect(url_for('frontpage'))
		else:
			abort(403)
	else:
		abort(404)


@app.get("/logs/<project>")
def logs(project):
	conf_path = app.basedir + "/config.json"
	with open(conf_path, 'r') as conf:
		config = json.load(conf)
	projects = config["projects"]

	if project in projects.keys():
		proc = subprocess.run([
			'/bin/journalctl',
			'-S', '-24h',
			'-o', 'short-iso',
			'-u', project
		], check=True, capture_output=True)
		return render_template(
			"logs.html",
			project_name=project,
			logs=str(proc.stdout).splitlines()
		)


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


@app.route("/millis", methods=["GET"])
def millis():
	return str(round(time.time() * 1000))
