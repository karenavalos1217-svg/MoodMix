from flask import Flask, render_template, request, redirect, flash
import requests
import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = "moodmix_secret_key"

PORT = int(os.getenv("PORT", 5000))


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


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.name, COUNT(ps.id) AS total_songs
        FROM playlists p
        LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
        GROUP BY p.id, p.name
        ORDER BY p.id DESC
    """)
    playlists = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", tracks=[], artist="", playlists=playlists)


@app.route("/search", methods=["POST"])
def search():
    artist = request.form.get("artist", "").strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, COUNT(ps.id) AS total_songs
        FROM playlists p
        LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
        GROUP BY p.id, p.name
        ORDER BY p.id DESC
    """)
    playlists = cur.fetchall()
    cur.close()
    conn.close()

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

        return render_template("index.html", tracks=tracks, artist=artist, playlists=playlists)

    except Exception as error:
        print("Error con Deezer:", error)
        flash("No se pudieron cargar canciones en este momento.")
        return render_template("index.html", tracks=[], artist=artist, playlists=playlists)


@app.route("/playlists")
def playlists():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.created_at, COUNT(ps.id) AS total_songs
        FROM playlists p
        LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
        GROUP BY p.id, p.name, p.created_at
        ORDER BY p.id DESC
    """)
    playlists = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("playlists.html", playlists=playlists)


@app.route("/playlists/create", methods=["POST"])
def create_playlist():
    name = request.form.get("name", "").strip()

    if not name:
        flash("El nombre de la playlist es obligatorio.")
        return redirect("/playlists")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO playlists (name) VALUES (%s)",
        (name,)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Playlist creada correctamente.")
    return redirect("/playlists")


@app.route("/playlists/delete/<int:id>", methods=["POST"])
def delete_playlist(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM playlists WHERE id = %s", (id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Playlist eliminada correctamente.")
    return redirect("/playlists")


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

    if not playlist_id:
        flash("Selecciona una playlist.")
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    # verificar que la playlist exista
    cur.execute("SELECT id, name FROM playlists WHERE id = %s", (playlist_id,))
    playlist = cur.fetchone()

    if not playlist:
        cur.close()
        conn.close()
        flash("La playlist seleccionada no existe.")
        return redirect("/")

    # contar canciones actuales
    cur.execute("""
        SELECT COUNT(*)
        FROM playlist_songs
        WHERE playlist_id = %s
    """, (playlist_id,))
    total_songs = cur.fetchone()[0]

    if total_songs >= 10:
        cur.close()
        conn.close()
        flash("Esta playlist ya tiene 10 canciones. No puedes agregar más.")
        return redirect(f"/playlists/{playlist_id}")

    # evitar duplicados
    cur.execute("""
        SELECT 1
        FROM playlist_songs
        WHERE playlist_id = %s AND deezer_track_id = %s
    """, (playlist_id, track_id))
    existing_song = cur.fetchone()

    if existing_song:
        cur.close()
        conn.close()
        flash("Esa canción ya está en la playlist.")
        return redirect(f"/playlists/{playlist_id}")

    # insertar canción
    cur.execute("""
        INSERT INTO playlist_songs
        (playlist_id, deezer_track_id, title, artist_name, album_name, duration, preview, cover)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (playlist_id, track_id, title, artist, album, duration, preview, cover))

    conn.commit()
    cur.close()
    conn.close()

    flash("Canción agregada correctamente.")
    return redirect(f"/playlists/{playlist_id}")


@app.route("/songs/delete/<int:song_id>", methods=["POST"])
def delete_song(song_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT playlist_id FROM playlist_songs WHERE id = %s", (song_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        flash("La canción no existe.")
        return redirect("/playlists")

    playlist_id = row[0]

    cur.execute("DELETE FROM playlist_songs WHERE id = %s", (song_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Canción eliminada correctamente.")
    return redirect(f"/playlists/{playlist_id}")


@app.route("/playlists/<int:id>")
def view_playlist(id):
    conn = get_connection()
    cur = conn.cursor()

    # obtener playlist
    cur.execute("SELECT id, name FROM playlists WHERE id = %s", (id,))
    playlist = cur.fetchone()

    if not playlist:
        cur.close()
        conn.close()
        flash("La playlist no existe.")
        return redirect("/playlists")

    # obtener canciones
    cur.execute("""
        SELECT id, title, artist_name, album_name, duration, preview, cover
        FROM playlist_songs
        WHERE playlist_id = %s
        ORDER BY id DESC
    """, (id,))
    songs = cur.fetchall()

    # duración total
    cur.execute("""
        SELECT COALESCE(SUM(duration), 0)
        FROM playlist_songs
        WHERE playlist_id = %s
    """, (id,))
    total_duration = cur.fetchone()[0]

    # contador de canciones
    total_songs = len(songs)

    cur.close()
    conn.close()

    return render_template(
        "playlist.html",
        playlist=playlist,
        songs=songs,
        total_duration=total_duration,
        total_songs=total_songs
    )


if __name__ == "__main__":
    print(f"Servidor corriendo en http://localhost:{PORT}")
    app.run(debug=True, port=PORT)