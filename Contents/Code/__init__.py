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
@route('/video/roosterteeth/<channel>/shows')
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
        if episode.is_sponsor_only:
            continue
        oc.add(
            EpisodeObject(
                key = Callback(RecentEpisodes, channel),
                rating_key = episode.id_,
                title = episode.title,
                thumb = episode.thumbnail,
                summary = episode.description,
                season = episode.season.number,
                duration = episode.length,
                items = [
                    MediaObject(
                        video_resolution = 720,
                        optimized_for_streaming = True,
                        parts = [
                            PartObject(
                                key = HTTPLiveStreamURL(episode.video.get_quality())
                            )
                        ]
                    )
                ]
            )
        )
    return oc