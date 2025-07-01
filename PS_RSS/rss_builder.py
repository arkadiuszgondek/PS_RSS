import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timedelta

BASE_URL = "https://przegladsportowy.onet.pl"
FEED_URL = f"{BASE_URL}/koszykowka.feed"

def get_article_links():
    res = requests.get(FEED_URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'xml')
    return [item.find('link').text for item in soup.find_all('item')]

def extract_metadata(article_url):
    try:
        res = requests.get(article_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        def meta(property=None, name=None, itemprop=None):
            if property:
                tag = soup.find("meta", attrs={"property": property})
            elif name:
                tag = soup.find("meta", attrs={"name": name})
            elif itemprop:
                tag = soup.find("meta", attrs={"itemprop": itemprop})
            return tag["content"] if tag else None

        pub_str = meta(itemprop="datePublished")
        pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else None

        return {
            "title": meta(property="og:title") or "",
            "link": meta(property="og:url") or article_url,
            "desc": meta(name="description") or "",
            "image": meta(property="og:image") or "",
            "pub_date": pub_date,
        "guid": meta(name="DC.Identifier") or ""
        }
    except Exception as e:
        print(f"❌ Błąd przy {article_url}: {e}")
        return None

def generate_rss(items):
    fg = FeedGenerator()
    fg.title("RSS z koszykówki – PS Onet")
    fg.link(href=BASE_URL + "/koszykowka", rel='alternate')
    fg.description("Artykuły z kategorii koszykówka z ostatnich 7 dni")
    now = datetime.utcnow()

    for art in items:
        if not art or not art["pub_date"]:
            continue
        if art["pub_date"] < now - timedelta(days=7):
            continue

        fe = fg.add_entry()
        fe.title(art["title"])
        fe.link(href=art["link"])
        fe.description(f"<img src='{art['image']}'/><br/>{art['desc']}")
                fe.guid(art["guid"], permalink=False)
        fe.pubDate(art["pub_date"].strftime('%a, %d %b %Y %H:%M:%S +0000'))

    return fg.rss_str(pretty=True)

def main():
    links = get_article_links()
    articles = [extract_metadata(link) for link in links]
    rss = generate_rss(articles)

    os.makedirs("docs", exist_ok=True)
    with open("docs/rss.xml", "wb") as f:
        f.write(rss)
    print("✅ Zaktualizowano docs/rss.xml")

if __name__ == "__main__":
    main()
