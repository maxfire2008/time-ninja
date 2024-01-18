import flask

app = flask.Flask(__name__)
app.jinja_env.autoescape = True


@app.route("/")
def index():
    return flask.render_template("index.html.j2")
