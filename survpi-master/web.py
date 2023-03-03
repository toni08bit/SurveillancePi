import flask
application = flask.Flask("survpi-web")

@application.route("/")
def test():
    return "Hello!",200

if (__name__ == "__main__"):
    print("hello? flask")
    application.run()