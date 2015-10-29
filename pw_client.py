import traceback
from urllib import urlencode, quote_plus, quote
import datetime
from datetime import timedelta
import httplib2
import os
import time
# import xml.etree.ElementTree as ET
import lxml.etree as ET
import re
import logging
import sys
import pymongo
import requests

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


def _get_param_from_url(url_string, param):
    # TODO: use this where appropriate
    param += "="
    idx = url_string.index(param) + len(param)
    url_string = url_string[idx:]
    try:
        end_idx = url_string.index('&')
    except:
        end_idx = len(url_string)
    return url_string[:end_idx].strip()

class NationDoesNotExistError(Exception): pass
class WhyIsNationInBeige(Exception): pass
class NationIsNotInBeige(Exception): pass

class Battle:
    """
    Abstraction of battles
    """

    BATTLE_GROUND = "ground attack" #
    BATTLE_AIR = "an airstrike" #
    BATTLE_DOGFIGHT = "dogfight airstrike" #
    BATTLE_NAVAL = "naval attack" #
    BATTLE_MISSILE_STRIKE = "launched a missile" #
    BATTLE_NUCLEAR_DETONATION = "detonated a nuclear weapon" #
    BATTLE_DECLARATION = "declared war upon" #
    BATTLE_TRUCE_AGREEMENT = "have agreed upon a truce" #
    BATTLE_COMPLETION = "immediate surrender" #
    BATTLE_EXPIRATION = "conflict expired" #
    BATTLE_NO_CHANGE = "continues to rage on" #

    BATTLE_TYPES = [BATTLE_GROUND, BATTLE_AIR, BATTLE_DOGFIGHT, BATTLE_NAVAL, BATTLE_MISSILE_STRIKE, BATTLE_NUCLEAR_DETONATION, BATTLE_DECLARATION, BATTLE_TRUCE_AGREEMENT, BATTLE_COMPLETION, BATTLE_EXPIRATION, BATTLE_NO_CHANGE]
    BATTLE_TYPES_NO_CHANGES = [BATTLE_EXPIRATION, BATTLE_NO_CHANGE]

    @classmethod
    def from_nodes(cls, war_id, time_string, description):

        date_format = "%m/%d/%Y %I:%M %p"
        time_of_battle = datetime.datetime.strptime(time_string.strip(), date_format)

        fight_string = stringify_children(description)

        battle_type = None
        for bt in Battle.BATTLE_TYPES:
            if bt in fight_string:
                battle_type = bt
        if battle_type is None:
            raise Exception("Don't know how to parse "+fight_string)


        ended_war = battle_type == Battle.BATTLE_COMPLETION
        immense_triumph = "immense triumph" in fight_string

        if battle_type in Battle.BATTLE_TYPES_NO_CHANGES:
            actor_id = None
            defender_id = None
        else:
            actor_id = _get_param_from_url(description[0].attrib['href'], "id")
            defender_id = _get_param_from_url(description[1].attrib['href'],"id")

        return Battle(war_id, time_of_battle, actor_id, defender_id, battle_type, immense_triumph, ended_war)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Battle, time="+str(self.time_of_battle)+", war="+str(self.war_id)+", actor="+str(self.actor_id)+", defender_id="+str(self.defender_id)+", type="+self.battle_type+", imm tri="+str(self.immense_triumph)+">"

    def __init__(self, war_id, time_of_battle, actor_id, defender_id, battle_type, immense_triumph, ended_war = False):
        """

        :rtype : Battle
        """
        self.war_id = war_id
        self.time_of_battle = time_of_battle
        self.actor_id = actor_id
        self.defender_id = defender_id
        self.battle_type = battle_type
        self.immense_triumph = immense_triumph
        self.ended_war = ended_war
        self.is_declaration = battle_type == Battle.BATTLE_DECLARATION

class War:
    def __init__(self, war_id, battles = None):
        """
        :rtype : War
        """
        self.war_id = war_id
        self.battles = battles
        self.date_ended = None
        self.date_started = None
        self.winner_id = None
        if len(battles) == 0:
            raise Exception("What happened with war "+str(war_id)+"??")
        if self.battles is None:
            self.battles = []
            raise Exception("What happened with war "+str(war_id)+"??")
        self.date_started = self.battles[0].time_of_battle
        self.in_progress = False
        for b in self.battles:
            assert isinstance(b, Battle)
            if b.ended_war:
                self.date_ended = b.time_of_battle
                self.in_progress = False
                self.winner_id = b.actor_id

    def __str__(self):
        representation = "<War: "+str(self.war_id) + ", winner:"
        if self.in_progress:
            representation += " inconclusive"
        else:
            representation += str(self.winner_id)
        representation += ">"
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

