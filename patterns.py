import re

timestamp_pattern = re.compile(r'^\[(.*?)\].*?$')
chat_pattern = re.compile(r'^\[(.*?)\].*?\:\ \<(.*?)\>\ (.*?)$')
join_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (joined the game)$')
left_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (left the game)$')
died_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (was.*?|walked.*?|drowned.*?|experienced.*?|blew.*?|hit.*?|fell.*?|went.*?|burned.*?|tried.*?|discovered.*?|got.*?|starved.*?|suffocated.*?|withered.*?)$')
achievement_pattern = re.compile(r'^\[(.*?)\].*?\:\ (.*?) (has just earned.*?)$')
broadcast_patterns = [
    died_pattern,
    achievement_pattern
]

