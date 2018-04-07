import urllib
from lxml import html
from config import CHANNELS
SERIES_URL = "https://roosterteeth.com/series?"

def getShows(channel):
    url = SERIES_URL + "channel_id=" + channel
    print url
    content = urllib.urlopen(url).read()
    page = html.fromstring(urllib.urlopen(url).read())
    shows = []
    print str(html.tostring(page))
    for item in page.find_class('card-image-wrapper'): 
        show = {}
        print item
        try:
            show["url"] = item.xpath("./@href")[0]
            show["img"] = item.xpath(".//img/@src")[0]

            if show["img"].startswith("//"):
                show["img"] = 'http:' + show["img"]

            # show["name"] = item.xpath(".//*[@class='name']/text()")[0]
            # show["desc"] = item.xpath(".//*[@class='post-stamp']/text()")[0]

            # if not show["name"] in showNames:
                # showNames.append(show["name"])
                # shows.append(show)
        except:
            pass

    print shows
