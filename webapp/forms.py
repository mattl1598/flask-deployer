from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, FileField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp


class AddNewProject(FlaskForm):
	project_name = StringField(
		'Project Name',
		render_kw={
			"placeholder": " "
		},
		validators=[DataRequired()]
	)
	git_repo = StringField(
		'Git Repository',
		render_kw={
			"placeholder": " "
		},
		validators=[DataRequired()],
	)
	git_branch = StringField(
		'Git Branch',
		render_kw={
			"placeholder": " "
		},
		validators=[DataRequired()],
	)
	urls = TextAreaField(
		'Sub-Domains for Project',
		render_kw={
			"placeholder": " "
		},
		validators=[DataRequired()],
	)
	submit = SubmitField('Submit')
