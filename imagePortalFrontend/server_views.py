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

# from flask_login import (
#     LoginManager,
#     UserMixin,
#     login_user,
#     login_required,
#     logout_user,
#     current_user,
# )


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

    return render_template("index.html", image_urls=image_urls)


@app.route("/detailed_view/<path:img_url>")
def detailed_view(img_url):
    app.logger.info("IMG_URL: %s", img_url)
    comments_str = json.dumps({
        "user1": "love it",
        "user2": "feels a bit off",
        "user3": "hilarious",
    })

    comments = json.loads(comments_str)

    return render_template("detailed.html", img_url=img_url, comments=comments)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        usermanagement_api = (
            "http://"
            + app.config["USERMANAGE_HOSTNAME"]
            + ":"
            + app.config["USERMANAGE_PORT"]
            + "/login_credentials_check"
        )

        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        data = {"username": form.username.data, "password": form.password.data}

        response = requests.post(usermanagement_api, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
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

@app.route('/upload/', defaults={"service": None, "version": None})
@app.route("/upload/<string:service>/<string:version>", methods=["GET", "POST"])
def upload(service, version):

    if request.method == "POST":
        
        # upload_api = (
        #     "http://"
        #     + app.config["UPLOAD_HOSTNAME"]
        #     + ":"
        #     + app.config["UPLOAD_PORT"]
        #     + "/upload/files/"
        #     + service
        #     + "/"
        #     + version
        #     + "/"
        # )

        # headers = {"Content-type": "multipart/form-data", 'Accept':'application/json'}

        # # r = requests.post("http://myservicedotcom/upload", files=sendFile,
        # #                 headers={"X-Auth-Token": token, "Checksum": c, "File-Size": actualSize}

        # # ffiles = {"user_image": request.files["user_image"]}
        # # app.logger.info("%s", request.files["user_image"])
        # response = requests.post(upload_api, files=request.files)
        # # response = requests.post(upload_api, files=request.files["user_image"])
        # # response = requests.post(upload_api, headers=headers, data=request.files["user_image"])

        upload_api = (
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

        return redirect(upload_api, code=307)

        # if response.status_code == 200:
        #     return redirect(url_for("index"))

    return render_template("upload.html")
