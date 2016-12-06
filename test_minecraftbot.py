import minecraftbot

bot = minecraftbot.MinecraftBot('Foo', 'Bar', '/tmp')

def test_parse_slack_output():
    output = [
        {
            'channel': '#foobar',
            'text': '<@Foo>: list'
        }
    ]

    command, channel = bot.parse_slack_output(output)

    assert command == 'list', 'Command not found'
    assert channel == '#foobar', 'Channel not found'

def test_parse_slack_output_not_at_us():
    output = [
        {
            'channel': '#foobar',
            'text': '<@Bar>: How was your weekend?'
        }
    ]

    command, channel = bot.parse_slack_output(output)

    assert command is None, 'Command not None'
    assert channel is None, 'Channel not None'