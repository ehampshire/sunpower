#!/usr/bin/python

import sys
import argparse
from os import path
from configparser import ConfigParser
import mysql.connector
from mysql.connector import errorcode
import datetime, time, pytz
from time import gmtime, strftime
from datetime import datetime, timedelta
import argparse

# constants
PROGRAM_NAME = "solar_analysis"
CONFIG_FILE_NAME = PROGRAM_NAME + ".conf"
MENU_MAIN_DESC = "SunPower solar analysis of raw data sent to SunPower's portal, populating SP_POWER and SP_ENERGY tables in the mysql DB.\nCreated by Eric Hampshire (ehampshire@gmail.com)."
PROGRAM_VERSION = '1.0'
cnx = mysql.connector
fmt = '%Y-%m-%d %H:%M:%S %Z%z'
ignoreTimestamp=False
global_produced_counter = 0

def main():
    global cnx, fmt, ignoreTimestamp
    # build main menu parser
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=MENU_MAIN_DESC)
    parser.add_argument('-V', '-v', '--version', action='version',
                        version='%(prog)s (version {})'.format(PROGRAM_VERSION))
    parser.add_argument("-c", "-config", dest="config", default=None, required=False, help="Optional config path.")
    parser.add_argument("-i", dest="ignoreTimestamp", action="store_true", help="Ignore timestamp (ie. process all rows in the SP_RAW_PRODUCTION table).")
    parser.set_defaults(ignoreTimestamp=False)

    # parse the user's args
    args = parser.parse_args()
    ignoreTimestamp = args.ignoreTimestamp

    # get config path and load config object
    config_path = get_config_path(args)
    config = load_config(config_path)

    dbHost = config["defaults"]["dbHost"]
    dbName = config["defaults"]["dbName"]
    dbUser = config["defaults"]["dbUser"]
    dbPassword = config["defaults"]["dbPassword"]

    # setup date variables
    today =  datetime.now()
    yesterday = today - timedelta(days=1)
    todayString = today.strftime("%Y-%m-%d")
    yesterdayString = yesterday.strftime("%Y-%m-%d")
    print "today: %s" % (todayString)
    print "yesterday: %s" % (yesterdayString)
    utc = datetime.utcnow()
    utcString = utc.strftime(fmt)
    print "utc: %s" % (utcString)

    if (dbHost is None or dbName is None or dbUser is None or dbPassword is None):
        print("Something is wrong with your DB config, please specify the config file or check your settings.")
        sys.exit(1)
    try:
        cnx = mysql.connector.connect(user=dbUser, password=dbPassword, host=dbHost, database=dbName)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
       if (ignoreTimestamp):
           min_timestamp = get_min_timestamp("sp_raw_production")
           #max_timestamp = get_max_timestamp("sp_raw_production")
           #print "min_timestamp: %s" % (min_timestamp)
           #print "max_timestamp: %s" % (max_timestamp)
           #read_used(min_timestamp, max_timestamp)
           #read_produced(min_timestamp, max_timestamp)
           read_used(min_timestamp[0])
           read_produced(min_timestamp[0])
           max_timestamp_power = get_max_timestamp("sp_energy")
           read_power(max_timestamp_power[0])
       else:
           max_timestamp = get_max_timestamp("sp_power")
           #read_used(yesterdayString, todayString)
           #read_produced(yesterdayString, todayString)
           read_used(max_timestamp[0])
           read_produced(max_timestamp[0])
           max_timestamp_power = get_max_timestamp("sp_energy")
           read_power(max_timestamp_power[0])
       cnx.close()

def load_config(config_path):
    # configure the config parser
    config = ConfigParser()
    if config_path is not None:
        config.read(config_path)
    return config

def get_config_path(args):
    # if the config file is provided via command line arg then always use that
    if args.config is not None:
        return args.config

    # otherwise look for a config file path
    config_file = None
    config_home = path.join(path.expanduser("~/.config/"), CONFIG_FILE_NAME)
    config_etc = path.join("/etc/", CONFIG_FILE_NAME)

    # conf file search order:
    #   1. search the executable directory
    #   2. search the user's home directory
    #   3. search /etc
    if path.isfile(CONFIG_FILE_NAME):
        config_file = path.join(".", CONFIG_FILE_NAME)
    elif path.isfile(config_home):
        config_file = config_home
    elif path.isfile(config_etc):
        config_file = config_etc
    return config_file

