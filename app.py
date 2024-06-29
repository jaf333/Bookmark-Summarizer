import os
from flask import Flask, redirect, request, session, url_for
import tweepy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = os.getenv('TWITTER_CLIENT_ID')
client_secret = os.getenv('TWITTER_CLIENT_SECRET')
redirect_uri = os.getenv('TWITTER_REDIRECT_URI')

oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=client_id,
    redirect_uri=redirect_uri,
    scope=["tweet.read", "users.read", "bookmark.read"],
    client_secret=client_secret
)

@app.route('/')
def login():
    authorization_url = oauth2_user_handler.get_authorization_url()
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    oauth2_user_handler.fetch_token(code)
    session['access_token'] = oauth2_user_handler.access_token
    session['refresh_token'] = oauth2_user_handler.refresh_token
    return redirect(url_for('bookmarks'))

@app.route('/bookmarks')
def bookmarks():
    access_token = session.get('access_token')
    client = tweepy.Client(bearer_token=access_token)
    # Now you can call the main functionality to fetch bookmarks
    fetch_recent_bookmarks(client)
    return "Bookmarks fetched successfully!"

def fetch_recent_bookmarks(client):
    response = client.get_bookmarks(max_results=100)
    bookmarks = response.data
    recent_bookmarks = [tweet for tweet in bookmarks if (time.time() - tweet.created_at.timestamp()) < 86400]
    return recent_bookmarks

if __name__ == "__main__":
    app.run(debug=True)