class Alliance:
    color = None
    nations = None
    founded = None
    score = None
    bank_balance = None


class City:
    name = None
    population = None
    infrastructure = None
    land_area = None
    powered = None
    founded = None


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
    nation_id = None
    time_since_active = None
    precisely_founded = False
    cities = []

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
        self.session = requests.Session()

        self._authenticate()
        if logger is None:
            logger = logging.getLogger("PWClient")
            hndl = logging.StreamHandler(sys.stdout)
            logger.addHandler(hndl)
            logger.setLevel(logging.INFO)
        self.logger = logger

    def _authenticate( self ):
        """
        Call this if you have waited a long time between accesses; it resubmits your password to the server so that you can access stuff
        :return: None
        """
        self._print(1, "Starting authentication as:",self.__username)
        r,c = self.__make_http_request(self.__root_url+'/login/', body={'email':self.__username, 'password':self.__password, 'loginform':'Login'}, request_type='POST')
        for cookie in self.session.cookies:
            self.headers[cookie.name] = cookie.value
        if "Login Failure" in c:
            raise Exception("Failure to authenticate!")
        self._print(1, "Authentication success!")

    def __query_timecheck(self):
        """
        ensures that the client doesn't DDOS or spam the server so no one gets banned
        :return: None
        """
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
        """
        You probably don't need to use this
        :param url:
        :param body:
        :param request_type:
        :return:
        """
        self._print(2, "Making HTTP request for: ",url)
        self.__query_timecheck()
        r_headers = self.headers
        if(request_type == 'POST' or request_type == 'PUT'):
            r_headers['Content-type']= 'application/x-www-form-urlencoded'

        if body != None:
            body = urlencode(body)
        try:
            response = self.session.request(request_type, url, data=body, headers=self.headers)
            content = response.content
            response = response.headers
            # response, content = self.http.request(url, request_type, body = body, headers = r_headers)
        except (Exception, SystemExit ) as e:
            raise
        return response, content

    def _print( self, debug_level, *kwargs ):
        """
        Keep printing controlled. You probably don't need to use this.

        :param debug_level:
        :param kwargs:
        :return:
        """
        if self.debug >= debug_level:
            logstring = ""
            for arg in kwargs:
                print arg,
                logstring += str(arg)+" "
            print ""
            self.logger.info(logstring)

    def _retrieve_leftcolumn(self):
        """
        you probably don't need to use this
        Retrieve leftcolumn html (where the server time is)
        :return:
        """
        self._print("Retrieving leftcolumn")
        status,content = self.__make_http_request(self.__root_url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)
        leftcolumn = tree.find(".//div[@id='leftcolumn']")
        return leftcolumn

    def _retrieve_nationtable(self, url, idx=0):
        """
        you probably don't need to use this

        get the main table of a page from pnw
        :param url:
        :param idx:
        :return:
        """
        self._print(1, "Retrieving nationtable for:",url)
        status,content = self.__make_http_request(url)
        if "That nation does not exist." in content:
            raise NationDoesNotExistError(url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)

        nationtables = tree.findall(".//table[@class='nationtable']")

        return nationtables[idx]

    def _generate_full_query_list(self, url, minimum=0, maximum=50):
        """
        don't worry about this, trust me
        :param url:
        :param minimum:
        :param maximum:
        :return:
        """
        # Note: DO NOT INCLUDE &maximum=n&minimum=m in this url! They will be calculated and added in here!
        min_max_url = url
        # only modify this url, will need original unused url for later
        min_max_url += "&ob=score&maximum="+str(maximum)+"&minimum="+str(minimum)+"&search=Go"

        nationtable = self._retrieve_nationtable(min_max_url)

        for tr in nationtable.findall(".//tr"):
            if len(tr) < 1 or tr[0].tag == "th":
                continue
            if "Your search returned 0 results." in stringify_children(tr):
                raise StopIteration()
            yield tr

        for tr in self._generate_full_query_list(url, minimum=minimum+maximum):
            yield tr

    def _generate_full_nation_list(self, url, minimum=0, maximum=50):
        """

        :param url:
        :param minimum:
        :param maximum:
        :return:
        """
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
                nation_id = int(href[eq_idx+1:])
                yield self.get_nation_obj_from_ID(nation_id)
                more_pages = True

        if more_pages:
            for nation in self._generate_full_nation_list(url, minimum=minimum+maximum):
                yield nation

    def set_db(self, db):
        # TOOD: this
        # self.__using_db = True
        raise Exception("Unimplemented, sry")
        pass

    def count_turns_since(self, date):
        now = self.get_current_date_in_datetime()
        time_diff = now - date
        assert isinstance(time_diff, timedelta)
        hours = (time_diff.total_seconds() / 60) / 60
        turns = hours/2
        return turns

    def get_list_of_alliance_members_from_alliance_name(self, alliance_name):
        """
        Get a list of nations from an alliance name (e.g. "Charming Friends").

        :param alliance_name: a string representing an alliance's name (e.g. "Charming Friends"
        :return: list of nations
        """
        self._print(2, "Getting dict for alliance name:",alliance_name)
        query_url = self.__root_url + "/index.php?id=15&keyword="+quote_plus(str(alliance_name))+"&cat=alliance"
        nations = []
        for nation in self._generate_full_nation_list(query_url):
            assert isinstance(nation, Nation)
            nations.append(nation)
        return nations

    def generate_all_nations_with_color(self, color):
        """

        This is hard to explain how it works, but easy to explain how to use it. This will return a list--sort of. You can iterate over it like this:

        for nation in client.get_all_nations_with_color('beige'):
            print nation.nation_id

        generators are hard to explain the backend of but the idea is that it makes the program "appear" to be running faster.

        :param color: A string (e.g. "beige") representing a color to search for
        :return Nation generator object
        """
        query_url = self.__root_url + "/index.php?id=15&keyword="+color+"&cat=color"
        for nation in self._generate_full_nation_list(query_url):
            yield nation

    def get_list_of_alliance_members_from_ID(self, alliance_id):
        """
        returns an iterable list of nation objects from an alliance's ID.

        example usage:

        list = client.get_list_get_list_of_alliance_members_from_ID(1234)
        for nation in list:
            print nation.nation_id

        :param alliance_id: a number representing an alliance ID
        :return: a list of Nation objects
        :rtype list
        """
        a_name = self.get_alliance_name_from_ID(alliance_id)
        return self.get_list_of_alliance_members_from_alliance_name(a_name)

    def get_alliance_name_from_ID(self, alliance_id):
        """
        returns an string of an alliance's name from their alliance ID.

        example usage:

        alliance_name = client.get_alliance_name_from_ID(1234)
        print alliance_name # prints the name representation of the alliance

        :param alliance_id: a number representing an alliance ID
        :return: str alliance_name
        :rtype str
        """
        self._print(2, "Getting alliance name from id:",alliance_id)
        alliance_url = self.__root_url + "/alliance/id="+str(alliance_id)

        status,content = self.__make_http_request(alliance_url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)

        title_obj = tree.find(".//td[@style='text-align:center; font-weight:bold; width:260px;']")
        title = title_obj.text

        self._print(2, "Alliance name found: ",title)
        return title

    def get_nation_name_from_id(self, nation_id):
        """
        returns an string of a nation's name from their nation ID.

        example usage:

        nation_name = client.get_nation_name_from_ID(1234)
        print nation_name # prints the name representation of the nation

        :param nation_id: a number representing a nation ID
        :return: str nation_name
        :rtype str
        """
        nation_id = int(nation_id)
        if nation_id in self.nation_cache.keys():
            return self.nation_cache[nation_id].name
        n = self.get_nation_obj_from_ID(nation_id)
        return n.name

    def get_alliance_score_from_id(self, alliance_id):
        alliance_score = 0
        for nation in self.get_list_of_alliance_members_from_ID(alliance_id):
            alliance_score += nation.score
        return alliance_score

    def get_alliance_average_score_from_id (self, alliance_id):
        total_score = self.get_alliance_score_from_id(alliance_id)
        return total_score/float(self.get_number_of_members_in_alliance_by_id(alliance_id))


    def get_next_turn_in_datetime(self, reftime=None):
        """
        returns a datetime object of the next turn. If given a reference time, returns a datetime object of the next
        turn after the reference time.

        example usage:

        next_turn = client.get_next_turn_in_datetime()
        print next_turn # prints the date and time of the next turn

        OR

        next_turn_after_nation_leaves_beige = \
            client.get_next_turn_in_datetime(client.calculate_beige_exit_time(1234))
        print next_turn_after_nation_leaves_beige # prints the date and time of the turn that a nation will leave beige

        :param reftime: a datetime object representing a reference time
        :return: datetime alliance_name
        :rtype datetime
        """
        if reftime is None:
            leftcol = self._retrieve_leftcolumn()
            datestring = str(leftcol[4][1].tail).strip()
            now_year = datetime.datetime.now().year
            reftime = datetime.datetime.strptime(datestring+" "+str(now_year), "%B %d %I:%M %p %Y")
        plus_hour = 0
        if reftime.hour % 2 == 0:
            plus_hour = 1
        reftime += timedelta(hours=plus_hour, minutes=60-reftime.minute)
        return reftime

    def get_current_date_in_datetime(self):
        """
        returns a datetime object of the server's current date.

        example usage:

        current_time = client.get_current_date_in_datetime()
        print current_time # prints the date and time w.r.t the server

        :return: datetime current_time
        :rtype datetime
        """
        leftcol = self._retrieve_leftcolumn()
        datestring = str(leftcol[4][1].tail).strip()
        now_year = datetime.datetime.now().year
        dt = datetime.datetime.strptime(datestring+" "+str(now_year), "%B %d %I:%M %p %Y")
        return dt

    def get_nation_obj_from_ID(self,nation_id, skip_cache = False):
        """
        returns a nation object from a nations ID. If skip_cache = True, this will pull the webpage even if it is cached

        example usage:

        nation = client.get_nation_obj_from_ID(1234)
        print nation.military.soldiers

        :return: nation nation
        :rtype Nation
        """
        # TODO: put a time check on last pull, in case this script ends up being used in ways that take long periods of time
        nation_id = str(nation_id)

        self._print(2, "Getting nation from ID:",nation_id)
        if not skip_cache: # Sometimes may want to force-skip cache
            if nation_id in self.nation_cache.keys():
                self._print(2, "Cache hit on ",nation_id,"! Skipping download")
                return self.nation_cache[nation_id]

        # Not in cache, go pull data
        url = self.__root_url + "/nation/id="+nation_id
        nationtable = self._retrieve_nationtable(url)

        nation = Nation()
        military = Military()
        cities = []

        second_nationtable = self._retrieve_nationtable(url, 1)
        for city in second_nationtable.findall(".//tr/td/a"):

            city_obj = City()
            city_obj.name = city.text
            city_link = city.attrib["href"]
            city_table = self._retrieve_nationtable(city_link)

            infrastructure = float(city_table[1][0][1].text.replace(",",""))
            city_obj.infrastructure = infrastructure
            land_area = city_table[1][1][0][1].text.split(" ")[0].replace(",","")
            city_obj.land_area = land_area
            population = int(city_table[1][0][3].text.split(" ")[0].replace(",",""))
            city_obj.population = population

            # print city_table[1][1][0][2][1].tag
            # print city_table[1][1][0][2][1].text
            date_string = city_table[1][1][0][3][1][0][3][3][1].text
            day_founded = datetime.datetime.strptime(date_string, "%m/%d/%Y")
            city_obj.founded = day_founded

            cities.append(city_obj)
        nation.cities = cities
        nation.nation_id = nation_id

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
                            if datetime.datetime.now() < created_obj:
                                #This is in the future, oops, fix it I guess (this is bad but w/e)
                                creation_string = tr[0][0].text[:-3]+" "+str(nation.founded_date.year)
                                format_string = "%m/%d %I:%M %p %Y"
                                created_obj = datetime.datetime.strptime(creation_string, format_string)
                            found_something = True
                            if created_obj > nation.founded_date:
                                nation.founded_date = created_obj
                                nation.precisely_founded = True
                                self._print(3, "Found more precise founded date:",created_obj)
                except:
                    pass
                finally:
                    if not found_something:
                        self._print(3, "Unknown key:",td_key_tag, td_key_text)
        nation.military = military
        self.nation_cache[nation_id] = nation
        return nation

    def queue_new_notification(self, to, subject, body, seconds_until_notification):
        """
        This will send an email in a certain number of seconds

        :param to: string representing an email address (e.g. "someone@gmail.com"
        :param subject: string representing a subject (e.g. "Important PNW email!"
        :param body: string representing a body (e.g. "just kidding it wasn't that important lol")
        :param seconds_until_notification: the number of seconds the server should wait before sending (e.g. for thirty minute delay:  60 * 30 )
        :return: None
        """
        url = "http://radiofreaq.spencer-hawkins.com:5000/queue_n/"+quote(to)+"/"+quote(subject)+"/"+quote(body)+"/"+quote(str(seconds_until_notification))+"/"
        self._print(2, "Making new notification req: ", url)
        self._print(3, self.__make_http_request(url))

    def calculate_beige_exit_time(self,nation_id, be_stupid_verbose=False):
        """
        Calculates the time that a nation is expected to leave beige.

        :paramnation_id: int representing a nation's ID
        :param be_stupid_verbose: print lots of dumb things. Useful for debugging
        :return: datetime object representing the exact (but not turn-biased) time a nation will leave beige
        :rtype War
        """
        nation = self.get_nation_obj_from_ID(nation_id)
        if nation.color != "Beige":
            raise NationIsNotInBeige(str(nation.nation_id))
        wars = self.get_wars(nation_id)

        all_battles = self.assemble_sorted_battle_list_from_wars(wars)

        last_lost_date = None
        for battle in all_battles:
            if battle.immense_triumph and str(battle.actor_id) != str(nation_id):
                if battle.ended_war:
                    last_lost_date = battle.time_of_battle
                    if be_stupid_verbose:
                        print nation_id, "exiting because of battle ",battle
                else:
                    if last_lost_date is not None and battle.time_of_battle - last_lost_date < BEIGE_WAR_TIMEDELTA:
                        last_lost_date = battle.time_of_battle
                        if be_stupid_verbose:
                            print nation_id, "exiting beige because of battle ",battle
                    else:
                        last_lost_date = None # gone past the 5 day limit, start over
                        if be_stupid_verbose:
                            print nation_id, "jk not exiting because of       ",battle

        if last_lost_date is not None and self.get_next_turn_in_datetime() - self.get_next_turn_in_datetime(last_lost_date) <= BEIGE_WAR_TIMEDELTA:
            print "returning now", last_lost_date
            print BEIGE_WAR_TIMEDELTA
            print last_lost_date + BEIGE_WAR_TIMEDELTA
            return last_lost_date + BEIGE_WAR_TIMEDELTA
        # wasn't a war that kicked into beige, must be creation date OR NUKE
        #TODO: check nukes, figure out if they have extensions

        if self.get_next_turn_in_datetime() - self.get_next_turn_in_datetime(nation.founded_date) <= BEIGE_CREATION_TIMEDELTA:
            print "returning because new", nation.founded_date
            print nation.founded_date + BEIGE_CREATION_TIMEDELTA
            return nation.founded_date + BEIGE_CREATION_TIMEDELTA
        sys.stderr.write(str(WhyIsNationInBeige("ERROR: Nation "+str(nation_id)+" shouldn't be in beige...??!?!?")))
        sys.stderr.write("Returning very inaccurate time difference!")
        return datetime.datetime.now() + BEIGE_WAR_TIMEDELTA

    def get_war_obj_from_id(self, war_id):
        """
        Returns a war object based on a war ID number
        :param war_id: int representing a war number
        :return: War
        :rtype War
        """
        # idx = 1 because on war screens there are actually 3 separate nationtables. We want the second, 0 indexed -> 1
        nationtable = self._retrieve_nationtable(self.__root_url+"/nation/war/timeline/war="+str(war_id),1)
        battle_nodes = nationtable.findall(".//tr")

        battle_objs = []

        for battle_idx in range(len(battle_nodes)):
            battle = battle_nodes[battle_idx]
            battle_time = battle[0][0].text
            battle_description = battle[1][0]
            try:
                new_battle = Battle.from_nodes(war_id=war_id,time_string =battle_time, description =battle_description)
            except:
                print "no idea what happened here"
                print stringify_children(battle_description)
                self.logger.error("no idea what happened here")
                self.logger.error(stringify_children(battle_description))
                self.logger.error(traceback.format_exc())
                self.logger.error(traceback.format_stack())
                raise
            battle_objs.append(new_battle)

        w = War(war_id, battles=battle_objs)

        return w

    def get_alliance_obj_from_id(self, alliance_id):
        """
        Returns an alliance object based on an alliance ID number
        :param alliance_id: int representing an alliance ID number
        :return: Alliance
        :rtype Alliance
        """
        # TODO: put a time check on last pull, in case this script ends up being used in ways that take long periods of time
        self._print(2, "Getting alliance from ID:",alliance_id)

        url = self.__root_url + "/alliance/id="+str(alliance_id)
        nationtable = self._retrieve_nationtable(url)

        alliance = Alliance()

        for tr in nationtable.findall(".//tr"):

            # self.get_nation_obj_from_ID()

            td_key_text = str(tr[0].text).strip()
            td_key_tag = str(tr[0].tag).strip()

            if td_key_text == "Founded:":
                date_string = tr[1].text.split(" ")[0]
                date_obj = datetime.datetime.strptime(date_string, "%m/%d/%Y")
                alliance.founded = date_obj
                self._print(3,"FOUND: Founded:",date_obj)
            elif td_key_text == "National Color:":
                self._print(3,"FOUND COLOR:", tr[1][0][0].text)
                alliance.color = tr[1][0][0].text.strip()
            elif td_key_text == "Score:":
                self._print(3,"FOUND SCORE:", tr[1].text)
                alliance.score = float(tr[1].text.strip().replace(",",""))
        bank_url = url + "&display=bank"
        bank_ntable = self._retrieve_nationtable(bank_url)

        alliance.bank_balance = {}

        for tr in bank_ntable.findall(".//tr"):
            if len(tr) > 1 and len(tr[0]) > 0:
                resource_key = tr[0][0].text.strip()
                resource_amt_str = tr[0][1].text
                if resource_amt_str is None:
                    resource_amt_str = "0"
                if not resource_key.startswith("When"):
                    resource_amt = float(resource_amt_str.strip().replace(",","").replace("$",""))
                    alliance.bank_balance[resource_key] = resource_amt

        return alliance

    def get_number_of_members_in_alliance_by_id(self, alliance_id):
        alliance_name = self.get_alliance_name_from_ID(alliance_id)
        query_url = self.__root_url + "/index.php?id=15&keyword="+quote_plus(str(alliance_name))+"&cat=alliance"
        number_of_alliance_members = sum(1 for _ in self._generate_full_query_list(query_url))
        return number_of_alliance_members

    def get_alliance_tax_records_from_id(self, alliance_id, only_last_turn=False, records_since_datetime=None):
        """

        :param alliance_id: a number representing an alliance id
        :param only_last_turn: if you only want to look at tax records from the most recent turn
        :param records_since_datetime: a date to go back since. Should be game-time biased!
        :return: list of tax records
        """
        url = self.__root_url + "/alliance/id="+str(alliance_id)+"&display=banktaxes"
        nationtable_idx = 0

        num_records = 100

        if records_since_datetime is not None:
            # estimate how many records we'll need
            now = self.get_current_date_in_datetime()
            diff =  now - records_since_datetime
            hours = diff.total_seconds() / (60 * 60)
            turns = hours / 2

            num_records = turns * (self.get_number_of_members_in_alliance_by_id(alliance_id) + 10) # give a big margin of error, because it doesn't cost anything
            self._print(3, "searching for records since ",records_since_datetime," which was ",hours, "hours ago and",turns," turns ago ->",num_records, "records to fetch")


        records = []

        window_start = 0
        max_window = 100

        if only_last_turn:
            num_records = self.get_number_of_members_in_alliance_by_id(alliance_id)
            max_window = min(max_window, num_records)

        records_left = num_records

        while records_left > 0:
            self._print(1, "Retrieving nationtable for:",url)
            r,content = self.__make_http_request(url, body={'maximum': max_window, 'minimum':window_start}, request_type='POST')
            parser = ET.XMLParser(recover=True)
            tree = ET.fromstring(content, parser=parser)
            nationtables = tree.findall(".//table[@class='nationtable']")
            nationtable = nationtables[nationtable_idx]

            records_left -= max_window
            window_start += max_window

            for tr in nationtable.findall(".//tr"):
                tax_record = {}
                if tr[1].text == "Date":
                    continue
                transaction_date_str = tr[1].text
                transaction_date = datetime.datetime.strptime(transaction_date_str.strip(), "%m/%d/%Y %I:%M %p")
                try:
                    tax_record["sender"] = nation_id = _get_param_from_url( tr[1][1][0].attrib['href'], "id" )
                except IndexError:
                    print len(tr)
                    print len(tr[1][1])
                    print tr[1][1].text
                    print stringify_children(tr[1][0])
                    tax_record["sender"] = nation_id = _get_param_from_url( tr[2][0].attrib['href'], "id" )
                tax_record["date"] = transaction_date
                tax_record['resources'] = {}
                tax_record['resources']["money"] = float(tr[1][3].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["food"] = float(tr[1][4].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["coal"] = float(tr[1][5].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["oil"] = float(tr[1][6].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["uranium"] = float(tr[1][7].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["lead"] = float(tr[1][8].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["iron"] = float(tr[1][9].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["bauxite"] = float(tr[1][10].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["gasoline"] = float(tr[1][11].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["munition"] = float(tr[1][12].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["steel"] = float(tr[1][13].text.strip().replace("$","").replace(",",""))
                tax_record['resources']["aluminum"] = float(tr[1][14].text.strip().replace("$","").replace(",",""))
                if records_since_datetime is not None and transaction_date < records_since_datetime:
                    return records # we already went too far, stop and return
                records.append(tax_record)
            # if only_last_turn:
                # records = records[:num_records]
        return records

    def get_alliance_bank_records_from_id(self, alliance_id, records_since_datetime, min_records=50):
        """

        :param alliance_id: a number representing an alliance id
        :param only_last_turn: if you only want to look at tax records from the most recent turn
        :param records_since_datetime: a date to go back since. Should be game-time biased!
        :return: list of tax records
        """
        url = self.__root_url + "/alliance/id="+str(alliance_id)+"&display=bank"
        nationtable_idx = 3

        # estimate how many records we'll need
        num_records = min_records
        self._print(3, "searching for records since ", records_since_datetime)

        records = []

        window_start = 0
        max_window = min(num_records, 50)

        last_datetime = None

        while last_datetime is None or last_datetime > records_since_datetime:
            self._print(1, "Retrieving nationtable for:",url)
            r,content = self.__make_http_request(url, body={'maximum': max_window, 'minimum':window_start}, request_type='POST')
            parser = ET.XMLParser(recover=True)
            tree = ET.fromstring(content, parser=parser)
            nationtables = tree.findall(".//table[@class='nationtable']")
            nationtable = nationtables[nationtable_idx]

            window_start += max_window

            for tr in nationtable.findall(".//tr"):
                has_note = len(tr[1].findall(".//img[@src='https://politicsandwar.com/img/icons/16/note.png']")) > 0
                tax_record = {}
                if tr[1].text == "Date":
                    continue
                transaction_date_str = tr[1].text
                transaction_date = datetime.datetime.strptime(transaction_date_str.strip(), "%m/%d/%Y %I:%M %p")
                try:
                    if has_note:
                        tax_record["sender"] = nation_id = _get_param_from_url(tr[1][1][0].attrib['href'], "id")
                        tax_record["reciever"] = _get_param_from_url(tr[1][2][0].attrib['href'], "id")
                        tax_record["banker"] = _get_param_from_url(tr[1][3][0].attrib['href'], "id")
                    else:
                        tax_record["sender"] = nation_id = _get_param_from_url(tr[2][0].attrib['href'], "id")
                        tax_record["reciever"] = _get_param_from_url(tr[3][0].attrib['href'], "id")
                        tax_record["banker"] = _get_param_from_url(tr[4][0].attrib['href'], "id")
                    tax_record["date"] = transaction_date
                    tax_record['resources'] = {}
                    if has_note:
                        tax_record['resources']["money"] = float(tr[1][4].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["food"] = float(tr[1][5].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["coal"] = float(tr[1][6].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["oil"] = float(tr[1][7].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["uranium"] = float(tr[1][8].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["lead"] = float(tr[1][9].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["iron"] = float(tr[1][10].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["bauxite"] = float(tr[1][11].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["gasoline"] = float(tr[1][12].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["munition"] = float(tr[1][13].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["steel"] = float(tr[1][14].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["aluminum"] = float(tr[1][15].text.strip().replace("$","").replace(",",""))
                    else:
                        tax_record['resources']["money"] = float(tr[5].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["food"] = float(tr[6].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["coal"] = float(tr[7].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["oil"] = float(tr[8].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["uranium"] = float(tr[9].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["lead"] = float(tr[10].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["iron"] = float(tr[11].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["bauxite"] = float(tr[12].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["gasoline"] = float(tr[13].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["munition"] = float(tr[14].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["steel"] = float(tr[15].text.strip().replace("$","").replace(",",""))
                        tax_record['resources']["aluminum"] = float(tr[16].text.strip().replace("$","").replace(",",""))

                    if transaction_date < records_since_datetime:
                        return records # we already went too far, stop and return
                    records.append(tax_record)

                except IndexError:
                    # just skip if it's gonna bitch about stuff, probably me trying to hack lel
                    if transaction_date < records_since_datetime:
                        return records  # we already went too far, stop and return
            # if only_last_turn:
                # records = records[:num_records]
        return records

    def get_wars(self, nation_id):

        war_url = self.__root_url + "/nation/id="+str(nation_id)+"&display=war"
        nationtable = self._retrieve_nationtable(war_url)

        war_list = []
        for tr in nationtable.findall(".//tr"):
            if "No wars to display" in stringify_children(tr): # empty warlist, just return
                return war_list
            if tr[0].text == "Date":
                continue # skip empty row

            a_tag = tr[3].find(".//a")
            war_id = a_tag.attrib['href']
            war_id = _get_param_from_url(war_id, "war")
            war_list.append(self.get_war_obj_from_id(war_id))
        return war_list

    def assemble_sorted_battle_list_from_wars(self, wars):
        sorted_battles = []

        for war in wars:
            assert isinstance(war, War)
            for battle in war.battles:
                sorted_battles.append(battle)
        sorted_battles.sort(key=lambda b:b.time_of_battle)

        return sorted_battles

    def make_bank_withdrawal(self, recipient_id, ticket_no, money=0, food=0, coal=0, oil=0, uranium=0, lead=0, iron=0, bauxite=0,
                             gasoline=0, munitions=0, steel=0, aluminum=0):

        recipient_id = str(recipient_id)

        # don't give money to non-cf's
        alliance_members = self.get_list_of_alliance_members_from_ID(1356)
        assert recipient_id in [str(alliance_member.nation_id) for alliance_member in alliance_members]

        recipient_name = self.get_nation_name_from_id(recipient_id)
        body_data = {
            'withmoney': money,
            'withfood': food,
            'withcoal': coal,
            'withoil': oil,
            'withuranium': uranium,
            'withlead': lead,
            'withiron': iron,
            'withbauxite': bauxite,
            'withgasoline': gasoline,
            'withmunitions': munitions,
            'withsteel': steel,
            'withaluminum': aluminum,
            'withtype': 'Nation',
            'withrecipient': recipient_name,
            'withnote': 'FALCON n-'+str(ticket_no),
            'withsubmit': 'Withdraw'
        }
        self.__make_http_request(self.__root_url + "/alliance/id=1356&display=bank", body=body_data, request_type='POST')


class LeanPWDB(object):
    """ this will replace pnw_db.py eventually """
    def __init__(self):
        mongo_host = os.environ.get("mongodb_url")
        mongo_port = int(os.environ.get("mongodb_port"))
        mongo_dbname = os.environ.get("mongodb_dbname")
        mongo_user = os.environ.get("mongodb_user")
        mongo_password = os.environ.get("mongodb_password")

        mongo = pymongo.MongoClient(host=mongo_host, port=mongo_port)
        pnw_db = mongo[mongo_dbname]
        pnw_db.authenticate(mongo_user, mongo_password)
        self._db = pnw_db
        self.market_watch_collection = self._db["market_watch"]
        self.market_watch_notification_collection = self._db["market_watch_notifications"]

    def add_market_watch_record(self, resource_dict):
        today = datetime.datetime.now()
        record = {"values": resource_dict,
                  "time": today}
        self.market_watch_collection.insert_one(record)

    def get_notification_counts(self):
        return self.market_watch_notification_collection.find().sort("_id", pymongo.DESCENDING)[0]

    def _increment_notification_for_type(self, item_type, record_type, percentage):
        percentage_key = "last_"+record_type+"_percentage"
        n_record = self.get_notification_counts()
        n_id = n_record["_id"]
        n_record[item_type][record_type] += 1
        last_percentage = n_record[item_type][percentage_key]
        if abs(abs(last_percentage) - abs(percentage)) > 5:
            n_record[item_type][record_type] = 0
            n_record[item_type][percentage_key] = percentage
        count = n_record[item_type][record_type]
        okay_to_notify = count <= 3
        self.market_watch_notification_collection.update({"_id": n_id}, n_record)
        return okay_to_notify

    def increment_buy_counter_for_type(self, item_type, percentage):
        return self._increment_notification_for_type(item_type, "buy", percentage)

    def increment_sell_counter_for_type(self, item_type, percentage):
        return self._increment_notification_for_type(item_type, "sell", percentage)

    def increment_buy_offer_counter_for_type(self, item_type):
        return self._increment_notification_for_type(item_type, "buy_offer", 0)

    def init_new_counter(self, realstring_dict):
        new_record = {}
        for key in realstring_dict.keys():
            new_record[key] = {"buy": 0, "last_buy_percentage": 0, "sell": 0, "last_sell_percentage": 0, "buy_offer": 0, "last_buy_offer_percentage": 0}
        self.market_watch_notification_collection.insert_one(new_record)

    def _reset_counter(self, item_type, record_type):
        percentage_key = "last_"+record_type+"_percentage"
        n_record = self.get_notification_counts()
        n_id = n_record["_id"]
        n_record[item_type][record_type] = 0
        n_record[item_type][percentage_key] = 0
        self.market_watch_notification_collection.update({"_id": n_id}, n_record)

    def reset_buy_counter(self, item_type):
        self._reset_counter(item_type, "buy")

    def reset_sell_counter(self, item_type):
        self._reset_counter(item_type, "buy")

    def reset_buy_offer_counter(self, item_type):
        self._reset_counter(item_type, "buy_offer")


if __name__ == "__main__":

    pwc = PWClient(os.environ['PWUSER'], os.environ['PWPASS'])
    # pwc.get_list_of_alliance_members_from_alliance_name("Charming Friends")

    print pwc.get_alliance_tax_records_from_id(1356)
    print pwc.get_alliance_obj_from_id(1356)

    pass
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