def get_min_timestamp(tablename):
    global cnx
    icursor = cnx.cursor()
    if (tablename == 'sp_power'):
        sql = "SELECT min(period) FROM `%s`" % (tablename) 
    else:
        sql = "SELECT min(src_timestamp) FROM `%s`" % (tablename) 
    icursor.execute(sql)
    timestamp = icursor.fetchone()
    return timestamp

def get_max_timestamp(tablename):
    global cnx
    icursor = cnx.cursor()
    if (tablename == 'sp_power' or tablename == 'sp_energy'):
        sql = "SELECT max(period) FROM `%s`" % (tablename) 
    else:
        sql = "SELECT max(src_timestamp) FROM `%s`" % (tablename) 
    icursor.execute(sql)
    timestamp = icursor.fetchone()
    return timestamp

def insert_used_line_into_sp_power(src_timestamp, used_watts):
    global cnx
    if used_watts == 0:
        return;
    icursor = cnx.cursor()
    sql = "SELECT id FROM `sp_power` WHERE period='%s'" % (src_timestamp)
    icursor.execute(sql)
    update = False
    id = icursor.fetchone()
    if (id is None):
        sql = "INSERT into sp_power(period, used) VALUES ('%s', '%s')" % (src_timestamp, used_watts)
    else:
        update = True
        sql = "UPDATE sp_power SET used='%s' where period='%s'" % (used_watts, src_timestamp)
    #print "sql: %s" % (sql)
    icursor.execute(sql)
    print(icursor.statement)
    id = icursor.lastrowid
    #print "Insert/Update SUCCESS! TableID: ", id
    cnx.commit()

def insert_produced_line_into_sp_power(src_timestamp, produced_watts):
    global cnx
    if produced_watts == 0:
        return;
    icursor = cnx.cursor()
    sql = "SELECT id FROM `sp_power` WHERE period='%s'" % (src_timestamp)
    icursor.execute(sql)
    update = False
    id = icursor.fetchone()
    if (id is None):
        sql = "INSERT into sp_power(period, generated) VALUES ('%s', '%s')" % (src_timestamp, produced_watts)
    else:
        update = True
        sql = "UPDATE sp_power SET generated='%s' where period='%s'" % (produced_watts, src_timestamp)
    #print "sql: %s" % (sql)
    icursor.execute(sql)
    print(icursor.statement)
    id = icursor.lastrowid
    #print "Insert/Update SUCCESS! TableID: ", id
    cnx.commit()

def insert_line_into_sp_energy(period, per_produced, per_used, per_net, cum_produced, cum_used, cum_net):
    global cnx
    icursor = cnx.cursor()
    sql = "SELECT id FROM `sp_energy` WHERE period='%s'" % (period)
    icursor.execute(sql)
    update = False
    id = icursor.fetchone()
    if (id is None):
        sql = "INSERT into sp_energy(period, per_produced, per_used, per_net, cum_produced, cum_used, cum_net) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (period, per_produced, per_used, per_net, cum_produced, cum_used, cum_net)
    else:
        update = True
        sql = "UPDATE sp_energy SET per_produced='%s', per_used='%s', per_net='%s', cum_produced='%s', cum_used='%s', cum_net='%s' where period='%s'" % (per_produced, per_used, per_net, cum_produced, cum_used, cum_net, period)
    #print "sql: %s" % (sql)
    icursor.execute(sql)
    print(icursor.statement)
    id = icursor.lastrowid
    print "Insert/Update SUCCESS! TableID: ", id
    cnx.commit()

#def read_used(start_timestamp, end_timestamp):
def read_used(start_timestamp):
    global cnx, ignoreTimestamp
    cursor = cnx.cursor(buffered=True)
    print "start_timestamp: %s" % (start_timestamp)
    #sql = "SELECT watts, src_timestamp, insert_timestamp FROM `sp_raw_production` WHERE insert_timestamp>='%s' and insert_timestamp<'%s' and message_type='140' order by insert_timestamp" % (start_timestamp, end_timestamp)
    if (ignoreTimestamp):
        sql = "SELECT watts, src_timestamp, insert_timestamp FROM `sp_raw_production` WHERE message_type='140' order by insert_timestamp" 
    else:
        sql = "SELECT watts, src_timestamp, insert_timestamp FROM `sp_raw_production` WHERE src_timestamp>='%s' and message_type='140' order by insert_timestamp" % (start_timestamp)
    # Execute the SQL command
    cursor.execute(sql)
    print(cursor.statement)
    rowcount = cursor.rowcount
    if (rowcount < 2):
        new_timestamp = start_timestamp - timedelta(minutes=5)
        read_used(new_timestamp)
        return
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    total_watts = 0;
    last_watts = 0;
    counter = 0;
    for row in results:
       difference = 0;
       calculated_watts = 0;
       watts = row[0]
       src_timestamp = row[1]
       insert_timestamp = row[2]
       if (last_watts != 0):
           difference = watts - last_watts
           total_watts = total_watts + difference
           temper = difference / 0.08333333333;
           calculated_watts = round(temper, 5);
 
       last_watts = watts
       # Now print fetched result
       #print "watts=%s : src_timestamp=%s :  insert_timestamp=%s : total_watts=%s : difference=%s : calculated_watts=%s" % (watts, src_timestamp, insert_timestamp, total_watts, difference, calculated_watts)
       if calculated_watts != 0:
           insert_used_line_into_sp_power(src_timestamp, calculated_watts)
       counter = counter + 1;
    print "total watts: %s" % (total_watts)
    print "total rows: %s" % (counter)

