from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from flask_server.models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class EditProfileForm(FlaskForm):
    profile_picture_url = StringField(
        "Profile Picture URL", validators=[DataRequired()]
    )
    twitter = StringField("twitter", validators=[DataRequired()])
    instagram = StringField("instagram", validators=[DataRequired()])
    github = StringField("github", validators=[DataRequired()])
    username = StringField("username", validators=[DataRequired()])
    about_me = TextAreaField("about me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Submit")

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError("Please use a different username.")


class ResetPWForm(FlaskForm):
    password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    new_password2 = PasswordField(
        "Repeat New Password", validators=[DataRequired(), EqualTo("new_password")]
    )
    submit = SubmitField("Reset Password")


class ForgotPWForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset Password")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class PostForm(FlaskForm):
    body = StringField("Say something about this video:", validators=[DataRequired()])
    url = StringField("https://www.youtube.com/watch?v=", validators=[DataRequired()])
    submit = SubmitField("Create Post")


class UpdateForm(FlaskForm):
    body = StringField("Say something about this video:", validators=[DataRequired()])
    url = StringField("https://www.youtube.com/watch?v=", validators=[DataRequired()])
    submit = SubmitField("Update Post")
