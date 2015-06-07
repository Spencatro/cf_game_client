__author__ = 'sxh112430'
import logging
import os
import time
import PWClient
import datetime
import sys

# recipients:  matodw@gmail.com, ashnicholson90@gmail.com

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("beige_watch.out", mode='w')
shandler = logging.StreamHandler(sys.stdout)
logger.addHandler(fhandler1)
logger.addHandler(shandler)
logger.setLevel(logging.INFO)

USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient.PWClient(USERNAME, PASS, logger=logger)

beiges_to_expire = []
skips = []
for beige in pwc.generate_all_nations_with_color('beige'):
# for beige in [pwc.get_nation_obj_from_ID(13348)]:
    if int(beige.n_id) in skips:
        print beige.n_id,",",
        continue
    try:
        time_to_beige_exit = pwc.get_next_turn_in_datetime(pwc.calculate_beige_exit_time(beige.n_id))- pwc.get_current_date_in_datetime()
        if time_to_beige_exit <= datetime.timedelta(hours=2, minutes=30):
            beiges_to_expire.append(beige.n_id)
            logger.info("")
            logger.info(str(beige.n_id) + " "+ str(beige.color) + " to expire in "+str(time_to_beige_exit))
            logger.info("")
        else :
            print beige.n_id,",",
    except PWClient.WhyIsNationInBeige:
        logger.info("\nshit this nation is in beige, why?? " + str(beige.n_id))
    except PWClient.NationDoesNotExistError:
        logger.info( "\nshit this nation doesn't exist wat " + str(beige.n_id))

logger.info( "reached the end of the list")
time.sleep((60 * 120) + 30)

for bte in beiges_to_expire:
    nation = pwc.get_nation_obj_from_ID(bte,skip_cache=True)
    logger.info( "Did nation expire? "+ str(nation.n_id)+ " "+str(nation.color))