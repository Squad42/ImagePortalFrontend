from flask import Flask
from flask_bootstrap import Bootstrap
import os
import consul
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
Bootstrap(app)
app.config.from_object("imagePortalFrontend.server_config.DevelopmentConfig")
metrics = PrometheusMetrics(app=app)

#Update configuration from consul server
@app.before_request
def update_from_consul():
    if "consul_server" not in app.config or app.config["consul_server"] is None:
        #connect to Consul server
        try:
                app.config["consul_server"] = consul.Consul(host=app.config["CONFIG_HOST"],
                                              port=app.config["CONFIG_PORT"])
                print("Consul config server [{}:{}] connected! ".format(
                        app.config["CONFIG_HOST"],
                        app.config["CONFIG_PORT"]))
                app.config["LOGGER"].info("Consul config server [{}:{}] connected! ".format(
                        app.config["CONFIG_HOST"],
                        app.config["CONFIG_PORT"]))
        except:
            app.config["consul_server"]=None
            print("Can not connect to Consul config server [{}:{}] ! ".format(
                        app.config["CONFIG_HOST"], app.config["CONFIG_PORT"]))
    
    
    if app.config["consul_server"] is None:
        return
    
    print("Updating configuration from config server..")
    protected_keys=["ENV","DEBUG","TESTING","PROPAGATE_EXCEPTIONS",
                    "PRESERVE_CONTEXT_ON_EXCEPTION","SECRET_KEY","PERMANENT_SESSION_LIFETIME",
                    "USE_X_SENDFILE","SERVER_NAME","APPLICATION_ROOT","SESSION_COOKIE_NAME",
                    "SESSION_COOKIE_DOMAIN","SESSION_COOKIE_PATH","SESSION_COOKIE_HTTPONLY",
                    "SESSION_COOKIE_SECURE","SESSION_COOKIE_SAMESITE","SESSION_REFRESH_EACH_REQUEST",
                    "MAX_CONTENT_LENGTH","SEND_FILE_MAX_AGE_DEFAULT","TRAP_BAD_REQUEST_ERRORS",
                    "TRAP_HTTP_EXCEPTIONS","EXPLAIN_TEMPLATE_LOADING","PREFERRED_URL_SCHEME",
                    "JSON_AS_ASCII","JSON_SORT_KEYS","JSONIFY_PRETTYPRINT_REGULAR",
                    "JSONIFY_MIMETYPE","TEMPLATES_AUTO_RELOAD","MAX_COOKIE_SIZE"]
    try:
        for key in [k for k in app.config if k not in protected_keys]:
            index = None
            index, data = app.config["consul_server"].kv.get(key, index=index)
            if data is not None:
                app.config[key]=data["Value"]
                print("Consul KEY={}\t VALUE={}".format(key,data["Value"]))
            else:
                print("Consul KEY={}\t does not exist".format(key))
                app.config["LOGGER"].warning("Consul KEY={}\t does not exist".format(key))
    except Exception as e:
        print("!!!CONSUL SERVER PROBLEM [{}:{}]\n{}".format(app.config["CONFIG_HOST"],
                                                        app.config["CONFIG_PORT"],
                                                        str(e)))     
        app.config["LOGGER"].error("!!!CONSUL SERVER PROBLEM [{}:{}]\n{}".format(app.config["CONFIG_HOST"],
                                                        app.config["CONFIG_PORT"],
                                                        str(e))) 

from imagePortalFrontend.server_views import *

if __name__ == "__main__":

    # MIGHT COME HANDY FOR TESTING
    # if not app.config["UPLOAD_FOLDER"].exists():
    #     app.config["UPLOAD_FOLDER"].mkdir(parents=True)

    app.run(host="0.0.0.0", port=5003, debug=False)
