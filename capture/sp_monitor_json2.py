#!/usr/bin/python

import urllib, json
import datetime, time
from time import gmtime, strftime
import sys
import argparse
from os import path
from configparser import ConfigParser
import pcapy, re, os
import mysql.connector
from mysql.connector import errorcode

# constants
PROGRAM_NAME = "sp_monitor_json"
CONFIG_FILE_NAME = PROGRAM_NAME + ".conf"
MENU_MAIN_DESC = "Capture TCP traffic from a SunPower PV monitor, populating SP_RAW_PRODUCTION table in the mysql DB.\nCreated by Eric Hampshire (ehampshire@gmail.com)."
PROGRAM_VERSION = '1.0'

def main():
    global ipAddress, dbUser, dbPassword, dbName, dbHost

    # build main menu parser
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=MENU_MAIN_DESC)
    parser.add_argument('-V', '-v', '--version', action='version',
                        version='%(prog)s (version {})'.format(PROGRAM_VERSION))
    parser.add_argument("-c", "-config", dest="config", default=None, required=False, help="Optional config path.")
    parser.add_argument("-i", "-ipAddress", dest="ipAddress", default=None, required=False, help="IP Address of the SunPower PV Monitor.")

    # parse the user's args
    args = parser.parse_args()

    # get config path and load config object
    config_path = get_config_path(args)
    config = load_config(config_path)

    dbHost = config["defaults"]["dbHost"]
    dbName = config["defaults"]["dbName"]
    dbUser = config["defaults"]["dbUser"]
    dbPassword = config["defaults"]["dbPassword"]
    ipAddress = config["defaults"]["ipAddress"]

    url = "http://{}/cgi-bin/dl_cgi?Command=DeviceList".format(str(ipAddress))
    print ("Attempting to hit URL: %s") % (url)
    response = urllib.urlopen(url)
    parsed = json.loads(response.read())
    #print json.dumps(parsed, indent=4, sort_keys=True)

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

    counter = 0
    for x in parsed["devices"]:
        this_device_serial = x["SERIAL"] 
        DATATIME = x["DATATIME"]
        datatime_timestamp = datetime.datetime.strptime(DATATIME, "%Y,%m,%d,%H,%M,%S")

        if (this_device_serial != "PVS5M508095p" and this_device_serial != "PVS5M508095c" and this_device_serial != "ZT162585000441C1402"):
            #ac_power = float(x["ac_power"])  * 1000
            ac_power = float(x["p_3phsum_kw"])  * 1000
            print ("%s : %s : %s : %s") % (counter, this_device_serial, ac_power, datatime_timestamp)
            insert_microinverter_line(cnx, x, datatime_timestamp)
    
        elif (this_device_serial == "PVS5M508095c"):
            #power_w = x["power_w"]
            #energy_total = x["energy_total"]
            power_w = x["p_3phsum_kw"]
            energy_total = x["net_ltea_3phsum_kwh"]
            print ("%s : %s : %s : %s") % (counter, this_device_serial, power_w, energy_total)
            insert_pv_monitor_line(cnx, x, datatime_timestamp)
        counter+=1

    #print "Logging out of the DB!"
    cnx.commit()
    cnx.close()

