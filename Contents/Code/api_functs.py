import itertools

def get_episodes(api, season_id, count=None):
    if not count:
        return api.season_episodes(season_id)
    else:
        episodes = api.season_episodes(season_id)
        return list(itertools.islice(episodes, count))