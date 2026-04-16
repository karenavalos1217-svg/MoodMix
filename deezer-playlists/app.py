from flask import Flask, render_template, request, redirect
import requests
import os
from dotenv import load_dotenv
from db import get_connection

# cargar variables de entorno (.env)
load_dotenv()

app = Flask(__name__)

@app.route("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return f"Conectado a PostgreSQL: {result}"
    except Exception as e:
        return f"Error: {e}"

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
                "limit": 60
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
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, created_at FROM playlists ORDER BY id DESC")
    playlists = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("playlists.html", playlists=playlists)


#pa crear las playlist
@app.route("/playlists/create", methods=["POST"])
def create_playlist():
    name = request.form.get("name")

    if not name:
        return "El nombre de la playlist es obligatorio"

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO playlists (name) VALUES (%s)",
        (name,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/playlists")

#pa crear las playlist
@app.route("/add-to-playlist", methods=["POST"])
def add_to_playlist():
    playlist_id = request.form.get("playlist_id")
    track_id = request.form.get("track_id")
    title = request.form.get("title")
    artist = request.form.get("artist")
    album = request.form.get("album")
    duration = request.form.get("duration")
    preview = request.form.get("preview")
    cover = request.form.get("cover")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO playlist_songs
        (playlist_id, deezer_track_id, title, artist_name, album_name, duration, preview, cover)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (playlist_id, track_id, title, artist, album, duration, preview, cover))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/playlists")



@app.route("/playlists/<int:id>")
def view_playlist(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, artist_name, album_name, duration, preview, cover
        FROM playlist_songs
        WHERE playlist_id = %s
    """, (id,))

    songs = cur.fetchall()

    cur.execute("""
        SELECT COALESCE(SUM(duration), 0)
        FROM playlist_songs
        WHERE playlist_id = %s
    """, (id,))

    total_duration = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template("playlist.html", songs=songs, total_duration=total_duration)


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    print(f"Servidor corriendo en http://localhost:{PORT}")
    app.run(debug=True, port=PORT)


    