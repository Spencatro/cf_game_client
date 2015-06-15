__author__ = 'sxh112430'
import logging
import os
import time
import pw_client
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
pwc = pw_client.PWClient(USERNAME, PASS, logger=logger)

beiges_to_expire = []
skips = []
for beige in pwc.generate_all_nations_with_color('beige'):
# for beige in [pwc.get_nation_obj_from_ID(13348)]:
    if int(beige.nation_id) in skips:
        print beige.nation_id,",",
        continue
    try:
        time_to_beige_exit = pwc.get_next_turn_in_datetime(pwc.calculate_beige_exit_time(beige.nation_id))- pwc.get_current_date_in_datetime()
        if time_to_beige_exit <= datetime.timedelta(hours=2, minutes=30):
            beiges_to_expire.append(beige.nation_id)
            logger.info("")
            logger.info(str(beige.nation_id) + " "+ str(beige.color) + " to expire in "+str(time_to_beige_exit))
            logger.info("")
        else :
            print beige.nation_id,",",
    except pw_client.WhyIsNationInBeige:
        logger.info("\nshit this nation is in beige, why?? " + str(beige.nation_id))
    except pw_client.NationDoesNotExistError:
        logger.info( "\nshit this nation doesn't exist wat " + str(beige.nation_id))

logger.info( "reached the end of the list")
time.sleep((60 * 120) + 30)

for bte in beiges_to_expire:
    nation = pwc.get_nation_obj_from_ID(bte,skip_cache=True)
    logger.info( "Did nation expire? "+ str(nation.nation_id)+ " "+str(nation.color))