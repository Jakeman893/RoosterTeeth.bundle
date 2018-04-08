from config import *
from requirements_plex import api
from api_functs import *

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1     = TITLE
    ObjectContainer.art        = R(ART)


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
                key = Callback(Shows, channel=channel['title']),
                title = channel['title'],
                thumb = channel['image']
            )
        )

    return oc

##########################################################################################
@route('/video/roosterteeth/Shows')
def Shows(channel):
    oc = ObjectContainer(title2=channel)
    
    Log.Info("Getting shows for %s." % channel)

    channel = channel.replace(" ", "")

    oc.add(
        DirectoryObject(
            key = Callback(
                RecentEpisodes,
                channel=channel
            ),
            title = 'Recent'
        )
    )

    shows = api.shows(site=channel)

    for show in shows:
        oc.add(
            DirectoryObject(
                key = Callback(
                    ShowSeasons, 
                    show = show
                ), 
                title = show.name,
                summary = show.summary,
                thumb = show.thumbnail
            )
        )

    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No shows found."

    return oc

##########################################################################################
@route("/video/roosterteeth/ShowSeasons")
def ShowSeasons(show):
    oc = ObjectContainer(title2=show.name, art = show.cover_picture)

    Log.Info("Getting seasons for %s." % show.name)

    oc.add(
        DirectoryObject(
            title = 'Recent'
        )
    )

    episodes = show.episodes

    for episode in episodes:
        oc.add(
            DirectoryObject(
                key = Callback(
                    Items, 
                    title = title,
                    thumb = thumb,
                    art = thumb
                ),
                title = episode.title,
                thumb = episode.thumbnail,
                summary = episode.description
            )
        )

    seasons = show.seasons

    # Fetch seasons    
    for season in seasons:
        title = "Season " + str(season.number)

        oc.add(
            DirectoryObject(
                key = Callback(
                    Items, 
                    title = title,
                    id = season.id_
                ), 
                title = title
            )
        )

    return oc

##########################################################################################
@route("/video/roosterteeth/RecentEpisodes")
def RecentEpisodes(channel):
    oc = ObjectContainer(title2='Recent')

    Log.Info("Getting recent episodes for %s." % channel)

    episodes = api.episodes(site=channel)

    episodes = list(itertools.islice(episodes, 10))

    for episode in episodes:
        oc.add(
            EpisodeObject(
                title = episode.title,
                thumb = episode.thumbnail,
                summary = episode.description,
                url = episode.canonical_url,
                season = episode.season,
                duration = episode.length
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
