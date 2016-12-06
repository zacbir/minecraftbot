from patterns import *

chat_messages = [
    '[2016-12-02 13:18:57] [Server thread/INFO]: <[player]> here is a message I am saying',
]

join_messages = [
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] joined the game',
]

left_messages = [
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] left the game',
]

death_messages = [
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was shot by arrow',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was shot by [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was shot by [player/mob] using [bow name]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was pricked to death',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] walked into a cactus while trying to escape [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] drowned',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] drowned whilst trying to escape [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] experienced kinetic energy',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] blew up',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was blown up by [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] hit the ground too hard',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell from a high place',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell off a ladder',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell off some vines',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell out of the water',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell into a patch of fire',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell into a patch of cacti',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was doomed to fall by [mob/player]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was shot off some vines by [mob/player]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was shot off a ladder by [mob/player]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was blown from a high place by [mob/player]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was squashed by a falling anvil',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was squashed by a falling block',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] went up in flames',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] burned to death',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was burnt to a crisp whilst fighting [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] walked into a fire whilst fighting [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] tried to swim in lava',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] tried to swim in lava while trying to escape [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was struck by lightning',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] discovered floor was lava',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was slain by [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was slain by [player/mob] using [weapon]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] got finished off by [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] got finished off by [player/mob] using [weapon]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was fireballed by [mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was killed by magic',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was killed by [player/mob] using magic',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] starved to death',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] suffocated in a wall',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was squished too much',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] was killed while trying to hurt [player/mob]',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell out of the world',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] fell from a high place and fell out of the world',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] withered away',
    '[2016-12-02 13:18:57] [Server thread/INFO]: [victim] was pummeled by [killer]', ]

achievement_messages = [
    '[2016-12-02 13:18:57] [Server thread/INFO]: [player] has just earned the achievement [Achievement Name]',
]

def assert_pattern_matches(pattern, message):
    assert pattern.match(message) is not None, "\"{}\" does not match r'{}'".format(message, pattern.pattern)

def test_chat_messages():
    for message in chat_messages:
        assert_pattern_matches(chat_pattern, message)

def test_join_messages():
    for message in join_messages:
        assert_pattern_matches(join_pattern, message)

def test_left_messages():
    for message in left_messages:
        assert_pattern_matches(left_pattern, message)

def test_death_messages():
    for message in death_messages:
        assert_pattern_matches(died_pattern, message)

def test_achievement_messages():
    for message in achievement_messages:
        assert_pattern_matches(achievement_pattern, message)
