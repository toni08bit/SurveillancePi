import flask
application = flask.Flask("survpi-web")

@application.route("/ping")
def ping():
    return "Pong!",200

if (__name__ == "__main__"):
    application.run()