def insert_pv_monitor_line(cnx, x, datatime_timestamp):
    '''
    PV monitor example:
            "CAL0": "125",
            "CURTIME": "2017,03,30,16,06,41",
            "DATATIME": "2017,03,30,16,06,34",
            "DESCR": "Power Meter PVS5M508095c",
            "DEVICE_TYPE": "Power Meter",
            "ISDETAIL": "1",
            "MODEL": "PVS5M0400c",
            "PORT": "",
            "SERIAL": "PVS5M508095c",
            "STATE": "working",
            "STATEDESCR": "Working",
            "SWVER": "4",
            "TYPE": "PVS5-METER-C",
            "ct_scaler": "125",
            "energy_total": "840.63",
            "freq": "60.02",
            "power_factor": "0.5649",
            "power_va": "1.6723",
            "power_var": "1.1325",
            "power_w": "0.9447"
    They changed it!
        {
                "ISDETAIL":"1",
                "SERIAL":"PVS5M508095c",
                "TYPE":"PVS5-METER-C",
                "STATE":"working",
                "STATEDESCR":"Working",
                "MODEL":"PVS5M0400c",
                "DESCR":"Power Meter PVS5M508095c",
                "DEVICE_TYPE":"Power Meter",
                "SWVER":"4",
                "PORT":"",
                "DATATIME":"2017,06,30,14,56,51",
                "ct_scl_fctr":"125",
                "net_ltea_3phsum_kwh":"-640.39",
                "p_3phsum_kw":"-1.8784",
                "q_3phsum_kvar":"0.5875",
                "s_3phsum_kva":"2.0794",
                "tot_pf_rto":"-0.9033",
                "freq_hz":"60.02",
                "CAL0":"125",
                "CURTIME":"2017,06,30,14,57,04"
        },
    '''
    cursor = cnx.cursor()
    fcursor = cnx.cursor()
    check_existing_record_query = ("SELECT id FROM `sp_raw2` WHERE src_timestamp=%s and device_serial=%s")
    check_existing_record_data = (datatime_timestamp, x["SERIAL"])
    try:
        fcursor.execute(check_existing_record_query, check_existing_record_data)
        #print(fcursor.statement)
    except:
        print(fcursor.statement)
        raise

    add_raw_production_sql = ("INSERT INTO sp_raw2 "
               "(device_serial, src_timestamp, ac_curr, ac_power, ac_volt, dc_curr, dc_power, dc_volt, energy_total, heatsink_temp) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    insert_line = [] 
    insert_line.append(x["SERIAL"])
    insert_line.append(datatime_timestamp)
    insert_line.append("0")
    insert_line.append("0")
    insert_line.append("0")
    insert_line.append("0")
    insert_line.append("0")
    insert_line.append("0")
    #insert_line.append(x["energy_total"])
    insert_line.append(x["net_ltea_3phsum_kwh"])
    insert_line.append("0")

    if (fcursor.with_rows):
        id = fcursor.fetchone()
        if (id is None):
            try:
                cursor.execute(add_raw_production_sql, insert_line)
                print(cursor.statement)
            except:
                print(insert_line)
                print(cursor.statement)
                raise
            id = cursor.lastrowid
            print ("Insert SUCCESS! TableID: %s", id)
        else:
            print ("Row exists $s not adding!", id)
    cursor.close()
    fcursor.close()

def insert_microinverter_line(cnx, x, datatime_timestamp):
    '''
    microinverter example:
            "CURTIME": "2017,03,30,16,06,45",
            "DATATIME": "2017,03,30,16,04,34",
            "DESCR": "Inverter 414051637009125",
            "DEVICE_TYPE": "Inverter",
            "ISDETAIL": "1",
            "MODEL": "AC_Module_Type_C",
            "PORT": "",
            "SERIAL": "414051637009125",
            "STATE": "working",
            "STATEDESCR": "Working",
            "SWVER": "951007408",
            "TYPE": "SOLARBRIDGE",
            "ac_curr": "0.1049",
            "ac_power": "0.0082",
            "ac_volt": "245.6353",
            "dc_curr": "0.259",
            "dc_power": "0.011",
            "dc_volt": "53.8978",
            "energy_total": "107.9195",
            "freq": "60.024",
            "heatsink_temp": "19.25"
    They changed it!
        {
                "ISDETAIL":"1",
                "SERIAL":"414051637006465",
                "TYPE":"SOLARBRIDGE",
                "STATE":"working",
                "STATEDESCR":"Working",
                "MODEL":"AC_Module_Type_C",
                "DESCR":"Inverter 414051637006465",
                "DEVICE_TYPE":"Inverter",
                "SWVER":"951007408",
                "PORT":"",
                "MOD_SN":"",
                "NMPLT_SKU":"",
                "DATATIME":"2017,06,30,14,56,21",
                "ltea_3phsum_kwh":"284.4779",
                "p_3phsum_kw":"0.107",
                "vln_3phavg_v":"247.3326",
                "i_3phsum_a":"0.4554",
                "p_mpptsum_kw":"0.112",
                "v_mppt1_v":"56.2324",
                "i_mppt1_a":"2.0239",
                "t_htsnk_degc":"30.75",
                "freq_hz":"60.042",
                "CURTIME":"2017,06,30,14,57,04"
        },
    '''
    cursor = cnx.cursor()
    fcursor = cnx.cursor()
    check_existing_record_query = ("SELECT id FROM `sp_raw2` WHERE src_timestamp=%s and device_serial=%s")
    check_existing_record_data = (datatime_timestamp, x["SERIAL"])
    try:
        fcursor.execute(check_existing_record_query, check_existing_record_data)
        #print(fcursor.statement)
    except:
        print(fcursor.statement)
        raise

    add_raw_production_sql = ("INSERT INTO sp_raw2 "
               "(device_serial, src_timestamp, ac_curr, ac_power, ac_volt, dc_curr, dc_power, dc_volt, energy_total, heatsink_temp) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    insert_line = [] 
    insert_line.append(x["SERIAL"])
    insert_line.append(datatime_timestamp)

    #insert_line.append(x["ac_curr"])
    insert_line.append(x["i_3phsum_a"])

    #insert_line.append(x["ac_power"])
    insert_line.append(x["p_3phsum_kw"])

    #insert_line.append(x["ac_volt"])
    insert_line.append(x["vln_3phavg_v"])

    #insert_line.append(x["dc_curr"])
    insert_line.append(x["i_mppt1_a"])

    #insert_line.append(x["dc_power"])
    insert_line.append(x["p_mpptsum_kw"])

    #insert_line.append(x["dc_volt"])
    insert_line.append(x["v_mppt1_v"])

    #insert_line.append(x["energy_total"])
    insert_line.append(x["ltea_3phsum_kwh"])

    #insert_line.append(x["heatsink_temp"])
    insert_line.append(x["t_htsnk_degc"])

    if (fcursor.with_rows):
        id = fcursor.fetchone()
        if (id is None):
            try:
                cursor.execute(add_raw_production_sql, insert_line)
                print(cursor.statement)
            except:
                print(insert_line)
                print(cursor.statement)
                raise
            id = cursor.lastrowid
            print ("Insert SUCCESS! TableID: %s", id)
        else:
            print ("Row exists %s not adding!", id)
    cursor.close()
    fcursor.close()

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
    config_home = path.join(path.expanduser("~/.config/pycap.conf"), CONFIG_FILE_NAME)
    config_etc = path.join("/etc", CONFIG_FILE_NAME)

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

if __name__ == "__main__":
    sys.exit(main())
