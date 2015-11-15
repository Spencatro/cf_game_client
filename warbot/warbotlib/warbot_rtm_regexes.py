import re

__author__ = 'shawkins'

SHOW_ME_THE_PIPELINE = re.compile(".*pipeline.*")
WATCH_MY_WAR = re.compile(".*war.*|.*points.*")
HELP = re.compile(".*help.*")
REGISTER = re.compile(".*register.*")
WHO_IS = re.compile(".*who owns.*|.*who is.*")
END_OF_BEIGE = re.compile(".*beige.*|.*i can fight.*")
UNBEIGE = re.compile(".*unbeige.*")