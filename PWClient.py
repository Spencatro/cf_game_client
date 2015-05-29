from urllib import urlencode, quote_plus, quote
import datetime
from datetime import timedelta
import httplib2
import os
import time
import lxml.etree as ET
import re
import logging
import sys

__author__ = 'sxh112430'

DEBUG_LEVEL_MEGA_VERBOSE = 3
DEBUG_LEVEL_PRETTY_VERBOSE = 2
DEBUG_LEVEL_SORTA_VERBOSE = 1
DEBUG_LEVEL_STFU = 0

BEIGE_CREATION_TIMEDELTA = timedelta(days=14, hours=2)
BEIGE_WAR_TIMEDELTA = timedelta(days=5, hours=2)

def stringify_children(node):
    from lxml.etree import tostring
    from itertools import chain
    parts = ([node.text] +
            list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
            [node.tail])
    # filter removes possible Nones in texts and tails
    return ''.join(filter(None, parts))

class NationDoesNotExistError(Exception): pass
class WhyIsNationInBeige(Exception): pass

class War:
    def __init__(self, war_id, aggressor_id, defender_id,date_started,date_ended = None, winner_id = None, last_nuclear_strike_against = {}):
        self.war_id = war_id
        self.aggressor = aggressor_id
        self.defender = defender_id
        self.in_progress = False
        self.date_started = date_started
        self.date_ended = date_ended
        self.winner_id = winner_id
        self.last_nuclear_strike_against = last_nuclear_strike_against

        if winner_id is None:
            self.in_progress = True

    def set_winner(self, winner_id, date_ended):
        self.in_progress = False
        self.winner_id = winner_id
        self.date_ended = date_ended

    def can_contribute_to_beige(self, current_date):
        if self.in_progress:
            return False
        if self.date_ended is None:
            return False
        assert isinstance(current_date, datetime)
        time_difference = current_date - self.date_ended
        seconds = time_difference.total_seconds()
        if seconds < timedelta(days=14).total_seconds():
            return True
        return False

    def __str__(self):
        representation = "<War: "+str(self.war_id) + ", winner:"
        if self.in_progress:
            representation += " inconclusive"
        else:
            representation += str(self.winner_id)
        representation += ", nuclear war: "+str(len(self.last_nuclear_strike_against.keys()) > 0)+">"
        return str(representation)

    def __repr__(self):
        return self.__str__()


class Military:
    nukes = 0
    missiles = 0
    spies = 0
    ships = 0
    aircraft = 0
    tanks = 0
    soldiers = 0

    def get_score(self):
        score = self.soldiers*0.0005 + self.tanks * 0.02 + self.aircraft * 0.2 + self.ships * 1.5 + self.missiles * 5 + self.nukes * 50
        return score

    def __cmp__(self, other):
        diff = other.get_score() - self.get_score()
        if diff < 0:
            return 1
        elif diff == 0:
            return 0;
        else:
            return -1

    def __str__(self):
        return "Military Score: "+str(self.get_score())

    def __repr__(self):
        return self.__str__()


class Nation:
    military = None
    score = None
    rank = None
    pollution_index = None
    infrastructure = None
    land_area = None
    population = None
    govt_type = None
    alliance_id = None
    alliance_name = None
    color = None
    uid = None
    founded_date = None
    leader = None
    name = None
    n_id = None
    time_since_active = None
    precisely_founded = False

    warrable_list = []

