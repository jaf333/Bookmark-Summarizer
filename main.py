import os
import tweepy
import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from transformers import pipeline
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

# Initialize summary generator
summarizer = pipeline("summarization")

# Email setup
def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_ADDRESS')
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)

def fetch_recent_bookmarks(client):
    response = client.get_bookmarks(max_results=100)
    bookmarks = response.data
    recent_bookmarks = [tweet for tweet in bookmarks if (time.time() - tweet.created_at.timestamp()) < 86400]
    return recent_bookmarks

def extract_urls(bookmarks):
    urls = []
    for bookmark in bookmarks:
        if 'urls' in bookmark.entities:
            for url in bookmark.entities['urls']:
                urls.append(url['expanded_url'])
    return urls

def fetch_html_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def is_article(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.find('article') is not None

def generate_summary(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    article_text = ' '.join([p.get_text() for p in soup.find_all('p')])
    summary = summarizer(article_text, max_length=100, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def compose_email(bookmarks, summaries):
    email_content = "<h1>Twitter Bookmarks Summary</h1><ul>"
    for bookmark, summary in zip(bookmarks, summaries):
        tweet_url = f"https://twitter.com/user/status/{bookmark.id}"
        email_content += f"<li><a href='{tweet_url}'>Original Tweet</a> - <a href='{bookmark.entities['urls'][0]['expanded_url']}'>Article</a><br>Summary: {summary}</li>"
    email_content += "</ul>"
    return email_content

def send_summary_email(client):
    bookmarks = fetch_recent_bookmarks(client)
    urls = extract_urls(bookmarks)
    summaries = []
    for url in urls:
        html_content = fetch_html_content(url)
        if html_content and is_article(html_content):
            summary = generate_summary(html_content)
            summaries.append(summary)
    email_body = compose_email(bookmarks, summaries)
    send_email("Your Daily Twitter Bookmarks Summary", email_body, os.getenv('EMAIL_ADDRESS'))

def schedule_daily_task():
    scheduler = BlockingScheduler()
    scheduler.add_job(send_summary_email, 'interval', hours=24)
    scheduler.start()

def test_script():
    client = tweepy.Client(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
    send_summary_email(client)

if __name__ == "__main__":
    test_script()
