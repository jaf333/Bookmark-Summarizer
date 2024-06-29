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
    bookmarks = fetch_recent_bookmarks(client)
    # Call the main functionality to process bookmarks and send the email
    send_summary_email(client, bookmarks)
    return "Bookmarks fetched and email sent successfully!"

def fetch_recent_bookmarks(client):
    response = client.get_bookmarks(max_results=100)
    bookmarks = response.data
    recent_bookmarks = [tweet for tweet in bookmarks if (time.time() - tweet.created_at.timestamp()) < 86400]
    return recent_bookmarks

def send_summary_email(client, bookmarks):
    urls = extract_urls(bookmarks)
    summaries = []
    for url in urls:
        html_content = fetch_html_content(url)
        if html_content and is_article(html_content):
            summary = generate_summary(html_content)
            summaries.append(summary)
    email_body = compose_email(bookmarks, summaries)
    send_email("Your Daily Twitter Bookmarks Summary", email_body, os.getenv('EMAIL_ADDRESS'))

if __name__ == "__main__":
    app.run(debug=True)
