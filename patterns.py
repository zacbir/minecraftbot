import re

timestamp_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?$')
chat_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?\:\ \<(?P<user>.*?)\>\ (?P<message>.*?)$')
join_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?\:\ (?P<user>.*?) (?P<message>joined the game)$')
left_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?\:\ (?P<user>.*?) (?P<message>left the game)$')
died_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?\:\ (?P<user>.*?) (?P<message>was.*?|walked.*?|drowned.*?|experienced.*?|blew.*?|hit.*?|fell.*?|went.*?|burned.*?|tried.*?|discovered.*?|got.*?|starved.*?|suffocated.*?|withered.*?)$')
achievement_pattern = re.compile(r'^\[(?P<timestamp>.*?)\].*?\:\ (?P<user>.*?) (?P<message>has just earned.*?)$')
slack_pattern = re.compile(r'^(?P<addressee><\@\S+\>)\:*\ (?P<command>.*?)$')
broadcast_patterns = [
    died_pattern,
    achievement_pattern
]

