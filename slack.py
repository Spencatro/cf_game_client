import json
import os
import slackclient

__author__ = 'shawkins'


ROBOT_CHANNEL_ID = os.environ.get("robot_channel_id")
MARKET_CHANNEL = os.environ.get("market_channel_id")


def post_good_buy(good, good_url, average_price, current_price, image_url):

    test_attachment = {
        "color": "#2883BD",
        "text": "There's an extra spicy BUY deal on the market right now!",
        "title": "PNW Market: " + good.capitalize(),
        "title_link": good_url,
        "image_url": image_url,
        "fields": [
            {
                "title": "Resource",
                "value": good,
                "short": False
            },
            {
                "title": "Average Price",
                "value": average_price,
                "short": True
            },
            {
                "title": "Current Price",
                "value": current_price,
                "short": True
            }
        ]

    }
    post_to_market_channel("", attachments=json.dumps([test_attachment]))


def post_good_sell(good, good_url, average_price, current_price, image_url):
    test_attachment = {
        "color": "#FF7B0C",
        "text": "There's an extra spicy SELL deal on the market right now!",
        "title": "PNW Market: "+good.capitalize(),
        "title_link": good_url,
        "image_url": image_url,
        "fields": [
            {
                "title": "Resource",
                "value": good,
                "short": False
            },
            {
                "title": "Average Price",
                "value": average_price,
                "short": True
            },
            {
                "title": "Current Price",
                "value": current_price,
                "short": True
            }
        ]

    }
    post_to_market_channel("", attachments=json.dumps([test_attachment]))


def post_good_buy_offer(good, good_url, average_sell_price, current_buy_price):

    test_attachment = {
        "color": "#2883BD",
        "text": "There's a 'buy' offer for a good that is higher than the average 'sell' offer! Take this deal!",
        "title": "PNW Market: " + good.capitalize(),
        "title_link": good_url,
        "fields": [
            {
                "title": "Resource",
                "value": good,
                "short": False
            },
            {
                "title": "Average SELL Price",
                "value": average_sell_price,
                "short": True
            },
            {
                "title": "Current BUY Price",
                "value": current_buy_price,
                "short": True
            }
        ]

    }
    post_to_market_channel("", attachments=json.dumps([test_attachment]))


def post_to_market_channel(message, attachments=None):
    sc = slackclient.SlackClient(os.environ.get("slack_token"))
    sc.api_call("chat.postMessage", channel=MARKET_CHANNEL, text=message, username="ROBIE The Robot Bank!", icon_url="http://www.theoldrobots.com/images6/money5.JPG", attachments=attachments)
