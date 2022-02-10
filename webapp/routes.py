import json
import os
import subprocess

from flask import make_response, render_template, send_file

from webapp import app


@app.route('/')
def frontpage():
	conf_path = app.basedir + "/config.json"
	print(conf_path := conf_path.replace("\\", "/"))
	with open(conf_path, 'r') as conf:
		config = json.load(conf)
	projects = config["projects"]
	return render_template(
		'frontpage.html',
		css="frontpage.css",
		projects=projects
	)


@app.route("/test")
def test():
	output = subprocess.check_output("service open-amdram-portal status")
	return output
	# if output == 0:
	# 	return "Running"
	# else:
	# 	return "Dead"


@app.route("/css/<string:filename>", methods=["GET"])
def css(filename):
	fp = app.basedir + '/webapp/static/css/' + filename
	response = make_response(send_file(fp.replace("\\", "/")))
	response.headers['mimetype'] = 'text/css'
	return response
