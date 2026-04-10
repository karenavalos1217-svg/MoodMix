const express = require("express");
const path = require("path");
const axios = require("axios");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
  res.render("index", { tracks: [], artist: "" });
});

app.post("/search", async (req, res) => {
  const artist = req.body.artist;

  try {
    const response = await axios.get("https://api.deezer.com/search", {
      params: {
        q: `artist:"${artist}"`,
        limit: 10
      }
    });

    const tracks = response.data.data || [];
    res.render("index", { tracks, artist });
  } catch (error) {
    console.error("Error con Deezer:", error.message);
    res.render("index", { tracks: [], artist });
  }
});

app.get("/playlists", (req, res) => {
  res.render("playlists");
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});