#def read_produced(start_timestamp, end_timestamp):
def read_produced(start_timestamp):
    global cnx, ignoreTimestamp, fmt, global_produced_counter
    cursor = cnx.cursor(buffered=True)
    sql = "SELECT distinct device_serial FROM `sp_raw_production` WHERE message_type='130'"
    # Execute the SQL command
    cursor.execute(sql)
    print(cursor.statement)
    # Fetch all the rows in a list of lists.
    devices = list(cursor.fetchall())
    print(devices)
    total_watts = 0;
    calculated_watts = 0;
    src_timestamp_dict = dict()
    print "start_timestamp: %s" % (start_timestamp)
    for i in devices:
	this_device = i[0]
        #print "this_device: %s" % (this_device)
        #sql = "SELECT watts, src_timestamp, insert_timestamp, device_serial FROM `sp_raw_production` WHERE insert_timestamp>='%s' and insert_timestamp<'%s' and message_type='130' and device_serial='%s' order by insert_timestamp" % (start_timestamp, end_timestamp, this_device)
        if (ignoreTimestamp):
            sql = "SELECT watts, src_timestamp, insert_timestamp, device_serial FROM `sp_raw_production` WHERE message_type='130' and device_serial='%s' order by insert_timestamp" % (this_device)
        else:
            sql = "SELECT watts, src_timestamp, insert_timestamp, device_serial FROM `sp_raw_production` WHERE src_timestamp>='%s' and message_type='130' and device_serial='%s' order by insert_timestamp" % (start_timestamp, this_device)
        # Execute the SQL command
        cursor.execute(sql)
        #print(cursor.statement)
        rowcount = cursor.rowcount
        if (rowcount < 2):
            print "Rowcount < 2 for %s" % (this_device)
            new_timestamp = start_timestamp - timedelta(minutes=5)
            global_produced_counter = global_produced_counter + 1
            if (global_produced_counter < 11):
                read_produced(new_timestamp)
                return
        this_device_total_watts = 0;
        this_device_calculated_watts = 0;
        last_watts = 0;
        counter = 0;
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
           difference = 0;
           calculated_watts = 0;
           watts = row[0]
           src_timestamp = row[1]
           insert_timestamp = row[2]
           device_serial = row[3]
           if (last_watts != 0):
               difference = watts - last_watts
               this_device_total_watts = this_device_total_watts + difference
               total_watts = total_watts + difference
               temper = difference / 0.08333333333;
               this_device_calculated_watts = round(temper, 5);
               calculated_watts = calculated_watts + this_device_calculated_watts
           last_watts = watts
           counter = counter + 1;
           if (src_timestamp_dict.has_key(src_timestamp)):
               src_timestamp_dict[src_timestamp] = src_timestamp_dict[src_timestamp] + this_device_calculated_watts
           else:
               src_timestamp_dict[src_timestamp] = this_device_calculated_watts
       # Now print fetched result
       #print "watts=%s : src_timestamp=%s :  insert_timestamp=%s : total_watts=%s : difference=%s : calculated_watts=%s" % (watts, src_timestamp, insert_timestamp, total_watts, difference, calculated_watts)
        print "this_device_total_watts (%s): %s , rowcount: %s" % (this_device, this_device_total_watts, rowcount)
        #print "this_device_calculated_watts (%s): %s" % (this_device, this_device_calculated_watts)
    print "total watts produced: %s" % (total_watts)
    #print "total rows: %s" % (counter)
    for src_timestamp, calculated_watts in src_timestamp_dict.items():
        #print "%s : %s" % (src_timestamp, calculated_watts)
        if calculated_watts != 0:
            insert_produced_line_into_sp_power(src_timestamp, calculated_watts)

