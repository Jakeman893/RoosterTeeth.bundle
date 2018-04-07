from config import *

Login = SharedCodeService.roosterteeth.Login

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1     = TITLE
    ObjectContainer.art        = R(ART)

    HTTP.CacheTime  = CACHE_1HOUR
    HTTP.User_Agent = HTTP_USER_AGENT

###################################################################################################
def ValidatePrefs():

    if Prefs['login'] and Prefs['username'] and Prefs['password']:
        result = Login()

        if result:
            return ObjectContainer(
                header = "Login success",
                message = "You're now logged in!"
            )
        else:
            return ObjectContainer(
                header = "Login failure",
                message = "Please check your username and password"
            )

##########################################################################################
@handler('/video/roosterteeth', TITLE, thumb = ICON, art = ART)
def MainMenu():

    oc = ObjectContainer()

    oc.add(PrefsObject(title = "Preferences"))

    for channel in CHANNELS:
        oc.add(
            DirectoryObject(
                key = Callback(Shows, url=channel['url'], title=channel['title']),
                title = channel['title'],
                thumb = channel['image']
            )
        )

    return oc

##########################################################################################
@route('/video/roosterteeth/Shows')
def Shows(url, title):

    url = SERIES_URL + "channel_id=" + url
    oc = ObjectContainer(title2=title)
    
    shows       = []
    showNames   = []

    # Add shows by parsing the site
    element = HTML.ElementFromURL(url)

    # Log.Info("The url is %s" % url, True)
    # Log.Info("The series url is %s" % SERIES_URL, True)

    # Log.Info(str(element), True)

    Log.Info("Hello", True)

    for item in element.xpath('//div[contains (@class, "card-image-wrapper")]'):
        show = {}
        try:
            Log.Info("Hello", True)
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

    sortedShows = sorted(shows, key=lambda show: show["name"])
    for show in sortedShows:

        if show["name"] in ('RT Sponsor Cut'):
            if not (Prefs['login'] and Prefs['username'] and Prefs['password']):
                continue

        oc.add(
            DirectoryObject(
                key = Callback(
                    EpisodeCategories, 
                    title = show["name"],
                    url = show["url"], 
                    thumb = show["img"]
                ), 
                title = show["name"],
                summary = show["desc"],
                thumb = show["img"]
            )
        )

    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No shows found."

    return oc

##########################################################################################
@route("/video/roosterteeth/EpisodeCategories")
def EpisodeCategories(title, url, thumb):

    oc = ObjectContainer(title2=title)

    content = HTTP.Request(url).content

    if 'Sponsor Only Content' in content:
        if not (Prefs['login'] and Prefs['username'] and Prefs['password']):
            return ObjectContainer(header="Sponsor Only", message="This show contains sponsor only content.\r\nPlease login to access this show")

    element = HTML.ElementFromString(content)

    try:
        art = element.xpath("//*[@class='cover-image']/@style")[0].split("(")[1].split(")")[0]

        if art.startswith("//"):
            art = 'http:' + art 
    except:
        art = None

    # Fetch seasons    
    for item in element.xpath("//*[@id='tab-content-episodes']//*[@class='accordion']//label"):
        id = item.xpath("./@for")[0]

        if not id:
            continue

        try:
            season = id.split(" ")[1]
        except:
            season = None

        title = item.xpath(".//*[@class='title']/text()")[0]

        oc.add(
            DirectoryObject(
                key = Callback(
                    Items, 
                    title = title, 
                    url = url, 
                    thumb = thumb,
                    xpath_string = "//*[@id='tab-content-episodes']//*[@class='accordion']",
                    art = art,
                    id = id
                ), 
                title = title,
                thumb = thumb,
                art = art
            )
        )

    if len(oc) > 0:
        title = 'Episodes'
        oc.add(
            DirectoryObject(
                key = Callback(
                    Items, 
                    title = title,
                    url = url,
                    thumb = thumb,
                    xpath_string = "//*[@id='tab-content-episodes']",
                    art = art
                ), 
                title = title,
                thumb = thumb,
                art = art
            )
        )

    return oc

##########################################################################################
@route("/video/roosterteeth/Items", recent = bool)
def Items(title, url, thumb, xpath_string, art, id=None, recent=False):

    oc = ObjectContainer(title2=title)

    element = HTML.ElementFromURL(url)

    episodes = []
    for item in element.xpath(xpath_string):

        if id:
            season_id = item.xpath(".//label/@for")[0]

            if id != season_id:
                continue

            try:
                season = int(id.split(" ")[1])
            except:
                season = None

        else:
            season = None

        for episode in item.xpath(".//*[@class='grid-blocks']//li"):

            url = episode.xpath("./a/@href")[0]
            title = episode.xpath(".//*[@class='name']/text()")[0]
            thumb = episode.xpath(".//img/@src")[0]

            if thumb.startswith("//"):
                thumb = 'http:' + thumb

            try:
                index = int(title.split(" ")[1])
            except:
                index = None

            try:
                duration_string = episode.xpath(".//*[@class='timestamp']/text()")[0].strip()
                duration = ((int(duration_string.split(":")[0])*60) + int(duration_string.split(":")[1])) * 1000
            except:
                duration = None

            episodes.append(
                EpisodeObject(
                    url = url,
                    title = title,
                    thumb = thumb,
                    season = season,
                    index = index,
                    duration = duration,
                    art = art
                )
            )

    if Prefs['sort'] == 'Latest First' or recent:
        for episode in episodes:
            oc.add(episode)   
    else:
        for episode in reversed(episodes):
            oc.add(episode)

    if len(oc) < 1:
        return ObjectContainer(
            header = "Sorry",
            message = "Couldn't find any videos for this show"
        )

    return oc
