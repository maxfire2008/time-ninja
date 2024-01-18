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


@app.after_request
def after_request(response):
    response.headers.add("Accept-Ranges", "bytes")
    return response


def get_chunk(path, byte1=None, byte2=None):
    video_files = {}
    # get all mp4 files in path and write their sizes to video_files
    for file in sorted(pathlib.Path(path).iterdir()):
        if file.suffix == ".mp4":
            video_files[file.name] = file.stat().st_size

    path = pathlib.Path(path)

    file_size = sum(video_files.values())

    start = 0

    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start

    chunk = b""
    bytes_read = 0

    for file_name, size in video_files.items():
        if bytes_read + size > start:
            with open(path / file_name, "rb") as f:
                if bytes_read < start:
                    f.seek(start - bytes_read)
                chunk += f.read(
                    min(length - (bytes_read - start), size - (start - bytes_read))
                )
        if bytes_read + size > start + length:
            break
        bytes_read += size

    return chunk, start, length, file_size


@app.route("/video/<string:slug>/<string:host>/<string:recording>")
def video(slug, host, recording):
    file_path = (
        pathlib.Path("../footage")
        / sanitize_text(slug)
        / sanitize_text(host)
        / sanitize_text(recording)
    )

    range_header = flask.request.headers.get("Range", None)
    byte1, byte2 = 0, None
    if range_header:
        match = re.search(r"(\d+)-(\d*)", range_header)
        groups = match.groups()

        if groups[0]:
            byte1 = int(groups[0])
        if groups[1]:
            byte2 = int(groups[1])

    chunk, start, length, file_size = get_chunk(file_path, byte1, byte2)
    resp = flask.Response(
        chunk,
        206,
        mimetype="video/mp4",
        content_type="video/mp4",
        direct_passthrough=True,
    )
    resp.headers.add(
        "Content-Range",
        "bytes {0}-{1} / {2}".format(start, start + length - 1, file_size),
    )
    return resp


@app.route("/video_duration/<string:slug>/<string:host>/<string:recording>")
def video_duration(slug, host, recording):
    file_path = (
        pathlib.Path("../footage")
        / sanitize_text(slug)
        / sanitize_text(host)
        / sanitize_text(recording)
    )

    # Create a list to store video chunks
    video_chunks = []

    # Collect video chunks
    for file in sorted(pathlib.Path(file_path).iterdir()):
        if file.suffix == ".mp4":
            with open(file, "rb") as f:
                video_chunks.append(f.read())

    # Check if there are video chunks
    if not video_chunks:
        return flask.Response(
            "No video chunks found", status=404, mimetype="text/plain"
        )

    # pipe the video chunks to ffprobe to get the duration
    try:
        ffprobe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                "-",
            ],
            input=b"".join(video_chunks),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        # duration = ffprobe.stdout.decode()
        duration = 0  # ffprobe is NOT giving the correct duration (always 15 seconds)
    except subprocess.CalledProcessError as e:
        return flask.Response(
            f"Error running ffprobe: {e.stderr.decode()}",
            status=500,
            mimetype="text/plain",
        )

    return flask.Response(duration, mimetype="text/plain")
