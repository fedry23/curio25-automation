"""Bounded, opt-in learning using the official YouTube APIs only.

No peer metrics are persisted or used as a cross-channel score. First-party
experimentation never bypasses editorial or publication approval.
"""
import json
import math
import os
from datetime import date, timedelta
from statistics import median

BASELINE = 'entusiasta'
CHALLENGER = 'alegre'
PROFILES = {BASELINE, CHALLENGER}
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/yt-analytics.readonly']
QUERIES = {
    'es': ('curiosidades ciencia datos sorprendentes', 'datos curiosos divulgación'),
    'en': ('interesting facts science curiosity', 'amazing facts educational'),
}


def collect_peers(api, own_channel, per_language=15):
    """Return ephemeral official public records, never fictional fill-ins.

    Search languages and regions are discovery filters, not verified nationality.
    At least 15 distinct channels per search language and 30 total by default.
    Titles/thumbnails/duration/statistics are original API fields, not copied
    scripts or inferred retention. Read-only calls; no scraping or downloads.
    """
    if not 1 <= per_language <= 15:
        raise ValueError('Tamaño de muestra inválido')
    selected = []
    seen = {own_channel}
    for language, queries in QUERIES.items():
        candidates = {}
        for query in queries:
            items = api.search().list(
                part='snippet', type='video', q=query, maxResults=50,
                relevanceLanguage=language, regionCode='ES' if language=='es' else 'US',
                videoDuration='medium').execute().get('items', [])
            for item in items:
                channel = item.get('snippet', {}).get('channelId')
                video = item.get('id', {}).get('videoId')
                if channel and video and channel not in seen:
                    candidates.setdefault(channel, []).append(video)
        found = 0
        for channel, ids in candidates.items():
            if found == per_language:
                break
            ids = list(dict.fromkeys(ids))[:5]
            details = api.videos().list(
                part='id,snippet,contentDetails,statistics,status',
                id=','.join(ids)).execute().get('items', [])
            videos = [v for v in details if v.get('id') in ids
                      and v.get('snippet', {}).get('channelId') == channel
                      and v.get('status', {}).get('privacyStatus') == 'public']
            if not videos:
                continue
            records = api.channels().list(part='id,snippet,statistics',
                                           id=channel).execute().get('items', [])
            record = next((c for c in records if c.get('id') == channel), None)
            if not record:
                continue
            selected.append({'search_language': language, 'channel': record, 'videos': videos})
            seen.add(channel)
            found += 1
        if found < per_language:
            raise ValueError('Muestra real insuficiente para '+language)
    return selected


def decide(samples):
    """Only first-party, fixed observation-window data; no peer aggregation.

    Compare video-level median averageViewPercentage after at least five
    qualifying episodes per variant. A 3-point threshold avoids small changes.
    This is a heuristic, not proof of statistical significance or causation.
    """
    cohorts = {name: [] for name in PROFILES}
    seen = set()
    for row in samples:
        video = row.get('video_id')
        profile = row.get('profile')
        views, retention = row.get('views'), row.get('retention')
        if not video or video in seen or profile not in cohorts:
            continue
        seen.add(video)
        if (isinstance(views, (int, float)) and not isinstance(views, bool)
                and isinstance(retention, (int, float)) and not isinstance(retention, bool)
                and math.isfinite(views) and math.isfinite(retention)
                and views >= 100 and retention >= 0):
            cohorts[profile].append(retention)
    if not all(len(v) >= 5 for v in cohorts.values()):
        return 'explore'
    delta = median(cohorts[CHALLENGER])-median(cohorts[BASELINE])
    if delta >= 3:
        return CHALLENGER
    return BASELINE


def assigned_profile(episode, decision):
    if decision in PROFILES:
        return decision
    if decision != 'explore':
        raise ValueError('Decisión desconocida')
    day = date.fromisoformat(episode.removeprefix('daily-'))
    # Alternation is reproducible across retries; every weekday sees both variants.
    return BASELINE if day.toordinal() % 2 else CHALLENGER


def authorized_clients(config):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    raw = os.environ.get('YOUTUBE_ANALYTICS_TOKEN_JSON')
    if not raw or not config.get('channel_id'):
        raise PermissionError('Falta OAuth de analítica del canal')
    credentials = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    if credentials.expired:
        credentials.refresh(Request())
    if not credentials.has_scopes(SCOPES):
        raise PermissionError('Scopes de analítica insuficientes')
    data = build('youtube','v3',credentials=credentials,cache_discovery=False)
    own = data.channels().list(part='id',mine=True).execute().get('items', [])
    if {c['id'] for c in own} != {config['channel_id']}:
        raise PermissionError('El OAuth no corresponde al canal esperado')
    analytics = build('youtubeAnalytics','v2',credentials=credentials,cache_discovery=False)
    return data, analytics


def own_samples(api, db, today):
    from .state import production_episode
    samples = []
    rows = db.execute(
        "SELECT e.id,e.video_id,p.profile FROM episodes e JOIN episode_profiles p "
        "ON e.id=p.episode WHERE e.status='published' AND e.video_id IS NOT NULL ORDER BY e.id DESC")
    for episode, video, profile in rows:
        if not production_episode(episode) or profile not in PROFILES:
            continue
        day = date.fromisoformat(episode[6:])
        # Same first seven calendar days for each video; allow reporting latency.
        if not 10 <= (today-day).days <= 30:
            continue
        result = api.reports().query(
            ids='channel==MINE', startDate=day.isoformat(),
            endDate=(day+timedelta(days=6)).isoformat(),
            metrics='views,averageViewPercentage', dimensions='video',
            filters='video=='+video).execute()
        names = [x['name'] for x in result.get('columnHeaders', [])]
        for values in result.get('rows', []):
            row = dict(zip(names, values))
            if row.get('video') == video:
                samples.append({'video_id':video,'profile':profile,
                                'views':row.get('views'),'retention':row.get('averageViewPercentage')})
    return samples


def select_for_render(config, db, episode, today=None, clients=None):
    """Fail to baseline on missing credentials/data; never persist raw metrics."""
    baseline = config.get('voice_delivery', BASELINE)
    if config.get('learning_enabled') is not True or config.get('learning_policy_accepted') is not True:
        return baseline, 'disabled'
    if not episode.startswith('daily-'):
        return baseline, 'not_daily'
    try:
        data, analytics = clients or authorized_clients(config)
        # Require the real 30-channel sample before entering experimental mode.
        collect_peers(data, config['channel_id'])
        decision = decide(own_samples(analytics, db, today or date.today()))
        return assigned_profile(episode, decision), decision
    except Exception:
        # Do not print OAuth errors, API payloads or peer statistics in public Actions.
        return baseline, 'unavailable'


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root/'config.json').read_text())
    if config.get('learning_policy_accepted') is not True:
        raise SystemExit('Analítica desactivada hasta aceptar condiciones y disponer de OAuth.')
    data, _ = authorized_clients(config)
    peers = collect_peers(data, config['channel_id'])
    # No third-party statistics, names or titles are written to the public repository.
    print(json.dumps({'official_channels_retrieved':len(peers),
                      'publication_attempted':False,'raw_metrics_persisted':False}))
