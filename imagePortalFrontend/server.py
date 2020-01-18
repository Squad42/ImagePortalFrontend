from flask import Flask
from flask_bootstrap import Bootstrap
import os

app = Flask(__name__)
Bootstrap(app)
app.config.from_object("imagePortalFrontend.server_config.DevelopmentConfig")

from imagePortalFrontend.server_views import *

if __name__ == "__main__":

    # MIGHT COME HANDY FOR TESTING
    # if not app.config["UPLOAD_FOLDER"].exists():
    #     app.config["UPLOAD_FOLDER"].mkdir(parents=True)

    app.run(host="0.0.0.0", port=5003)
