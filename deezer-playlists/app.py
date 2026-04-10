from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

# cargar variables de entorno (.env)
load_dotenv()

app = Flask(__name__)

# puerto
PORT = int(os.getenv("PORT", 5000))


# =========================
# RUTA PRINCIPAL "/"
# =========================
@app.route("/")
def index():
    return render_template("index.html", tracks=[], artist="")


# =========================
# BUSCAR EN DEEZER
# =========================
@app.route("/search", methods=["POST"])
def search():
    artist = request.form.get("artist")

    try:
        response = requests.get(
            "https://api.deezer.com/search",
            params={
                "q": f'artist:"{artist}"',
                "limit": 50
            },
            timeout=10
        )

        data = response.json()
        tracks = data.get("data", [])

        return render_template("index.html", tracks=tracks, artist=artist)

    except Exception as error:
        print("Error con Deezer:", error)
        return render_template("index.html", tracks=[], artist=artist)


# =========================
# PLAYLISTS
# =========================
@app.route("/playlists")
def playlists():
    return render_template("playlists.html")


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    print(f"Servidor corriendo en http://localhost:{PORT}")
    app.run(debug=True, port=PORT)