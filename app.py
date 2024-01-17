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
    print(flask.request.headers)

    # save content to file
    filename = flask.request.headers.get("File-Name")
    # sanitize filename
    filename_sanitized = "".join(
        [(c if c.isalpha() or c.isdigit() else "_") for c in filename]
    )

    filepath = pathlib.Path("footage") / (filename_sanitized + ".webm")
    # append flask.request.get_data(cache=False) to file
    with filepath.open("ab") as f:
        f.write(flask.request.get_data(cache=False))
    return "OK"
