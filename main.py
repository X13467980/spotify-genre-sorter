import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

app = FastAPI()

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-library-read playlist-modify-private"
))

@app.get("/")
def read_root():
    return {"message": "FastAPI is working!"}

@app.get("/classify-liked-songs")
def classify_liked_songs():
    try:
        results = sp.current_user_saved_tracks(limit=50)
        genre_map = {}

        for item in results["items"]:
            track = item["track"]
            artist_id = track["artists"][0]["id"]
            artist_info = sp.artist(artist_id)
            genres = artist_info.get("genres", [])

            for genre in genres:
                genre_map.setdefault(genre, []).append(track["name"])

        return {"genres": genre_map}

    except Exception as e:
        print("🔴 classify error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-playlists-by-genre")
def create_playlists_by_genre():
    try:
        user_id = sp.me()["id"]
        genre_map = {}

        # 🎧 全曲を取得（ページネーション）
        limit = 50
        offset = 0
        total = 1  # 初期値を 1 にしてループ開始

        print("🎧 Starting to fetch liked songs...")

        while offset < total:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            total = results["total"]
            print(f"📄 Fetching tracks {offset+1} to {min(offset+limit, total)} of {total}")

            for item in results["items"]:
                track = item["track"]
                track_name = track["name"]
                track_id = track["id"]
                artist = track["artists"][0]
                artist_name = artist["name"]
                artist_id = artist["id"]

                artist_info = sp.artist(artist_id)
                genres = artist_info.get("genres", [])

                if genres:
                    print(f"🎤 {track_name} by {artist_name} → Genres: {genres}")
                else:
                    print(f"🎤 {track_name} by {artist_name} → No genre info")

                for genre in genres:
                    genre_map.setdefault(genre, []).append(track_id)

            offset += limit

        print("\n🗂️ Classification by genre:")
        for genre, tracks in genre_map.items():
            print(f"  - {genre}: {len(tracks)} track(s)")

        created_playlists = []

        print("\n✅ Creating playlists...")
        for genre, track_ids in genre_map.items():
            playlist = sp.user_playlist_create(
                user=user_id,
                name=f"{genre}",
                public=False,
                description="Auto-generated from liked songs by genre"
            )

            print(f"📝 Created playlist: Genre: {genre} → {playlist['external_urls']['spotify']}")

            # 100曲ずつ追加
            for i in range(0, len(track_ids), 100):
                chunk = track_ids[i:i+100]
                sp.playlist_add_items(playlist["id"], chunk)
                print(f"    ↳ Added {len(chunk)} tracks to playlist '{genre}'")

            created_playlists.append({
                "genre": genre,
                "url": playlist["external_urls"]["spotify"]
            })

        print("\n🎉 All playlists created successfully!")
        return {"created": created_playlists}

    except Exception as e:
        print("🔴 ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)))