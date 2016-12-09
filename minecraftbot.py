import argparse
from datetime import datetime
import os
import os.path
import signal
import subprocess
import sys
import time

from slackclient import SlackClient

from patterns import *

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


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
        self.slack_client = slack_client
        self.server_directory = server_directory
        self.server_process = None
        self.most_recent_timestamp_file = os.path.join(self.server_directory, 'latest_timestamp.txt')
        self.channel = channel
        self.most_recent_timestamp = self.find_most_recent_timestamp()
        self.current_players = set()
        self.commands = {
            'launch': self.command_launch_server,
            'list': self.command_list_current_players,
            'restart': self.command_restart_server,
            'stop': self.command_stop_server,
            'whitelist': self.command_whitelist_user,
        }
        self.log_parsers = {
            chat_pattern: self.handle_chat,
            join_pattern: self.handle_join,
            left_pattern: self.handle_left,
            died_pattern: self.handle_broadcast,
            achievement_pattern: self.handle_broadcast,
        }
        self.launch_args = ['java', '-Xmx1024M', '-Xms1024M', '-Dlog4j.configurationFile=custom-log4j2.xml', '-jar', 'current.jar', 'nogui']
        signal.signal(signal.SIGINT, self.handle_signal)

    # Bot/server

    def run(self):
        """ The main loop - read from the Slack RTM firehose, and also keep an eye on the server's stdout """
        if self.slack_client.rtm_connect():
            while True:
                command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                if command and channel:
                    # first, respond to in-Slack messages
                    self.handle_command(command, channel)
                    time.sleep(self.READ_WEBSOCKET_DELAY)
                elif self.server_process and self.server_process.poll() is None:
                    # else, read server logs and process them
                    line = self.server_process.stdout.readline()
                    print line.strip()
                    line_datetime = datetime.min

                    timestamp_match = timestamp_pattern.match(line)
                    if timestamp_match:
                        line_datetime = datetime.strptime(timestamp_match.group(1), TIMESTAMP_FORMAT)

                    if line_datetime > self.most_recent_timestamp:
                        for pattern, handler in self.log_parsers.items():
                            maybe_match = pattern.match(line)
                            if maybe_match:
                                handler(maybe_match.groups())
                    time.sleep(0.1)

        else:
            print("Connection failed. Invalid Slack token or bot ID?")

    def launch_server(self):
        """ Launch the server """
        if not self.server_process:
            self.server_process = subprocess.Popen(self.launch_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Started server with pid {}".format(self.server_process.pid))

    def stop_server(self):
        """ Stop the server """
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.current_players.clear()

    def find_most_recent_timestamp(self):
        """ Set the most recent timestamp seen by the bot """
        try:
            with open(self.most_recent_timestamp_file) as f:
                timestamp_float = float(f.read().strip())
                most_recent_timestamp = datetime.fromtimestamp(timestamp_float)
        except IOError, e:
            most_recent_timestamp = datetime.min
        
        return most_recent_timestamp
        
    def remember_timestamp(self, timestamp):
        """ Record the timestamp from a given log line as its mktime float """
        most_recent_timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        seconds_timestamp = time.mktime(most_recent_timestamp.timetuple())

        with open(self.most_recent_timestamp_file, 'w') as f:
            f.write(str(seconds_timestamp))

    def post_message(self, message, channel=None):
        """ Post a message to the the channel as our bot """
        self.slack_client.api_call(
            'chat.postMessage',
            channel=channel or self.channel,
            text=message,
            as_user=True,
            link_names=True,
            username=self.bot_id)
    
    def parse_slack_output(self, slack_rtm_output):
        """ Parse the output of the Slack Real-Time Messaging firehose
        
            Look for messages directed at our bot and return the relevant information
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output:
                    print(u"Channel output: {}".format(output['text']))
                    maybe_match = slack_pattern.match(output['text'])
                    if maybe_match and maybe_match.group('addressee') == self.bot_id:
                        # return text after the @ mention, whitespace removed
                        print(u"Found a command for me! {}".format(maybe_match.groups()))
                        return maybe_match.group('command').lower(), output['channel']
        return None, None

    def handle_command(self, command, channel):
        """ Process the command given from a channel and write back to same.
        
            If the command is not understoon, return a helpful message.
        """
        command_args = command.split(' ')
        command = command_args[0]
        args = command_args[1:] if len(command_args) > 1 else []
        handler = self.commands.get(command, self.command_unknown)
        response = handler(*args)
        self.post_message(response, channel)

    def handle_signal(self, signum, frame):
        """ Handle SIGINT, primarily """
        self.post_message("Stopping bot, shutting down server!")
        self.stop_server()
        sys.exit()

    # Commands

    def command_unknown(self, *args, **kw):
        """ The default response for commands the bot doesn't understand. """
        return "So far, the commands I recognize are: {}! Tell @zacbir to add more smarts!".format(
            ', '.join(['`{}`'.format(x) for x in sorted(self.commands)])
        )

    def command_list_current_players(self, *args, **kw):
        """ List the currently logged in users """
        if not self.server_process:
            return "The server isn't running right now"
        current_players = self.current_players
        response = "There {} currently {} player{} logged into the server{}.".format(
            'is' if len(current_players) == 1 else 'are',
            len(current_players),
            '' if len(current_players) == 1 else 's',
            '' if len(current_players) == 0 else ': {}'.format(', '.join(current_players)))
        return response

    def command_launch_server(self, *args, **kw):
        """ Command handler for launching the server """
        response = "Server already running" if self.server_process else "Launching Server"
        self.launch_server()
        return response

    def command_stop_server(self, *args, **kw):
        """ Command handler for stopping the server """
        response = "Stopping server" if self.server_process else "Server not running"
        self.stop_server()
        return response

    def command_restart_server(self, *args, **kw):
        """ Restart the server, stopping it first, if necessary """
        response = "Restarting server" if self.server_process else "Starting server"
        self.stop_server()
        self.launch_server()
        return response

    def command_whitelist_user(self, *args, **kw):
        """ Whitelist a user """
        user = args[0]

        self.server_process.stdin.write('/whitelist add {}'.format(user))
        return "Whitelisted {}".format(user)

    # Log line parsers

    def handle_chat(self, groups):
        timestamp, user, message = groups
        self.post_message('{} said: {}'.format(user, message))
        self.remember_timestamp(timestamp)

    def handle_join(self, groups):
        timestamp, user, message = groups
        self.post_message('{} {}'.format(user, message))
        self.remember_timestamp(timestamp)
        self.current_players.add(user)

    def handle_left(self, groups):
        timestamp, user, message = groups
        self.post_message('{} {}'.format(user, message))
        self.remember_timestamp(timestamp)
        self.current_players.discard(user)

    def handle_broadcast(self, groups):
        timestamp, user, message = groups
        self.post_message('{} {}'.format(user, message))
        self.remember_timestamp(timestamp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch a bot to communicate information about a shared Minecraft server to Slack')
    parser.add_argument('-d', '--directory', help="The directory where the Minecraft server lives")
    parser.add_argument('-c', '--channel', help="The name of the channel where the Minecraft bot should report to")
    args = parser.parse_args()

    api_key = os.environ.get('SLACK_API_KEY')
    slack_client = SlackClient(api_key)

    channel = args.channel or '#general'

    minecraft_bot = MinecraftBot(
        os.environ.get('SLACK_BOT_ID'),
        slack_client,
        args.directory,
        channel = channel)
    
    minecraft_bot.run()
