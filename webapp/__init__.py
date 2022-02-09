from flask import Flask
import os
from sass import compile

basedir = os.getcwd()
print(basedir)

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{basedir}/dev.db"
app.basedir = basedir
app.scss_path = "static/scss/"

scss_paths = [
	"webapp/" + app.scss_path,
	"webapp/" + app.scss_path + "partials"
]

compile(dirname=("webapp/static/scss/", "webapp/static/css/"), output_style="compressed")

# app.scss_compiler = Compiler(search_path=scss_paths)

app.jinja_env.globals.update(
	len=len,
	range=range,
	str=str
)

from webapp import routes