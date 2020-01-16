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
    app.logger.info("Displaying landing page")
    return render_template("index.html")


@app.route("/gallery")
def gallery():
    app.logger.info("Displaying landing page")

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

    return render_template("gallery.html", image_urls=image_urls)
