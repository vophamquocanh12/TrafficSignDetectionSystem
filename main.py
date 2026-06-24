from flask import Flask, render_template

from routes.camera_routes import camera_bp
from routes.image_routes import image_bp
from routes.video_routes import video_bp
from routes.history_routes import history_bp
from routes.sound_routes import sound_bp
from routes.download_routes import download_bp

app = Flask(__name__)

app.register_blueprint(camera_bp)
app.register_blueprint(image_bp)
app.register_blueprint(video_bp)
app.register_blueprint(history_bp)
app.register_blueprint(sound_bp)
app.register_blueprint(download_bp)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )