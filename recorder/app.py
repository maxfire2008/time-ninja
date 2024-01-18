import flask
import datetime
import pathlib

app = flask.Flask(__name__)


def sanitize_text(text: str) -> str:
    return "".join([(c if c.isalpha() or c.isdigit() else "_") for c in text])


@app.route("/")
def index():
    # return static file web/index.html
    return flask.send_file("index.html")


@app.route("/web/<path:path>")
def web(path):
    return flask.send_from_directory(".", path)


@app.route(
    "/upload/<string:event_slug>/<string:file_name>/<int:part_number>", methods=["POST"]
)
def upload(event_slug: str, file_name: str, part_number: int):
    address = flask.request.remote_addr
    if address == "127.0.0.1" and "X-Forwarded-For" in flask.request.headers:
        address = flask.request.headers["X-Forwarded-For"]

    print(datetime.datetime.now())
    print(event_slug, address, file_name, part_number, sep=" / ")
    print(flask.request.headers.get("User-Agent"))
    print(flask.request.mimetype)

    filepath = (
        pathlib.Path("../footage")
        / sanitize_text(event_slug)
        / sanitize_text(address)
        / sanitize_text(file_name)
        / f"{part_number:08d}.webm"
    )

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # append flask.request.get_data(cache=False) to file
    with filepath.open("ab") as f:
        f.write(flask.request.get_data(cache=False))
    return "OK"