class PWClient:

    __last_request_timestamp = 0
    __root_url = "https://politicsandwar.com"
    __username = None
    __password = None

    nation_cache = {}
    alliance_cache = {}

    def __init__(self, username, password, logger=None):
        self.debug = DEBUG_LEVEL_STFU
        self.http = httplib2.Http()
        self.headers = { 'Accept': 'text/html',
                         'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36' }
        self.__username = username
        self.__password = password
        self.__using_db = False

        self.__authenticate__()
        if logger is None:
            logger = logging.getLogger("PWClient")
            hndl = logging.StreamHandler(sys.stdout)
            logger.addHandler(hndl)
            logger.setLevel(logging.INFO)
        self.logger = logger

    def __authenticate__( self ):
        self._print(1, "Starting authentication as:",self.__username)
        r,c = self.__make_http_request(self.__root_url+'/login/', body={'email':self.__username, 'password':self.__password, 'sesh':'', 'loginform':'Login'}, request_type='POST')
        if "Login Failure" in c:
            raise Exception("Failure to authenticate!")
        if not 'set-cookie' in r:
            self._print(1, "Already authed?")
            return
        self.headers['Cookie'] = r['set-cookie']
        self._print(1, "Authentication success!")

    def __query_timecheck(self):
        current_timestamp = int(round(time.time() * 1000))
        time_difference = current_timestamp - self.__last_request_timestamp
        if time_difference < 10:
            # wait 10 ms between queries, so as not to be banned I guess??
            ratio = time_difference / 1000
            if ratio < 0:
                ratio = 0
                print "WTF HAPPENED"
            time.sleep(ratio)
        self.__last_request_timestamp = time.time() * 1000

    def __make_http_request( self, url, body = None, request_type = 'GET' ):
        self._print(2, "Making HTTP request for: ",url)
        self.__query_timecheck()
        r_headers = self.headers
        if(request_type == 'POST' or request_type == 'PUT'):
            r_headers['Content-type']= 'application/x-www-form-urlencoded'

        if body != None:
            body = urlencode(body)
        try:
            response, content = self.http.request(url, request_type, body = body, headers = r_headers)
        except (Exception, SystemExit ) as e:
            raise
        return response, content

    def _print( self, debug_level, *kwargs ):
        if self.debug >= debug_level:
            logstring = ""
            for arg in kwargs:
                print arg,
                logstring += str(arg)+" "
            print ""
            self.logger.info(logstring)

    def _retrieve_leftcolumn(self):
        self._print("Retrieving leftcolumn")
        status,content = self.__make_http_request(self.__root_url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)
        leftcolumn = tree.find(".//div[@id='leftcolumn']")
        return leftcolumn

    def _retrieve_nationtable(self, url, idx=0):
        self._print(1, "Retrieving nationtable for:",url)
        status,content = self.__make_http_request(url)
        if "That nation does not exist." in content:
            raise NationDoesNotExistError(url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)
        nationtables = tree.findall(".//table[@class='nationtable']")
        return nationtables[idx]

    # TODO: get alliance info
    # TODO: get list of nation ID's from alliance ID
    # TODO: get list of nations who can declare against particular nation ID
    # TODO: consider downloading all ~3000 nations first, then parsing all the data after?

    def _generate_full_query_list(self, url, minimum=0, maximum=50):
        # Note: DO NOT INCLUDE &maximum=n&minimum=m in this url! They will be calculated and added in here!
        min_max_url = url
        # only modify this url, will need original unused url for later
        min_max_url += "&ob=score&maximum="+str(maximum)+"&minimum="+str(minimum)+"&search=Go"

        nationtable = self._retrieve_nationtable(min_max_url)

        more_pages = False
        for tr in nationtable.findall(".//tr"):
            self._print(3,">tr", len(tr))
            if tr[0].text is not None and re.search('[0-9]+\)', tr[0].text):
                href = tr[1][0].attrib['href']
                eq_idx = href.index("=")
                n_id = int(href[eq_idx+1:])
                nation_idx = int(tr[0].text.replace(')','').replace(',',''))
                yield self.get_nation_obj_from_ID(n_id)
                more_pages = True

        if more_pages:
            for nation in self._generate_full_query_list(url, minimum=minimum+maximum):
                yield nation

    def _get_param_from_url(self, url_string, param):
        # TODO: use this where appropriate
        param += "="
        idx = url_string.index(param) + len(param)
        url_string = url_string[idx:]
        try:
            end_idx = url_string.index('&')
        except:
            end_idx = len(url_string)
        return url_string[:end_idx].strip()

    def set_db(self, db):
        # TOOD: this
        # self.__using_db = True
        raise Exception("Unimplemented, sry")
        pass

    def get_dict_of_alliance_members_from_name(self, a_name):
        self._print(2, "Getting dict for alliance name:",a_name)
        query_url = self.__root_url + "/index.php?id=15&keyword="+quote_plus(str(a_name))+"&cat=alliance"
        full_dict = {}
        for nation in self._generate_full_query_list(query_url):
            assert isinstance(nation, Nation)
            n = Nation
            full_dict[nation.n_id] = nation
        return full_dict

    def generate_all_nations_with_color(self, color):
        query_url = self.__root_url + "/index.php?id=15&keyword="+color+"&cat=color"
        for nation in self._generate_full_query_list(query_url):
            yield nation


    def get_list_of_alliance_members_from_ID(self, a_id):
        a_name = self.get_alliance_name_from_ID(a_id)
        return self.get_dict_of_alliance_members_from_name(a_name)

    def get_alliance_name_from_ID(self, a_id):
        self._print(2, "Getting alliance name from id:",a_id)
        alliance_url = self.__root_url + "/alliance/id="+str(a_id)

        status,content = self.__make_http_request(alliance_url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)

        title_obj = tree.find(".//td[@style='text-align:center; font-weight:bold; width:260px;']")
        title = title_obj.text

        self._print(2, "Alliance name found: ",title)
        return title

    def get_nation_name_from_id(self, n_id):
        if n_id in self.nation_cache.keys():
            return self.nation_cache[n_id].name
        n = self.get_nation_obj_from_ID(n_id)
        return n.name

    def get_next_turn_in_datetime(self, reftime=None):
        if reftime is None:
            leftcol = self._retrieve_leftcolumn()
            datestring = str(leftcol[4][1].tail).strip()
            now_year = datetime.datetime.now().year
            reftime = datetime.datetime.strptime(datestring+" "+str(now_year), "%B %d %I:%M %p %Y")
        if reftime.hour % 2 == 0:
            reftime += timedelta(hours=1, minutes=60-reftime.minute)
        return reftime

    def get_current_date_in_datetime(self):
        leftcol = self._retrieve_leftcolumn()
        datestring = str(leftcol[4][1].tail).strip()
        now_year = datetime.datetime.now().year
        dt = datetime.datetime.strptime(datestring+" "+str(now_year), "%B %d %I:%M %p %Y")
        return dt

    def get_nation_obj_from_ID(self, n_id, skip_cache = False):
        # TODO: put a time check on last pull, in case this script ends up being used in ways that take long periods of time
        self._print(2, "Getting nation from ID:",n_id)
        if not skip_cache: # Sometimes may want to force-skip cache
            if n_id in self.nation_cache.keys():
                self._print(2, "Cache hit on ",n_id,"! Skipping download")
                return self.nation_cache[n_id]

        # Not in cache, go pull data
        url = self.__root_url + "/nation/id="+str(n_id)
        nationtable = self._retrieve_nationtable(url)

        nation = Nation()
        military = Military()

        nation.n_id = n_id

        for tr in nationtable.findall(".//tr"):
            self._print(3,">tr", len(tr))
            td_key_text = str(tr[0].text).strip()
            td_key_tag = str(tr[0].tag).strip()
            if td_key_text == "Nation Name:":
                nation.name = tr[1].text
                self._print(3,"FOUND: Nation name:",tr[1].text)
            elif td_key_text == "Leader Name:":
                nation.leader = tr[1].text
                self._print(3,"FOUND: Leader name:",tr[1].text)
            elif td_key_text == "Founded:":
                date_string = tr[1].text.split(" ")[0]
                date_obj = datetime.datetime.strptime(date_string, "%m/%d/%Y")
                nation.founded_date = date_obj
                self._print(3,"FOUND: Founded:",date_obj)
            elif td_key_text == "Last Activity:":
                activity_text = tr[1].text
                # TODO: transform this into a datetime
                nation.time_since_active = activity_text
                self._print(3,"FOUND: Last active:",tr[1].text)
            elif td_key_text == "Unique ID:":
                uid = tr[1].text
                nation.uid = tr[1][0].text
                self._print(3,tr[1][0].attrib['href'])
                self._print(3,"FOUND: UID:", tr[1][0].text)
            elif td_key_text == "National Color:":
                self._print(3,"FOUND COLOR:", tr[1][0][0].text)
                nation.color = tr[1][0][0].text.strip()
            elif td_key_text == "Alliance:":
                if len(tr[1]) > 0:
                    nation.alliance_name = tr[1][0].text
                    href = str(tr[1][0].attrib['href'])
                    idx = href.index('=')
                    a_id = href[idx+1:len(href)]
                    nation.alliance_id = int(a_id)
                    self._print(3,"Found A_ID:", href, a_id)
                else:
                    self._print(3,"No a_id")
                    nation.alliance_id = None
            elif td_key_text == "Government Type:":
                # ....don't ask, something is up with the parser
                # Edit: Okay it looks like any td with a question mark needs to be indexed weird
                # Normally it's tr[1], but for '?' td's, it's tr[0][1]. I don't know why.
                # Parser is probably mad at bad HTML.
                self._print(3,"Found Govt type:", tr[0][1].text)
                nation.govt_type = str(tr[0][1].text).strip()
            elif td_key_text == "Population:":
                population = str(tr[1].text.replace(',','')).strip()
                self._print(3,"Found pop:",population)
                nation.population = int(population) # get rid of commas
            elif td_key_text == "Land Area:":
                land = str(tr[0][1].text.replace(',','')).strip()
                idx = land.index("sq")-1
                land = land[:idx]
                self._print(3,"Found land area:", land)
                nation.land_area = int(land) # get rid of commas
            elif td_key_text == "Infrastructure:":
                inf = float(tr[0][1].text.replace(',',''))
                self._print(3,"Found infra:",inf)
                nation.infrastructure = inf
            elif td_key_text == "Pollution Index:":
                pollution_string = str(tr[0][1].text).strip()
                idx = pollution_string.index(" ")
                pollution = int(pollution_string[:idx].replace(',',''))
                self._print(3,"Found pollution:",pollution)
                nation.pollution_index = pollution
            elif td_key_text == "Nation Rank:":
                idx = tr[1].text.index(" of")
                rank = tr[1].text[1:idx].replace(',','')
                nation.rank = int(rank)
                self._print(3,"Found nation rank:", tr[1].text, rank)
            elif td_key_text == "Nation Score:":
                self._print(3,"Found nation score:",tr[1].text)
                score = float(tr[1].text.replace(",",""))
                nation.score = score

            elif td_key_text == "Soldiers:":
                soldiers = tr[1].text.replace(',','')
                military.soldiers = int(soldiers)
                self._print(3,"Found soldiers:",military.soldiers)

            elif td_key_text == "Tanks:":
                tanks = tr[1].text.replace(',','')
                military.tanks = int(tanks)
                self._print(3,"Found tanks:",military.tanks)

            elif td_key_text == "Aircraft:":
                aircraft = tr[1].text.replace(',','')
                military.aircraft = int(aircraft)
                self._print(3,"Found aircraft:",military.aircraft)

            elif td_key_text == "Ships:":
                ships = tr[1].text.replace(',','')
                military.ships = int(ships)
                self._print(3,"Found ships:",military.ships)

            elif td_key_text == "Spies:":
                spies = tr[1].text.replace(',','')
                military.spies = int(spies)
                self._print(3,"Found spies:",military.spies)

            elif td_key_text == "Missiles:":
                missiles = tr[1].text.replace(',','')
                military.missiles = int(missiles)
                self._print(3,"Found missiles:",military.missiles)

            elif td_key_text == "Nuclear Weapons:":
                nukes = tr[1].text.replace(',','')
                military.nukes = int(nukes)
                self._print(3,"Found nukes:",military.nukes)

            # TODO: scrape projects
            else:
                found_something = False
                try:
                    for obj in tr[0][0]:
                        if "was created!" in obj.tail:
                            now_year = datetime.datetime.now().year
                            creation_string = tr[0][0].text[:-3]+" "+str(now_year)
                            format_string = "%m/%d %I:%M %p %Y"
                            created_obj = datetime.datetime.strptime(creation_string, format_string)
                            found_something = True
                            nation.founded_date = created_obj
                            nation.precisely_founded = True
                            self._print(3, "Found more precise founded date:",created_obj)
                except:
                    pass
                finally:
                    if not found_something:
                        self._print(3, "Unknown key:",td_key_tag, td_key_text)
        nation.military = military
        self.nation_cache[n_id] = nation
        return nation

    def check_nation_for_wars(self, nation_id):
        if not self.__using_db:
            raise Exception("Can't do this because not using a database")

        war_url = self.__root_url + "/nation/id="+str(nation_id)+"&display=war"
        nationtable = self._retrieve_nationtable(war_url)

        for tr in nationtable.findall(".//tr"):
            if tr[0].text == "Date":
                continue # skip empty row
            date = tr[0].text
            aggressor_url = tr[1][0].attrib['href']
            aggressor = self._get_param_from_url(aggressor_url, "id")
            defender_url = tr[2][0].attrib['href']
            defender = self._get_param_from_url(defender_url, "id")
            war_state = tr[3][0].text
            query_dict = {'aggressor':aggressor, 'defender':defender, 'date':date}
            war_cursor = self.wars_collection.find(query_dict)
            if war_cursor.count() == 0:
                query_dict['war_state'] = war_state
                # TODO: replace this print with an actual notification
                print "Notification! Inserting into colleciton: ",query_dict
                print "Aggressor:", self.get_nation_name_from_id(aggressor)
                print "Defender:", self.get_nation_name_from_id(defender)
                self.wars_collection.insert(query_dict)
                # TODO: insert into db
            else:
                db_war_obj = war_cursor.next()
                db_war_state = db_war_obj['war_state']
                if db_war_state != war_state:
                    # TODO: make a notification
                    print "------------------------"
                    print "Notification! Old state: ",db_war_obj
                    print "Aggressor:", self.get_nation_name_from_id(aggressor)
                    print "Defender:", self.get_nation_name_from_id(defender)
                    db_war_obj['war_state'] = war_state
                    print "New state: ",db_war_obj

    def check_alliance_for_wars(self, a_id):
        alliance_list = self.get_list_of_alliance_members_from_ID(a_id)
        for n_id in alliance_list:
            self.check_nation_for_wars(n_id)

    def check_alliance_for_warrable_inactives(self, a_id):
        alliance_list = self.get_list_of_alliance_members_from_ID(a_id)
        nation_scores = [alliance_list[nation_key].score for nation_key in alliance_list]
        all_warrable_nations = []
        for nation_key in alliance_list:
            nation = alliance_list[nation_key]
            query_url = self.__root_url + "/index.php?id=15&keyword="+str(nation.score)+"&cat=war_range&ob=score&od=ASC&search=Go"
            for other_nation in self._generate_full_query_list(query_url):
                assert isinstance(other_nation, Nation)
                if not nation.n_id in other_nation.warrable_list:
                    other_nation.warrable_list.append(nation.n_id)
                if not other_nation.n_id in all_warrable_nations:
                    all_warrable_nations.append(other_nation.n_id)
        for n_id in all_warrable_nations:
            n_obj = self.get_nation_obj_from_ID(n_id)

    def queue_new_notification(self, to, subject, body, seconds_until_notification):
        url = "http://radiofreaq.spencer-hawkins.com:5000/queue_n/"+quote(to)+"/"+quote(subject)+"/"+quote(body)+"/"+quote(str(seconds_until_notification))+"/"
        self._print(2, "Making new notification req: ", url)
        self._print(3, self.__make_http_request(url))

    def calculate_beige_exit_time(self, n_id):
        nation = self.get_nation_obj_from_ID(n_id)
        if nation.color != "Beige":
            raise Exception("Error: nation is not in beige!")
        recent_wars = self.get_most_recent_wars(n_id)
        last_lost_date = None
        for lost_war in [r_war for r_war in recent_wars if not r_war.in_progress and str(r_war.winner_id) != str(n_id) or str(n_id) in r_war.last_nuclear_strike_against.keys()]:
            assert isinstance(lost_war, War)
            if not lost_war.in_progress and lost_war.winner_id != str(n_id):
                if last_lost_date is None or last_lost_date < lost_war.date_ended:
                    last_lost_date = lost_war.date_ended
            if len(lost_war.last_nuclear_strike_against) > 0:
                if str(n_id) in lost_war.last_nuclear_strike_against.keys():
                    nuke_time = lost_war.last_nuclear_strike_against[str(n_id)]
                    if last_lost_date is None or last_lost_date < nuke_time:
                        last_lost_date = nuke_time
        if last_lost_date is not None and self.get_next_turn_in_datetime() - self.get_next_turn_in_datetime(last_lost_date) <= BEIGE_WAR_TIMEDELTA:
            return last_lost_date + BEIGE_WAR_TIMEDELTA
        # wasn't a war that kicked into beige, must be creation date
        if self.get_next_turn_in_datetime() - self.get_next_turn_in_datetime(nation.founded_date) <= BEIGE_CREATION_TIMEDELTA:
            return nation.founded_date + BEIGE_CREATION_TIMEDELTA
        raise WhyIsNationInBeige("ERROR: Nation "+str(n_id)+" shouldn't be in beige...??!?!?")

    def get_war_obj_from_id(self, war_id):
        # idx = 1 because on war screens there are actually 3 separate nationtables. We want the second, 0 indexed -> 1
        nationtable = self._retrieve_nationtable(self.__root_url+"/nation/war/timeline/war="+war_id,1)
        tr_list = nationtable.findall(".//tr")
        last_idx = len(tr_list) - 1

        first_fight = tr_list[0][0][0].text
        last_fight = tr_list[last_idx][0][0].text

        date_format = "%m/%d/%Y %I:%M %p"

        aggressor_id = self._get_param_from_url(tr_list[0][1][0][0].attrib['href'], "id")
        defender_id = self._get_param_from_url(tr_list[0][1][0][1].attrib['href'],"id")

        last_nuclear_strike_against = {} # key is target ID

        # TODO: find any battles that used a nuke
        for battle_idx in range(len(tr_list)):
            battle = tr_list[battle_idx]
            battle_description = stringify_children(battle[1][0])
            nuke = "nuclear weapon" in battle_description


            if nuke:
                nuke_time_string = battle[0][0].text
                nuke_time = datetime.datetime.strptime(nuke_time_string, date_format)
                nuke_launcher = self._get_param_from_url(battle[1][0][0].attrib['href'], "id")
                nuke_target = self._get_param_from_url(battle[1][0][1].attrib['href'], "id")
                # print "LAUNCHED BY ~~~~~~",nuke_launcher, "TARGETING",nuke_target, "AT",nuke_time
                if nuke_target not in last_nuclear_strike_against or last_nuclear_strike_against[nuke_target] < nuke_time:
                    last_nuclear_strike_against[nuke_target] = nuke_time

        last_fight_description = tr_list[last_idx][1][0][0].tail

        start_date = datetime.datetime.strptime(first_fight.strip(), date_format)
        end_date = datetime.datetime.strptime(last_fight.strip(), date_format)

        w = War(war_id, aggressor_id,defender_id,start_date,last_nuclear_strike_against=last_nuclear_strike_against)

        war_ended = False
        if "resulting in the immediate surrender" in last_fight_description:
            winner_id = self._get_param_from_url(tr_list[last_idx][1][0][0].attrib['href'], "id")
            war_ended = True
            w.set_winner(winner_id, end_date)

        return w

    def get_most_recent_wars(self, nation_id, defensive_only = False, offensive_only = False):
        if defensive_only and offensive_only:
            defensive_only = offensive_only = False # you're a doof why did you do "only both" sheesh

        war_url = self.__root_url + "/nation/id="+str(nation_id)+"&display=war"
        nationtable = self._retrieve_nationtable(war_url)

        war_list = []
        for tr in nationtable.findall(".//tr"):
            if "No wars to display" in stringify_children(tr): # empty warlist, just return
                return war_list
            if tr[0].text == "Date":
                continue # skip empty row
            if defensive_only and self._get_param_from_url(tr[1][0].attrib['href'], "id") == str(nation_id):
                continue # Skip offensive wars
            if offensive_only and self._get_param_from_url(tr[2][0].attrib['href'], "id") == str(nation_id):
                continue # skip defensive wars
            if len(war_list) > 5:
                return war_list

            a_tag = tr[3].find(".//a")
            war_id = a_tag.attrib['href']
            war_id = self._get_param_from_url(war_id, "war")
            war_list.append(self.get_war_obj_from_id(war_id))
        return war_list


