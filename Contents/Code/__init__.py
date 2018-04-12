from config import *
from requirements_plex import api
from api_functs import *
import m3u8
import requests

resolution = None

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
            DirectoryObject(
                key = Callback(
                    ShowSeasons, 
                    show = show.id_
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
            DirectoryObject(
                key = Callback(
                    SeasonEpisodes, 
                    season = season.id_
                ), 
                title = title
            )
        )

    return oc

##########################################################################################
@route("/video/roosterteeth/channel/recent")
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
                        container = Container.MP4,
                        video_codec = VideoCodec.H264,
                        audio_codec = AudioCodec.AAC,
                        video_resolution = resolution,
                        audio_channels = 2,
                        parts = [
                            PartObject(key = Callback(PlayOfflineStream,url = episode.video.get_quality()))
                        ]
                    )
                ]
            )
        )
    return oc

##########################################################################################
@route("/video/roosterteeth/season/episodes")
def SeasonEpisodes(season, **kwargs):
    season = api.season(season)
    oc = ObjectContainer(title2='Season %d' % season.number)

    Log.Info("Getting season episodes for Season %d." % (season.number))

    episodes = season.episodes

    for episode in episodes:
        if episode.is_sponsor_only:
            continue
        url = episode.video.url.replace('https', 'http')
        Log.Info("Stream URL is %s." % url)
        oc.add(
            EpisodeObject(
                key = Callback(SeasonEpisodes, season = season.id_),
                rating_key = episode.id_,
                title = episode.title,
                thumb = episode.thumbnail,
                summary = episode.description,
                season = season.number,
                duration = episode.length,
                items = [
                    MediaObject(
                        protocol                = 'hls',
                        container               = 'mpegts',
                        video_codec             = VideoCodec.H264,
                        audio_codec             = AudioCodec.AAC,
                        audio_channels          = 2,
                        optimized_for_streaming = True,
                        parts                   = [PartObject(
                                                    key = HTTPLiveStreamURL(url=url)
                                                )]
                    )
                ]
            )
        )
    return oc

@indirect
def PlayOfflineStream(url, **kwargs):
    Log.Info(' --> Final stream url: %s' % (url))
    return IndirectResponse(VideoClipObject, key=url)

@indirect
def PlayVideo(url, **kwargs):
    # parts = []
    Log.Info('Getting video files for %s' % (url))

    try:
        res = requests.get(url)
    except requests.exceptions.SSLError:
        res = requests.get(url, verify=False)
        Log.Info("Warning: SSL Certificate Error")
        pass
    
    m3u8_obj = m3u8.loads(res.text)

    m3u8_obj.base_uri = url.replace('.m3u8', '')
    Log.Info('Returning segment from %s' % m3u8_obj.segments[0].absolute_uri)
    return IndirectResponse(VideoClipObject, m3u8_obj.segments[0].absolute_uri)

    # for seg in m3u8_obj.segments:
    #     duration = int(seg.duration * 1000)
    #     Log.Info('Log duration %d' % duration)
    #     parts.append(
    #         PartObject(
    #             key=seg.absolute_uri,
    #             duration= duration
    #         )
    #     )

    # return parts