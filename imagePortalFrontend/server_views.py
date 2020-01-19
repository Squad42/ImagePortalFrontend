from imagePortalFrontend.server import app
from flask import (
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
    jsonify,
    g,
    make_response,
)
import jwt
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import requests
from io import BytesIO
import os
import json
from datetime import datetime
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length


class LoginForm(FlaskForm):
    username = StringField("username", validators=[InputRequired(), Length(min=4, max=10)])
    password = PasswordField("password", validators=[InputRequired(), Length(min=4, max=20)])
    remember = BooleanField("remember me")


class RegisterForm(FlaskForm):
    username = StringField("username", validators=[InputRequired(), Length(min=4, max=10)])
    full_name = StringField("full name", validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField("password", validators=[InputRequired(), Length(min=4, max=20)])


def jwt_token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):

        if "jwt_token" not in session:
            return jsonify({"message": "Auth token is missing!"}), 403

        token = session["jwt_token"]

        if not token:
            return jsonify({"message": "Unknown token type!"}), 403

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
            g.user_info = data
            app.logger.info("Logged in user: %s", g.user_info["username"])
        except:
            return jsonify({"message": "Token is invalid!"}), 403

        return func(*args, **kwargs)

    return decorated


@app.route("/")
def index():

    catalogue_api_images = (
        "http://"
        + app.config["CATALOGUE_HOSTNAME"]
        + ":"
        + app.config["CATALOGUE_PORT"]
        + "/images"
    )

    response = requests.get(catalogue_api_images)
    json_data = json.loads(response.text)

    image_urls = []
    for image in json_data:

        image_url = image["img_uri"]
        if "www.dropbox.com" in image_url:
            image_url = image_url.replace("?dl=0", "?dl=1")

        image_urls.append(image_url)

    if "logged_in_user" in session:
        logged_user = session["logged_in_user"]
    else:
        logged_user = ""

    return render_template("index.html", image_urls=image_urls, user=logged_user)


@app.route("/detailed_view/<path:img_url>")
@jwt_token_required
def detailed_view(img_url):
    app.logger.info("IMG_URL: %s", img_url)
    comments_str = json.dumps(
        {"user1": "love it", "user2": "feels a bit off", "user3": "hilarious"}
    )

    comments = json.loads(comments_str)

    return render_template("detailed_view.html", img_url=img_url, comments=comments)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        usermanagement_api = (
            "http://"
            + app.config["USERMANAGE_HOSTNAME"]
            + ":"
            + app.config["USERMANAGE_PORT"]
            + "/users/login_credentials_check"
        )

        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        data = {"username": form.username.data, "password": form.password.data}

        response = requests.post(usermanagement_api, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_json = response.json()
            session["jwt_token"] = response_json["jwt_token"]
            session["logged_in_user"] = response_json["logged_in_user"]

            return redirect(url_for("index"))

        return "<h1>Invalid username or password</h1>"

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        usermanagement_api = (
            "http://"
            + app.config["USERMANAGE_HOSTNAME"]
            + ":"
            + app.config["USERMANAGE_PORT"]
            + "/users/add"
        )

        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        data = {
            "username": form.username.data,
            "full_name": form.full_name.data,
            "password": form.password.data,
        }

        response = requests.post(usermanagement_api, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            return redirect(url_for("index"))

        return response.text, response.status_code

    return render_template("register.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
def logout():

    usermanagement_api = (
        "http://"
        + app.config["USERMANAGE_HOSTNAME"]
        + ":"
        + app.config["USERMANAGE_PORT"]
        + "/users/logout"
    )

    response = requests.get(usermanagement_api)

    if response.status_code == 200:
        session.clear()

    return redirect(url_for("index"))


@app.route("/gui_upload/", defaults={"service": None, "version": None})
@app.route("/gui_upload/<string:service>/<string:version>", methods=["GET", "POST"])
def upload(service, version):

    if request.method == "POST":

        local_upload_api = (
            "http://"
            + app.config["UPLOAD_HOSTNAME"]
            + ":"
            + app.config["UPLOAD_PORT"]
            + "/upload/files/"
            + service
            + "/"
            + version
            + "/"
        )

        upload_api = "/upload/files/" + service + "/" + version + "/"

        return redirect(upload_api, code=307)

    return render_template("upload.html")