def process_power_rows(start_timestamp, period, period_generated, period_used, period_counter):
    global ignoreTimestamp
    if (ignoreTimestamp):
        start_timestampDateString = start_timestamp
    else:
        start_timestampDateString = start_timestamp.strftime(fmt)
    cum_produced = 0;
    cum_used = 0;
    cum_net = 0;
    for period in sorted(period_generated.iterkeys()):
       if period_counter[period] < 10:
           print "Not a full period (%s), only found: %s , skipping..." % (period, period_counter[period])
           continue
       period_generatedV = round(period_generated[period] * 0.08333333333, 5)
       period_usedV = round(period_used[period] * 0.08333333333, 5)
       period_net = period_generatedV + period_usedV
       cum_net = cum_net + period_net
       cum_produced = cum_produced + period_generatedV
       cum_used = cum_used + period_usedV
       dbPeriod = start_timestampDateString + " " + period
       print "%s: used - %s , generated - %s, net - %s, cum_produced - %s, cum_used - %s, cum_net - %s" % (dbPeriod, period_usedV, period_generatedV, period_net, cum_produced, cum_used, cum_net)
       insert_line_into_sp_energy(dbPeriod, period_generatedV, period_usedV, period_net, cum_produced, cum_used, cum_net)

def read_power(start_timestamp):
    global cnx, ignoreTimestamp
    cursor = cnx.cursor(buffered=True)
    print "start_timestamp: %s" % (start_timestamp)
    fmt = '%Y-%m-%d'
    start_timestampDateString = start_timestamp.strftime(fmt)
    #sql = "SELECT * FROM `sp_power` WHERE period>='2017-02-21' and period<='2017-02-22' order by period"
    if (ignoreTimestamp):
        sql = "SELECT * FROM `sp_power` order by period" 
    else:
        sql = "SELECT * FROM `sp_power` WHERE period>='%s' order by period" % (start_timestamp)
        #sql = "SELECT * FROM `sp_power` WHERE period>='2017-02-21' and period<='2017-02-22' order by period"
    # Execute the SQL command
    cursor.execute(sql)
    print(cursor.statement)
    rowcount = cursor.rowcount
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    counter = 0;
    period_generated = dict()
    period_used = dict()
    period_counter = dict()
    dater_generated = dict()
    dater_used = dict()
    dater_counter = dict()
    last_dateString = ""
    for row in results:
       difference = 0;
       calculated_watts = 0;
       id = row[0]
       period = row[1]
       generated = row[2]
       used = row[3]
       fmt = '%Y-%m-%d'
       dateString = period.strftime(fmt)
       if (ignoreTimestamp):
           if (dateString != last_dateString):
               period_generated = dict()
               period_used = dict()
               period_counter = dict()
       last_dateString = period.strftime(fmt)
       #if (ignoreTimestamp is False and dateString != start_timestampDateString):
           #continue;
       fmt = '%H'
       hourString = period.strftime(fmt)
       if (period_generated.has_key(hourString)):
           period_generated[hourString] = period_generated[hourString] + generated
       else:
           period_generated[hourString] = generated
       if (period_used.has_key(hourString)):
           period_used[hourString] = period_used[hourString] + used
           if (period_counter.has_key(hourString)):
               period_counter[hourString] = period_counter[hourString] + 1;
           else:
               period_counter[hourString] = 0
       else:
           period_used[hourString] = used
           if (period_counter.has_key(hourString)):
               period_counter[hourString] = period_counter[hourString] + 1;
           else:
               period_counter[hourString] = 0
       # Now print fetched result
       #print "id=%s : period=%s :  generated=%s : used=%s" % (id, period, generated, used)
       if (ignoreTimestamp):
           dater_generated[dateString] = period_generated
           dater_used[dateString] = period_used
           dater_counter[dateString] = period_counter
    if (ignoreTimestamp):
        for period in sorted(dater_generated.iterkeys()):
            #print "period: %s" % (period)
            process_power_rows(period, period, dater_generated[period], dater_used[period], dater_counter[period])
    else:
         fmt = '%Y-%m-%d %H'
         dateString = start_timestamp.strftime(fmt)
         process_power_rows(start_timestamp, dateString, period_generated, period_used, period_counter)

if __name__ == "__main__":
    sys.exit(main())
