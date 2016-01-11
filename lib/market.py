from datetime import datetime

realstring_dict = {'steel': 'steel', 'oil': 'oil', 'lead': 'lead', 'aluminum': 'aluminum', 'munition': 'munitions', 'food': 'food', 'bauxite': 'bauxite', 'uranium': 'uranium', 'coal': 'coal', 'iron': 'iron', 'gasoline': 'gasoline'}

__author__ = 'shawkins'

def get_long_short_term_averages(pwdb, num_records=3000):
    # get recent data
    long_term_average_records = pwdb.get_recent_market_records(num_records=num_records)
    short_term_average_records = long_term_average_records[-1000:]
    long_term_averages = []
    for i in range(len(long_term_average_records)):
        current_record = long_term_average_records[i]
        formatted_time = datetime.strftime(current_record['time'], "%y-%m-%d %H:%M:%S")
        average_dict = {"date": current_record['time'],
                        "morris_date": formatted_time}
        for item_type in realstring_dict.keys():
            if len(long_term_averages) < 1:
                # calc for sells
                average_sell_at_index = current_record['values'][item_type]['sell']
                # calc for buys
                average_buy_at_index = current_record['values'][item_type]['buy']
            else:
                # fast rolling average without looping
                average_sell_at_index = long_term_averages[-1][item_type + 'avg_sell'] * len(long_term_averages) + current_record['values'][item_type]['sell']
                average_sell_at_index /= float(len(long_term_averages) + 1)
                average_buy_at_index = long_term_averages[-1][item_type + 'avg_buy'] * len(long_term_averages) + current_record['values'][item_type]['buy']
                average_buy_at_index /= float(len(long_term_averages) + 1)
            average_dict[item_type + "avg_sell"] = average_sell_at_index
            average_dict[item_type + "avg_buy"] = average_buy_at_index
            average_dict[item_type + "buy"] = current_record['values'][item_type]["buy"]
            average_dict[item_type + "sell"] = current_record['values'][item_type]["sell"]
        long_term_averages.append(average_dict)

    short_term_averages = []
    for i in range(len(short_term_average_records)):
        current_record = short_term_average_records[i]
        average_dict = {"date": current_record['time']}
        for item_type in realstring_dict.keys():
            if len(short_term_averages) < 1:
                # calc for sells
                average_sell_at_index = current_record['values'][item_type]['sell']
                # calc for buys
                average_buy_at_index = current_record['values'][item_type]['buy']
            else:
                # fast rolling average without looping
                average_sell_at_index = short_term_averages[-1][item_type + 'avg_sell'] * len(short_term_averages) + current_record['values'][item_type]['sell']
                average_sell_at_index /= float(len(short_term_averages) + 1)
                average_buy_at_index = short_term_averages[-1][item_type + 'avg_buy'] * len(short_term_averages) + current_record['values'][item_type]['buy']
                average_buy_at_index /= float(len(short_term_averages) + 1)
            average_dict[item_type + "avg_sell"] = average_sell_at_index
            average_dict[item_type + "avg_buy"] = average_buy_at_index
            average_dict[item_type + "buy"] = current_record['values'][item_type]["buy"]
            average_dict[item_type + "sell"] = current_record['values'][item_type]["sell"]
        short_term_averages.append(average_dict)
    long_term_averages = long_term_averages[-600:]
    short_term_averages = short_term_averages[-600:]

    return long_term_averages, short_term_averages
