import flask
import pathlib
import os
import subprocess
import io
import re
import yaml

app = flask.Flask(__name__)
app.jinja_env.autoescape = True


def sanitize_text(text: str) -> str:
    return "".join([(c if c.isalpha() or c.isdigit() else "_") for c in text])


@app.route("/")
def index():
    # list items in ../footage
    files = {}
    for path in pathlib.Path("../footage").iterdir():
        if path.is_file() and path.suffix == ".yaml":
            if path.stem not in files:
                files[path.stem] = {}
            files[path.stem]["meta"] = True
        elif path.is_dir():
            if path.name not in files:
                files[path.name] = {}
            files[path.name]["video"] = True
    return flask.render_template("index.html.j2", files=files)


@app.route("/event/<string:slug>")
def event(slug):
    # find slug.yaml and slug/ in ../footage
    meta_path = pathlib.Path("../footage") / (slug + ".yaml")
    video_path = pathlib.Path("../footage") / slug
    if not meta_path.exists():
        flask.abort(404)
    meta = yaml.safe_load(meta_path.read_text())
    if not video_path.exists():
        flask.abort(404)

    recordings = {}
    for host_folder in video_path.iterdir():
        if not host_folder.is_dir():
            continue
        host = host_folder.name
        recordings[host] = []
        for recording in host_folder.iterdir():
            if not recording.is_dir():
                continue
            recordings[host].append(recording.name)
        recordings[host].sort()

    return flask.render_template(
        "event.html.j2",
        meta=meta,
        recordings=recordings,
        slug=slug,
    )


@app.route("/video/<string:slug>/<string:host>/<string:recording>/<string:file>")
def video(slug, host, recording, file):
    file_path = (
        pathlib.Path("../footage")
        / sanitize_text(slug)
        / sanitize_text(host)
        / sanitize_text(recording)
    )

    if not file_path.exists():
        flask.abort(404)

    if file == "index.m3u8":
        # open index.m3u8
        tc_m3u8 = file_path / "tc.m3u8"
        if not tc_m3u8.exists():
            flask.abort(404)

        # remove the #EXT-X-ENDLIST line
        tc_m3u8_text = tc_m3u8.read_text()
        tc_m3u8_text = re.sub(r"#EXT-X-ENDLIST", "", tc_m3u8_text)
        return flask.Response(tc_m3u8_text, mimetype="application/x-mpegURL")

    file_sanitized = sanitize_text(file)

    if file_sanitized.startswith("tc") and file_sanitized.endswith("ts"):
        # file_sanitized will end up as tc12_ts
        # extract the number "12"
        # send the file
        file_path = file_path / ("tc" + file_sanitized[2:-3] + ".ts")

        if not file_path.exists():
            flask.abort(404)

        return flask.send_file(file_path, mimetype="video/mp2t")

    return "404 Not Found", 404
