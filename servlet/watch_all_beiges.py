import sys
sys.path.append('/root/politicsandwar/pnw_stats_finder') # for non-ide usage
sys.path.append('/root/politicsandwar/pnw_stats_finder/servlet/mlibs') # for non-ide usage

from gmail.message import Message
from gmail.gmail import GMail
from PWClient import PWClient, Nation, WhyIsNationInBeige, NationDoesNotExistError
import base64
import lxml.etree as ETree
import logging
import os
import datetime

__author__ = 'sxh112430'
def send_email(to, subject, html):
    b64_un = 'Y2hhcm1pbmcuZnJpZW5kcy5wbnc=\n'
    b64_pass = 'bWUydGhhbmtz\n'
    m = GMail(base64.decodestring(b64_un), base64.decodestring(b64_pass))
    m.connect()
    message = Message(subject, to=to, html=html)
    # m.send(message)
    print "sending", to, subject, html
    m.close()

def create_html_table(nations, next_turn):
    html = ETree.Element("html")
    basic_text1 = ETree.Element("div")
    basic_text1.text = "The following nations are scheduled to leave beige next turn, at: "+str(next_turn)+" (game time)"
    h1 = ETree.Element("h1")
    h1.text = "REMEMBER!"
    basic_text2 = ETree.Element("div")
    basic_text2.text = "Ensure that all wars are a good target! Targets should have a trivial military, be inactive, be unprotected, and be a part of a small alliance (or no alliance)! Do not attack someone on this list without first checking each of these properties!"

    basic_text3 = ETree.Element("div")
    basic_text3.text = "Report any and all errors or issues to hawkins.spencer@gmail.com !"

    table = ETree.Element("table")

    for nation in nations:
        assert isinstance(nation, Nation)
        mil_percent = nation.military.get_score() / float(nation.score)
        name = nation.name
        link = "https://politicsandwar.com/nation/id="+str(nation.n_id)
        tr = ETree.Element("tr")
        name_td = ETree.Element("td")
        name_td.text = name
        score_td = ETree.Element("td")
        score_td.text = str(nation.score)
        mil_percent_td = ETree.Element("td")
        mil_percent_td.text = "Military % of score: "+str(mil_percent)[:5]
        link_td = ETree.Element("td")
        a = ETree.Element("a")
        a.attrib['href']=link
        a.text = link
        link_td.append(a)

        tr.append(name_td)
        tr.append(score_td)
        tr.append(mil_percent_td)
        tr.append(link_td)

        table.append(tr)
    html.append(basic_text1)
    html.append(h1)
    html.append(basic_text2)
    html.append(table)
    html.append(basic_text3)

    return ETree.tostring(html)

# recipients:  matodw@gmail.com, ashnicholson90@gmail.com

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("beige_watch.out", mode='w')
shandler = logging.StreamHandler(sys.stdout)
logger.addHandler(fhandler1)
logger.addHandler(shandler)
logger.setLevel(logging.INFO)

USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

beiges_to_expire = []
for beige in [pwc.get_nation_obj_from_ID(10203)]:
# for beige in pwc.generate_all_nations_with_color('beige'):
    try:
        time_to_beige_exit = pwc.get_next_turn_in_datetime(pwc.calculate_beige_exit_time(beige.n_id))- pwc.get_current_date_in_datetime()
        if time_to_beige_exit <= datetime.timedelta(hours=2, minutes=30):
            beiges_to_expire.append(beige.n_id)
            logger.info("")
            logger.info(str(beige.n_id) + " "+ str(beige.color) + " to expire in "+str(time_to_beige_exit))
            logger.info("")
        else :
            print beige.n_id,",",
    except WhyIsNationInBeige:
        logger.info("\nshit this nation is in beige, why?? " + str(beige.n_id))
    except NationDoesNotExistError:
        logger.info( "\nshit this nation doesn't exist wat " + str(beige.n_id))

filepath = "/root/politicsandwar/pnw_stats_finder/servlet/recipients.txt"

if len(beiges_to_expire) > 0:
    with open(filepath) as file:
        for line in file:
            recipient = line.strip()
            if len(recipient) > 0:
                send_email(recipient, 'html table test',create_html_table(beiges_to_expire, pwc.get_next_turn_in_datetime()))
