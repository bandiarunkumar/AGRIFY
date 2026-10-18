"""
Manual network test script for Google News RSS retrieval.
Safe for unittest discovery with zero import-time side effects.
"""
import urllib.request
import urllib.parse


def fetch_google_news():
    query = "India agriculture"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            print("Success! Read", len(xml_data), "bytes.")
    except Exception as e:
        print("Error:", e)


if __name__ == '__main__':
    fetch_google_news()