if __name__ == "__main__":

    logger = logging.getLogger("pwc")
    fhandler1 = logging.FileHandler("pwc.out", mode='w')
    logger.addHandler(fhandler1)
    logger.setLevel(logging.INFO)

    USERNAME = os.environ['PWUSER']
    PASS = os.environ['PWPASS']
    pwc = PWClient(USERNAME, PASS, logger=logger)

    count = 0
    beiges_to_expire = []
    for beige in pwc.generate_all_nations_with_color('beige'):
        try:
            if pwc.calculate_beige_exit_time(beige.n_id) - pwc.get_current_date_in_datetime() < timedelta(hours=1):
                count += 1
                beiges_to_expire.append(beige.n_id)
                logger.info("")
                logger.info(str(beige.n_id) + " "+ str(beige.color) + " to expire in less than one hour")
                logger.info("")
            else :
                print ".",
            if count > 5:
                break
        except WhyIsNationInBeige:
            logger.info("\nshit this nation is in beige, why?? " + str(beige.n_id))
        except NationDoesNotExistError:
            logger.info( "\nshit this nation doesn't exist wat " + str(beige.n_id))

    logger.info( "reached the end of the list")
    time.sleep(60 * 60)

    for bte in beiges_to_expire:
        nation = pwc.get_nation_obj_from_ID(bte,skip_cache=True)
        logger.info( "Did nation expire? "+ str(nation.n_id)+ " "+str(nation.color))
    # raw_input("WAITING ...")
    #
    # na_id = 18672
    #
    # pwc.get_current_date_in_datetime()
    # pwc.get_nation_obj_from_ID(na_id)
    #
    # now = pwc.get_current_date_in_datetime()
    # print pwc.calculate_beige_exit_time(1979) - now
    #
    # raw_input("WAITING")
    #
    # ids = [
    #     996,3766,94,4834,202,1979,228,529,3805
    # ]
    # for n in ids:
    #     print n, pwc.calculate_beige_exit_time(n) - now
    #
    # war_list = pwc.get_most_recent_wars(na_id)
    #
    # print len(war_list)

    # pwc.calculate_beige_exit_time(na_id)
    # pwc.check_alliance_for_warrable_inactives(1356)

    # pwc.queue_new_notification("hawkins.spencer@gmail.com", "howdy from the pnw client!","what up??",20)

    # pwc.check_nation_for_wars(na_id)


    '''
    print "enter alliance name to search for:"
    alliance_search = raw_input()

    nation_list = pwc.get_dict_of_alliance_members_from_name(alliance_search)

    print "List of nations in "+alliance_search+":"

    mil_score = 0

    min_mil_nation = None
    max_mil_nation = None

    for nation_key in nation_list.keys():
        nation = nation_list[nation_key]
        assert isinstance(nation, Nation)
        print "-",nation.name
        mil_score += nation.military.get_score()

        if min_mil_nation ==  None or nation.military.get_score() < min_mil_nation.military.get_score():
            min_mil_nation = nation
        if max_mil_nation == None or nation.military.get_score() > max_mil_nation.military.get_score():
            max_mil_nation = nation

    print alliance_search, "Total military score:",mil_score

    print "Nation with current highest overall score:",nation_list[1].name, nation_list[1].score
    print "Nation with current lowest score:",nation_list[len(nation_list.keys())].name, nation_list[len(nation_list.keys())].score

    print "Nation with current highest military score:",max_mil_nation.name,max_mil_nation.military.get_score()
    print "Nation with current lowest military score:",min_mil_nation.name, min_mil_nation.military.get_score()
    '''

