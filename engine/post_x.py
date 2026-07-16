"""Post to X (Twitter) via API v2 with media, using tweepy.

Env vars required (create app at https://developer.x.com, Free tier works):
  X_API_KEY, X_API_SECRET          - app consumer keys
  X_ACCESS_TOKEN, X_ACCESS_SECRET  - user tokens for @pursuit_ai
                                     (app must have Read+Write permission)
"""
import os

def post(text, media_path=None):
    import tweepy
    ck, cs = os.environ["X_API_KEY"], os.environ["X_API_SECRET"]
    at, ats = os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"]

    media_ids = None
    if media_path:
        # media upload still rides the v1.1 endpoint with OAuth 1.0a
        auth = tweepy.OAuth1UserHandler(ck, cs, at, ats)
        api_v1 = tweepy.API(auth)
        if media_path.endswith((".mp4", ".mov")):
            media = api_v1.media_upload(media_path, media_category="tweet_video",
                                        chunked=True)
        else:
            media = api_v1.media_upload(media_path)
        media_ids = [media.media_id]

    client = tweepy.Client(consumer_key=ck, consumer_secret=cs,
                           access_token=at, access_token_secret=ats)
    resp = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = resp.data["id"]
    print(f"[x] posted https://x.com/pursuit_ai/status/{tweet_id}")
    return tweet_id
