"""Episode topic and YouTube title validation, independent from rendering."""

SOLAR_BODIES = {'mercury','venus','earth','sun','moon','mars','jupiter',
                'saturn','uranus','neptune','pluto'}


def episode_identity(facts):
    """Reject misleading solar-system metadata when creating other subjects."""
    if not facts:
        raise ValueError('Episodio sin hechos')
    explicit = [f.get('episode_topic') for f in facts]
    if any(not value for value in explicit) and any(
            f.get('body') not in SOLAR_BODIES for f in facts):
        raise ValueError('Las temáticas nuevas requieren episode_topic en cada hecho')
    topics = {f.get('episode_topic') or 'sistema solar' for f in facts}
    if len(topics) != 1:
        raise ValueError('Las 25 curiosidades deben compartir un tema de episodio')
    topic = topics.pop()
    specified = {f['episode_title'] for f in facts if f.get('episode_title')}
    if len(specified) > 1:
        raise ValueError('Títulos de episodio inconsistentes')
    title = specified.pop() if specified else (
        '25 curiosidades del sistema solar que cambian tu forma de mirarlo'
        if topic == 'sistema solar' else
        f'25 curiosidades sobre {topic} que te sorprenderán')
    if len(title) > 100 or len(title.strip()) < 10:
        raise ValueError('Título de YouTube fuera de límites')
    return topic, title

