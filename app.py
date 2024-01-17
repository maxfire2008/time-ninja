import flask
import datetime
import pathlib

app = flask.Flask(__name__)


@app.route("/")
def index():
    # return static file web/index.html
    return flask.send_file("web/index.html")


@app.route("/web/<path:path>")
def web(path):
    return flask.send_file("web/" + path)


@app.route("/upload", methods=["POST"])
def upload():
    # print the mimetype of the request
    print(flask.request.mimetype)
    # save content to file
    filepath = pathlib.Path("data") / (
        datetime.datetime.now().isoformat().replace(":", "-") + ".webm"
    )
    with open(filepath, "wb") as f:
        f.write(flask.request.get_data(cache=False))
    return "OK"
