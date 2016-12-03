import argparse
from datetime import datetime
import os
import os.path
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

class MinecraftBot:
    """ A Slack-bot for reporting on and interacting with a multiplayer Minecraft server.
    
        The bot will read the latest.log and report to the Slack channel player-centered events, such as:
        
          - Joins
          - Departs
          - Achievements
          - Deaths
          - In-game chat
        
        In addition, the bot will respond to commands. Currently, the commands understood are:
        
          - list: list the currently logged-in players
        
    """
    
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose

    def __init__(self, bot_id, slack_client, server_directory, channel="#general"):
        """ Create a Minecraft bot. It requires a few bits to get going:
        
              - bot_id: the non-human-readable id of the bot
              - slack_client: an initialized SlackClient (created with your bot's API key)
              - server_directory: the path to the Minecraft server's directory
              - channel: the name of the channel to send messages (defaults to #general)
        """
        
        self.bot_id = bot_id
        self.at_bot = "<@{}>".format(self.bot_id)
        self.slack_client = slack_client
        self.server_directory = server_directory
        self.latest_log = os.path.join(self.server_directory, 'logs', 'latest.log')
        self.most_recent_timestamp_file = os.path.join(self.server_directory, 'latest_timestamp.txt')
        self.channel = channel
        self.most_recent_timestamp = self.find_most_recent_timestamp()
        self.current_players = set()
        self.commands = {'list': self.list_current_players}

    def find_most_recent_timestamp(self):
        """ Set the most recent timestamp seen by the bot """
        try:
            with open(self.most_recent_timestamp_file) as f:
                timestamp_float = float(f.read().strip())
                most_recent_timestamp = datetime.fromtimestamp(timestamp_float)
        except IOError, e:
            most_recent_timestamp = datetime.min
        
        return most_recent_timestamp
        
    def post_message(self, message, channel=None):
        """ Post a message to the the channel as our bot """
        self.slack_client.api_call(
            'chat.postMessage',
            channel=channel or self.channel,
            text=message,
            as_user=True,
            link_names=True,
            username=self.bot_id)
    
    def remember_timestamp(self, timestamp):
        """ Record the timestamp from a given log line as its mktime float """
        d = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        seconds_timestamp = time.mktime(d.timetuple())

        with open(self.most_recent_timestamp_file, 'w') as f:
            f.write(str(seconds_timestamp))

    def parse_slack_output(self, slack_rtm_output):
        """ Parse the output of the Slack Real-Time Messaging firehose
        
            Look for messages directed at our bot (using the self.at_bot marker), and return the relevant information
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output and self.at_bot in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(self.at_bot)[1].strip().lower(), \
                           output['channel']
        return None, None

    def handle_command(self, command, channel):
        """ Process the command given from a channel and write back to same.
        
            If the command is not understoon, return a helpful message.
        """
        command_args = command.split(' ', 1)
        command, args = command_args if len(command_args) > 1 else command_args[0], None
        handler = self.commands.get(command, self.unknown_command)
        response = handler(args)
        self.post_message(response, channel)
        
    def run(self):
        """ The main loop - read from the Slack RTM firehose, and also keep an eye on the server's latest.log """
        if self.slack_client.rtm_connect():
            with open(self.latest_log) as f:
                while True:
                    command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                    if command and channel:
                        # first, respond to in-Slack messages
                        self.handle_command(command, channel)
                        time.sleep(self.READ_WEBSOCKET_DELAY)
                    else:
                        # else, read server logs and process them
                        line = f.readline()
        
                        timestamp_match = timestamp_pattern.match(line)
                        if timestamp_match:
                            line_datetime = datetime.strptime(timestamp_match.group(1), TIMESTAMP_FORMAT)
        
                        if line_datetime <= self.most_recent_timestamp:
                            continue
        
                        chat_match = chat_pattern.match(line)
                        if chat_match:
                            timestamp, user, message = chat_match.groups()
                            self.post_message('{} said: {}'.format(user, message))
                            self.remember_timestamp(timestamp)
                            continue
                    
                        join_match = join_pattern.match(line)
                        if join_match:
                            timestamp, user, message = join_match.groups()
                            self.post_message('{} {}'.format(user, message))
                            self.remember_timestamp(timestamp)
                            self.current_players.add(user)
                            continue
                    
                        left_match = left_pattern.match(line)
                        if left_match:
                            timestamp, user, message = left_match.groups()
                            self.post_message('{} {}'.format(user, message))
                            self.remember_timestamp(timestamp)
                            self.current_players.remove(user)
                            continue
                    
                        for pattern in broadcast_patterns:
                            maybe_match = pattern.match(line)
                            if maybe_match:
                                timestamp, user, message = maybe_match.groups()
                                self.post_message('{} {}'.format(user, message))
                                self.remember_timestamp(timestamp)
                                continue
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

    # Commands

    def unknown_command(self):
        """ The default response for commands the bot doesn't understand. """
        return "So far, all I know how to do is `list`! Tell @zacbir to add more smarts!"

    def list_current_players(self):
        """ List the currently logged in users """
        current_players = self.current_players
        response = "There {} currently {} player{} logged into the server{}.".format(
            'is' if len(current_players) == 1 else 'are',
            len(current_players),
            '' if len(current_players) == 1 else 's',
            '' if len(current_players) == 0 else ': {}'.format(', '.join(current_players)))
        return response
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch a bot to communicate information about a shared Minecraft server to Slack')
    parser.add_argument('-d', '--directory', help="The directory where the Minecraft server lives")
    args = parser.parse_args()

    api_key = os.environ.get('SLACK_API_KEY')
    slack_client = SlackClient(api_key)

    minecraft_bot = MinecraftBot(
        os.environ.get('SLACK_BOT_ID'),
        slack_client,
        args.directory)
        
    minecraft_bot.run()
