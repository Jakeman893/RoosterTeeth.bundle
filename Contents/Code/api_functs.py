import itertools

def get_shows(api, channel=None, page=1, count=20):
    return api.shows(site=channel, page=page, count=count)

def get_seasons(api, show_id):
    return api.show_seasons(show_id)

def get_episodes(api, season_id, count=None):
    if not count:
        return api.season_episodes(season_id)
    else:
        episodes = api.season_episodes(season_id)
        return list(itertools.islice(episodes, count))

def get_recent_show_episodes(api, channel=None, count=20):
    episodes = api.episodes(site=channel)
    return list(itertools.islice(episodes, count))