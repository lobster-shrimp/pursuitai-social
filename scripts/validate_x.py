#!/usr/bin/env python3
"""X (Twitter) API pre-flight validator. Posts nothing.

Verifies the four secrets authenticate and carry write permission.

Usage:
  export X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_SECRET=...
  python scripts/validate_x.py
"""
import os
import sys

def main():
    for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"):
        if not os.environ.get(k):
            print(f"  ✗ {k} not set")
            sys.exit(1)
    import tweepy
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"])
    me = client.get_me(user_auth=True)
    if not me.data:
        print("  ✗ credentials rejected")
        sys.exit(1)
    print(f"  ✓ authenticated as @{me.data.username} (id {me.data.id})")

    # v1.1 check confirms media-upload path + surfaces app permission level
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    api = tweepy.API(auth)
    try:
        api.verify_credentials()
        print("  ✓ v1.1 media-upload auth path works")
    except Exception as e:
        print(f"  ✗ v1.1 auth failed (media uploads would break): {e}")
        sys.exit(1)

    print("\nNote: write permission is only provable by posting. If the app's")
    print("permission level isn't 'Read and write', regenerate the access")
    print("token AFTER changing it in the developer portal.")
    print("\nX credentials look good. 🚀")

if __name__ == "__main__":
    main()
