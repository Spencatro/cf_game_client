__author__ = 'sxh112430'
import logging
import os
import time
import PWClient
import datetime

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("pwc.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.INFO)

USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient.PWClient(USERNAME, PASS, logger=logger)

beiges_to_expire = []
for beige in pwc.generate_all_nations_with_color('beige'):
    try:
        if pwc.calculate_beige_exit_time(beige.n_id) - pwc.get_current_date_in_datetime() < datetime.timedelta(hours=1):
            beiges_to_expire.append(beige.n_id)
            logger.info("")
            logger.info(str(beige.n_id) + " "+ str(beige.color) + " to expire in less than one hour")
            logger.info("")
        else :
            print ".",
    except PWClient.WhyIsNationInBeige:
        logger.info("\nshit this nation is in beige, why?? " + str(beige.n_id))
    except PWClient.NationDoesNotExistError:
        logger.info( "\nshit this nation doesn't exist wat " + str(beige.n_id))

logger.info( "reached the end of the list")
time.sleep(60 * 60)

for bte in beiges_to_expire:
    nation = pwc.get_nation_obj_from_ID(bte,skip_cache=True)
    logger.info( "Did nation expire? "+ str(nation.n_id)+ " "+str(nation.color))