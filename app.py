import urllib2
import datetime
from bs4 import BeautifulSoup
from urlparse import urljoin
from flask import Flask, Markup, request
from werkzeug.contrib.atom import AtomFeed
from werkzeug.contrib.cache import FileSystemCache

app = Flask(__name__)
cache = FileSystemCache(cache_dir='/tmp/')

CACHE_TIMEOUT=60

def get_url(url, cache_timeout):
    """
    Returns the contents of the URL as a string.
    """
    html = cache.get("cache")
    if html is None:
        response = urllib2.urlopen(url)
        html = response.read()
        cache.set("cache", html, timeout=cache_timeout)
    return html

def get_articles(url):
    """yields a tuple of (title, url, published)"""
    html = get_url(url, cache_timeout=CACHE_TIMEOUT)
    soup = BeautifulSoup(html)
    for event in soup.select('.content-view-listing__single-item'):
        event_meta = event.select('div.event-meta')[0]

        event_day = event_meta.find('h1').get_text().strip()
        event_month, event_year = event_meta.find_all('h3')[:2]
        event_month = event_month.get_text().lower().strip()
        event_year = event_year.get_text().lower().strip()
        published = datetime.datetime.strptime("{} {} {}".format(event_year, event_month, event_day), "%Y %b %d")
        
        event_info = event.select('div.event-info')[0]
        url = event_info.find('a').get('href')
        title = event_info.find('h3').get_text().strip()
        title = Markup.escape(title)
        
        yield (title, url, published)

@app.route('/recent.atom')
def recent_feed():
    pages = [1,2,]
    fetch_urls = [
        'http://skillsmatter.com/skillscasts?page={}&q=&location=&content=skillscasts&sort_by=&historic='.format(p) for p in pages]
    feed = AtomFeed('SkillsCasts',  feed_url=request.url, url='http://skillsmatter.com/skillscasts')
    for fetch_url in fetch_urls:
        for title, url, published in get_articles(fetch_url):
            print 
            feed.add(title, unicode(""),
                     content_type='html',
                     author='Skills Matter',
                     url=urljoin(fetch_url, url),
                     updated=published,
                     published=published)
    return feed.get_response()

if __name__ == '__main__':
    app.run(debug=True)

