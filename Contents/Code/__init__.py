from config import *
from requirements_plex import api
from api_functs import *
import m3u8
import requests
from rt_api.api import AuthenticationError

resolution = None
token = None

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1     = TITLE
    ObjectContainer.art        = R(ART)


###################################################################################################
def ValidatePrefs():
    global token
    Log.Info("Attempting Login")

    if not token and Prefs['login'] and Prefs['username'] and Prefs['password']:
        try:
            # Log.Info("Attempting Login with: %s and %s" % (Prefs['username'], Prefs['password']))
            token = api.authenticate(Prefs['username'], Prefs['password'])
            Log.Info("Login success")
            return ObjectContainer(
                header = "Login success",
                message = "You're now logged in!"
            )
        except AuthenticationError:
            Log.Error("Could not authenticate, possibly incorrect username or password.")
            return ObjectContainer(
                header = "Login failure",
                message = "Please check your username and password"
            )

##########################################################################################
@handler('/video/roosterteeth', TITLE, thumb = ICON, art = ART)
def MainMenu():
    global token
    if not token and Prefs['login'] and Prefs['username'] and Prefs['password']:
        try:
            # Log.Info("Attempting Login with: %s and %s" % (Prefs['username'], Prefs['password']))
            token = api.authenticate(Prefs['username'], Prefs['password'])
            Log.Info("Login success")
            return ObjectContainer(
                header = "Login success",
                message = "You're now logged in!"
            )
        except AuthenticationError:
            Log.Error("Could not authenticate, possibly incorrect username or password.")
            return ObjectContainer(
                header = "Login failure",
                message = "Please check your username and password"
            )

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
@route('/video/roosterteeth/channel/shows')
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
            TVShowObject(
                key = Callback(
                    ShowSeasons, 
                    show = show.id_
                ), 
                title = show.name,
                summary = show.summary,
                thumb = show.thumbnail,
                studio = channel
            )
        )

    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No shows found."

    return oc

##########################################################################################
@route("/video/roosterteeth/show/seasons")
def ShowSeasons(show):
    show = api.show(show)
    oc = ObjectContainer(title2=show.name, art = show.cover_picture)

    Log.Info("Getting seasons for %s." % show.name)

    seasons = show.seasons

    # Fetch seasons    
    for season in seasons:
        title = "Season " + str(season.number)

        oc.add(
            SeasonObject(
                key = Callback(
                    SeasonEpisodes, 
                    season = season.id_
                ),
                summary = season.description,
                rating_key = season.id_,
                title = season.title,
                index = season.number,
                show = season,
                episode_count = len(season.episodes)
            )
        )

    return oc

##########################################################################################
@route("/video/roosterteeth/channel/recent")
def RecentEpisodes(channel):
    global token
    oc = ObjectContainer(title2='Recent')

    Log.Info("Getting recent episodes for %s." % channel)

    episodes = api.episodes(site=channel)

    episodes = list(itertools.islice(episodes, 20))

    for episode in episodes:
        if episode.is_sponsor_only and not token:
            continue
        oc.add(
            CreateEpisodeObject(
                ep_id = episode.id_
            )
        )
    return oc

##########################################################################################
@route("/video/roosterteeth/season/episodes")
def SeasonEpisodes(season, **kwargs):
    global token
    season = api.season(season)
    oc = ObjectContainer(title2='Season %d' % season.number)

    Log.Info("Getting season episodes for Season %d." % (season.number))

    episodes = season.episodes

    for episode in episodes:
        if episode.is_sponsor_only and not token:
            continue
        oc.add(
            CreateEpisodeObject(
                ep_id = episode.id_
            )
        )

    return oc

@route('/video/roosterteeth/videoclip')
def CreateEpisodeObject(ep_id, include_container=False):
    episode = api.episode(ep_id)

    episode.video.available_qualities

    items = []

    for qual in episode.video.available_qualities:
        items.append(
            MediaObject(
                protocol                = 'hls',
                container               = 'mpegts',
                video_codec             = VideoCodec.H264,
                audio_codec             = AudioCodec.AAC,
                video_resolution        = int(qual[:-1]),
                audio_channels          = 2,
                optimized_for_streaming = True,
                parts = [PartObject(key=HTTPLiveStreamURL(url=episode.video.get_quality(qual)))]
            )
        )
    items.reverse()

    ep_obj = EpisodeObject(
        key = Callback(CreateEpisodeObject, ep_id=ep_id, include_container=True),
        rating_key = episode.id_,
        title = episode.title,
        summary = episode.description,
        thumb = episode.thumbnail,
        duration = episode.length,
        art = episode.thumbnail,
        items = items
    )

    if include_container:
        return ObjectContainer(objects=[ep_obj])
    else:
        return ep_obj
