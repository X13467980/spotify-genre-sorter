import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# .envファイルから環境変数を読み込み
load_dotenv()

app = FastAPI()

# Spotify APIの認証情報（環境変数から取得）
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-library-read"
))

@app.get("/")
def read_root():
    return {"message": "FastAPI is working!"}

@app.get("/classify-liked-songs")
def classify_liked_songs():
    try:
        results = sp.current_user_saved_tracks(limit=50)
        genre_map = {}

        for item in results['items']:
            track = item['track']
            artist_id = track['artists'][0]['id']
            artist_info = sp.artist(artist_id)
            genres = artist_info.get('genres', [])

            for genre in genres:
                genre_map.setdefault(genre, []).append(track['name'])

        return {"genres": genre_map}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000))
    )