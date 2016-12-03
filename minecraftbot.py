from datetime import datetime
import os
import re
import time
from slackclient import SlackClient

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

timestamp_pattern = re.compile(r'^\[(.*?)\].*?$')
chat_pattern = re.compile(r'^\[(.*?)\].*?\:\ \<(.*?)\>\ (.*?)$')
join_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (joined the game)$')
left_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (left the game)$')
broadcast_patterns = [
  re.compile(r'^\[(.*?)\].*?\:\ (.*?) (was|walked|drowned|experienced|blew|hit|fell|went|burned|tried|discovered|got|starved|suffocated|withered.*?)$'),
  re.compile(r'^\[(.*?)\].*?\:\ (.*?) (has just earned.*?)$')
]

BOT_ID = os.environ.get('SLACK_BOT_ID')
AT_BOT = '<@{}>'.format(BOT_ID)
LIST_COMMAND = 'list'

API_KEY = os.environ.get('SLACK_API_KEY')
slack_client = SlackClient(API_KEY)

current_players = set()

def post_message(message):
    slack_client.api_call(
        'chat.postMessage',
        channel='#general',
        text=message,
        as_user=True,
        link_names=True,
        username=BOT_ID)

def remember_timestamp(timestamp):
    d = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    seconds_timestamp = time.mktime(d.timetuple())

    with open('latest_timestamp.txt', 'w') as f:
        f.write(str(seconds_timestamp))

def handle_command(command, channel):
    response = "So far, all I know how to do is `list`! Tell @zacbir to add more smarts!"
    if command.startswith(LIST_COMMAND):
        response = "There {} currently {} player{} logged into the server{}.".format(
            'is' if len(current_players) == 1 else 'are',
            len(current_players),
            '' if len(current_players) == 1 else 's',
            '' if len(current_players) == 0 else ': {}'.format(', '.join(current_players)))
    post_message(response)

def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == '__main__':
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        # If we're connected, get the most recent server log message we've seen
        try:
            with open('latest_timestamp.txt', 'r+') as f:
                timestamp_float = float(f.read().strip())
                most_recent_timestamp = datetime.fromtimestamp(timestamp_float)
        except IOError, e:
            most_recent_timestamp = datetime.min

        with open('/home/minecraft/frontporch/logs/latest.log') as f:
            while True:
                command, channel = parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    # first, respond to in-Slack messages
                    handle_command(command, channel)
                    time.sleep(READ_WEBSOCKET_DELAY)
                else:
                    # else, read server logs and process them
                    line = f.readline()
        
                    timestamp_match = timestamp_pattern.match(line)
                    if timestamp_match:
                        line_datetime = datetime.strptime(timestamp_match.group(1), TIMESTAMP_FORMAT)
        
                    if line_datetime <= most_recent_timestamp:
                        continue
        
                    chat_match = chat_pattern.match(line)
                    if chat_match:
                        timestamp, user, message = chat_match.groups()
        		post_message('{} said: {}'.format(user, message))
                        remember_timestamp(timestamp)
                        continue
                    
                    join_match = join_pattern.match(line)
                    if join_match:
                        timestamp, user, message = join_match.groups()
        		post_message('{} {}'.format(user, message))
                        remember_timestamp(timestamp)
                        current_players.add(user)
                        continue
                    
                    left_match = left_pattern.match(line)
                    if left_match:
                        timestamp, user, message = left_match.groups()
        		post_message('{} {}'.format(user, message))
                        remember_timestamp(timestamp)
                        current_players.remove(user)
                        continue
                    
                    for pattern in broadcast_patterns:
                        maybe_match = pattern.match(line)
                        if maybe_match:
                            timestamp, user, message = maybe_match.groups()
                            post_message('{} {}'.format(user, message))
                            remember_timestamp(timestamp)
                            continue
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
