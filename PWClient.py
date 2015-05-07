from urllib import urlencode, quote_plus
import httplib2
import os
import time
import lxml.etree as ET
import re

__author__ = 'sxh112430'

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

class PWClient:

    __last_request_timestamp = 0
    __root_url = "https://politicsandwar.com"
    __username = None
    __password = None

    nation_cache = {}
    alliance_cache = {}

    def __init__(self, username, password):
        self.debug = False
        self.http = httplib2.Http()
        self.headers = { 'Accept': 'text/html',
                         'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36' }
        self.__username = username
        self.__password = password

        self.__authenticate__()

    def __authenticate__( self ):
        print "Starting authentication as:",self.__username
        r,c = self.__make_http_request(self.__root_url+'/login/', body={'email':self.__username, 'password':self.__password, 'sesh':'', 'loginform':'Login'}, request_type='POST')
        self.headers['Cookie'] = r['set-cookie']
        print "Authentication success!"

    def __query_timecheck(self):
        current_timestamp = int(round(time.time() * 1000))
        time_difference = current_timestamp - self.__last_request_timestamp
        if time_difference < 100:
            # wait 100 ms between queries, so as not to be banned I guess??
            time.sleep(time_difference / 1000)
        self.__last_request_timestamp = time.time() * 1000

    def __make_http_request( self, url, body = None, request_type = 'GET' ):
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

    def _print( self, *kwargs ):
        if self.debug:
            for arg in kwargs:
                print arg,
            print ""

    def _retrieve_nationtable(self, url):
        status,content = self.__make_http_request(url)
        parser = ET.XMLParser(recover=True)
        tree = ET.fromstring(content, parser=parser)
        nationtable = tree.find(".//table[@class='nationtable']")
        return nationtable

    # TODO: get alliance info
    # TODO: get list of nation ID's from alliance ID
    # TODO: get list of nations who can declare against particular nation ID
    # TODO: consider downloading all ~3000 nations first, then parsing all the data after?

    def _retrieve_full_query_list(self, url, minimum=0, maximum=50):
        # Note: DO NOT INCLUDE &maximum=n&minimum=m in this url! They will be calculated and added in here!
        min_max_url = url
        # only modify this url, will need original unused url for later
        min_max_url += "&ob=score&maximum="+str(maximum)+"&minimum="+str(minimum)+"&search=Go"

        nationtable = self._retrieve_nationtable(min_max_url)

        full_dict = {}

        more_pages = False
        for tr in nationtable.findall(".//tr"):
            self._print(">tr", len(tr))
            if tr[0].text is not None and re.search('[0-9]+\)', tr[0].text):
                href = tr[1][0].attrib['href']
                eq_idx = href.index("=")
                n_id = int(href[eq_idx+1:])
                nation_idx = int(tr[0].text.replace(')','').replace(',',''))
                full_dict[nation_idx] = self.get_nation_obj_from_ID(n_id)
                more_pages = True

        if more_pages:
            append_to_list = self._retrieve_full_query_list(url, minimum=minimum+maximum)
            for key in append_to_list.keys():
                full_dict[key] = append_to_list[key]

        return full_dict

    def get_dict_of_alliance_members_from_name(self, a_name):
        # TODO: this

        query_url = self.__root_url + "/index.php?id=15&keyword="+quote_plus(str(a_name))+"&cat=alliance"
        full_dict = self._retrieve_full_query_list(query_url)

        return full_dict

    def get_list_of_alliance_members_from_ID(self, a_id):
        a_name = self.get_alliance_name_from_ID(a_id)
        return self.get_dict_of_alliance_members_from_name(a_name)

    def get_alliance_name_from_ID(self, a_id):
        # TODO: this
        print "ERROR NOT IMPLEMENTED"
        import sys
        sys.exit(1)
        pass


    def get_nation_obj_from_ID(self, n_id):
        # TODO: put a time check on last pull, in case this script ends up being used in ways that take long periods of time
        if n_id in self.nation_cache.keys():
            return self.nation_cache[n_id]

        # Not in cache, go pull data
        url = self.__root_url + "/nation/id="+str(n_id)
        nationtable = self._retrieve_nationtable(url)

        nation = Nation()
        military = Military()

        for tr in nationtable.findall(".//tr"):
            self._print(">tr", len(tr))
            td_key_text = str(tr[0].text).strip()
            td_key_tag = str(tr[0].tag).strip()
            if td_key_text == "Nation Name:":
                nation.name = tr[1].text
                self._print("FOUND: Nation name:",tr[1].text)
            elif td_key_text == "Leader Name:":
                nation.leader = tr[1].text
                self._print("FOUND: Leader name:",tr[1].text)
            elif td_key_text == "Founded:":
                nation.founded_date = tr[1].text
                self._print("FOUND: Founded:",tr[1].text)
            elif td_key_text == "Last Activity:":
                activity_text = tr[1].text
                # TODO: transform this into a datetime
                nation.time_since_active = activity_text
                self._print("FOUND: Last active:",tr[1].text)
            elif td_key_text == "Unique ID:":
                uid = tr[1].text
                nation.uid = tr[1][0].text
                self._print(tr[1][0].attrib['href'])
                self._print("FOUND: UID:", tr[1][0].text)
            elif td_key_text == "National Color:":
                self._print("FOUND COLOR:", tr[1][0][0].text)
                nation.color = tr[1][0][0].text
            elif td_key_text == "Alliance:":
                nation.alliance_name = tr[1][0].text
                href = str(tr[1][0].attrib['href'])
                idx = href.index('=')
                a_id = href[idx+1:len(href)]
                nation.alliance_id = int(a_id)
                self._print("Found A_ID:", href, a_id)
            elif td_key_text == "Government Type:":
                # ....don't ask, something is up with the parser
                # Edit: Okay it looks like any td with a question mark needs to be indexed weird
                # Normally it's tr[1], but for '?' td's, it's tr[0][1]. I don't know why.
                # Parser is probably mad at bad HTML.
                self._print("Found Govt type:", tr[0][1].text)
                nation.govt_type = tr[0][1].text
            elif td_key_text == "Population:":
                self._print("Found pop:",tr[1].text)
                nation.population = int(tr[1].text.replace(',','')) # get rid of commas
            elif td_key_text == "Land Area:":
                land = tr[0][1].text
                idx = land.index("sq")-1
                land = land[:idx]
                self._print("Found land area:", land)
                nation.land_area = int(land.replace(',','')) # get rid of commas
            elif td_key_text == "Infrastructure:":
                self._print("Found infra:",tr[0][1].text)
                nation.infrastructure = float(tr[0][1].text)
            elif td_key_text == "Pollution Index:":
                pollution_string = tr[0][1].text
                idx = pollution_string.index(" ")
                pollution = int(pollution_string[:idx])
                self._print("Found pollution:",pollution)
                nation.pollution_index = pollution
            elif td_key_text == "Nation Rank:":
                idx = tr[1].text.index(" of")
                rank = tr[1].text[1:idx].replace(',','')
                nation.rank = int(rank)
                self._print("Found nation rank:", tr[1].text, rank)
            elif td_key_text == "Nation Score:":
                self._print("Found nation score:",tr[1].text)
                score = float(tr[1].text)
                nation.score = score

            elif td_key_text == "Soldiers:":
                soldiers = tr[1].text.replace(',','')
                military.soldiers = int(soldiers)
                self._print("Found soldiers:",military.soldiers)

            elif td_key_text == "Tanks:":
                tanks = tr[1].text.replace(',','')
                military.tanks = int(tanks)
                self._print("Found tanks:",military.tanks)

            elif td_key_text == "Aircraft:":
                aircraft = tr[1].text.replace(',','')
                military.aircraft = int(aircraft)
                self._print("Found aircraft:",military.aircraft)

            elif td_key_text == "Ships:":
                ships = tr[1].text.replace(',','')
                military.ships = int(ships)
                self._print("Found ships:",military.ships)

            elif td_key_text == "Spies:":
                spies = tr[1].text.replace(',','')
                military.spies = int(spies)
                self._print("Found spies:",military.spies)

            elif td_key_text == "Missiles:":
                missiles = tr[1].text.replace(',','')
                military.missiles = int(missiles)
                self._print("Found missiles:",military.missiles)

            elif td_key_text == "Nuclear Weapons:":
                nukes = tr[1].text.replace(',','')
                military.nukes = int(nukes)
                self._print("Found nukes:",military.nukes)

            # TODO: scrape projects

            else:
                self._print(td_key_tag, td_key_text)
        nation.military = military
        self.nation_cache[n_id] = nation
        return nation

if __name__ == "__main__":

    USERNAME = os.environ['PWUSER']
    PASS = os.environ['PWPASS']
    pwc = PWClient(USERNAME, PASS)

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

