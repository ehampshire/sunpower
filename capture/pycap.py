#!/usr/bin/python

import sys
import argparse
from os import path
from configparser import ConfigParser
import pcapy, re, os
import mysql.connector
from mysql.connector import errorcode
import datetime, time
from time import gmtime, strftime
from impacket.ImpactDecoder import *

# constants
PROGRAM_NAME = "pycap"
CONFIG_FILE_NAME = PROGRAM_NAME + ".conf"
MENU_MAIN_DESC = "Capture TCP traffic from a SunPower PV monitor, populating SP_RAW_PRODUCTION table in the mysql DB.\nCreated by Eric Hampshire (ehampshire@gmail.com)."
PROGRAM_VERSION = '1.0'
regex = re.compile(r'^([0-9]+)\t')

def main():
    global MAC, logFileDir, dbUser, dbPassword, dbName, dbHost

    # build main menu parser
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description=MENU_MAIN_DESC)
    parser.add_argument('-V', '-v', '--version', action='version',
                        version='%(prog)s (version {})'.format(PROGRAM_VERSION))
    parser.add_argument("-c", "-config", dest="config", default=None, required=False, help="Optional config path.")

    # parse the user's args
    args = parser.parse_args()

    # get config path and load config object
    config_path = get_config_path(args)
    config = load_config(config_path)

    dbHost = config["defaults"]["dbHost"]
    dbName = config["defaults"]["dbName"]
    dbUser = config["defaults"]["dbUser"]
    dbPassword = config["defaults"]["dbPassword"]
    MAC = config["defaults"]["MAC"]
    ipAddress = config["defaults"]["ipAddress"]
    logFileDir = config["defaults"]["logFileDir"]

    # Grab a list of interfaces that pcap is able to listen on.
    # The current user will be able to listen from all returned interfaces,
    # using open_live to open them.
    max_bytes = 10000
    promiscuous = True
    read_timeout = 100 # in milliseconds
    dev = "eth0"
    ifs = pcapy.findalldevs()
    
    # No interfaces available, abort.
    if 0 == len(ifs):
        print "You don't have enough permissions to open any interface on this system."
        sys.exit(1)
    
    # Only one interface available, use it.
    elif 1 == len(ifs):
        print 'Only one interface present, defaulting to it.'
        dev=ifs[0]
    
    pc = pcapy.open_live(dev, max_bytes, promiscuous, read_timeout)

    pc.setfilter('tcp')
    pc.setfilter("ip && tcp && dst net %s && dst port 80" % (ipAddress))
    #pc.setfilter("ip && tcp && dst net %s && dst port 80 && ether src %s" % (ipAddress, MAC))

    packet_limit = -1 # infinite
    pc.loop(packet_limit, recv_pkts) # capture packets

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

def getLoggingTime():
    return datetime.datetime.now().strftime("%Y%m%d")

def appendLog(line):
    global logFileDir
    if not line:
       return
    this_line = line.split()
    if (len(this_line) < 1):
       return
    if (this_line[0] == "POST" or this_line[0] == "Host:" or this_line[0] == "Content-Type:" or this_line[0] == "Content-Length:"):
       return
    logFileName = logFileDir + getLoggingTime() + "-py.txt"
    #logFileName = logFileDir + getLoggingTime() + ".txt"
    #print "logFileName: %s" % (logFileName)
    with open(logFileName, 'a') as the_file:
        last_line = tail(logFileName)
        insert_line = last_line.split()
        candidate = False
        if (len(insert_line) < 14):
            if (len(insert_line) < 1):
                candidate = False
            elif (insert_line[0] == "140"):
                if (len(insert_line) < 3):
                    candidate = False
                elif (len(insert_line) > 12 or insert_line[2] == "PVS5M508095p" or insert_line[2] == "PVS5M508095c"):
                    candidate = False
                else:
                    if (this_line[0] != "130" or this_line[0] != "140"):
                        candidate = True
            elif (insert_line[0] == "130"):
                if (this_line[0] != "130" and this_line[0] != "140"):
                    candidate = True
        if (candidate):
            last_line = last_line.replace('\r\n', '').rstrip() 
            print 'last_line: %s\nthis_line: %s' % (last_line, line)
            new_line = last_line + line.lstrip()
            the_file.write('%s\n' % (new_line))
            #the_file.write('%s\n' % (line))
            insertLineIntoDb(new_line)
        else:
            the_file.write('%s\n' % (line))
            insertLineIntoDb(line)
    the_file.close()

def tail(filepath):
    try:
        filepath.is_file
        fp = str(filepath)
    except AttributeError:
        fp = filepath

    with open(fp, "rb") as f:
        size = os.stat(fp).st_size
        start_pos = 0 if size - 1 < 0 else size - 1

        if start_pos != 0:
            f.seek(start_pos)
            char = f.read(1)

            if char == b"\n":
                start_pos -= 1
                f.seek(start_pos)

            if start_pos == 0:
                f.seek(start_pos)
            else:
                char = ""

                for pos in range(start_pos, -1, -1):
                    f.seek(pos)

                    char = f.read(1)

                    if char == b"\n":
                        break

        return f.readline()

# callback for received packets
def recv_pkts(hdr, data):
    global regex
    packet = EthDecoder().decode(data)
    #print packet
    ip = packet.child()
    tcp = ip.child()
    #print tcp
    adata = tcp.get_data_as_string() 
    #adata = adata.replace('\r\n', '\r\n###~~~###') 
    arrline = adata.split('\n') 
    #print arrline
    counter = 0;
    for line in arrline:
        #print "%s: %s" % (counter, line)
        counter = counter + 1
        matcher = regex.match(line)
        if matcher:
            msg = matcher.group().strip()
            #print "msg: %s" % (msg)
            if (msg == "140"):  # this is a net metering message, and $value is net metering value in (IIRC) W averaged over the 5-minute interval
		# consumption = (corresponding production) + net
                print "net metering message (140):\n\t%s\n" % (line)
                appendLog(line)
            elif (msg == "130"): # this is a production message, and $value is a production valuein (IIRC) W averaged over the 5-minute interval
                print "production message (130):\n\t%s\n" % (line)
                appendLog(line)
            elif (msg == "100"):  # this is a control message / keep-alive
		print "control message (100):\n\t%s\n" % (line)
            elif (msg == "102"): # this is a checksum message
		print "checksum message (102):\n\t%s\n" % (line)
            elif (msg == "141"): # this is a consumption message?
		print "message (141):\n\t%s\n" % (line)
            elif (msg == "120"): # this is a consumption message?
		print "message (120):\n\t%s\n" % (line)
            else: 
		print "unknown message:\n\t%s\n" % (line)
                appendLog(line)
        else:
	     print "unmatched message:\n\t%s\n" % (line)
             appendLog(line)

def insertLineIntoDb(line):
    global dbUser, dbPassword, dbHost, dbName
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
        #print "We are logged in!"
        add_raw_production_sql_130 = ("INSERT INTO sp_raw_production "
                   "(message_type, src_timestamp, device_serial, device_description, watts, v1, v2, v3, v4, v5, v6, v7, v8, v9) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        add_raw_production_sql_140 = ("INSERT INTO sp_raw_production "
                   "(message_type, src_timestamp, device_serial, device_description, v1, watts, v2, v3, v4, v5, v6, v7) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        add_raw_production_sql = add_raw_production_sql_130
        cursor = cnx.cursor()
        fcursor = cnx.cursor()
        #example_data = "130     20170108161000  414051636007015 AC_Module_Type_C                18.7783 0.0144  245.3928        0.1376  0.017   55.3412 0.3274  5.5     60.0006 0"
        #example_data = "140     20170108171000  PVS5M508095c    PVS5M0400c      125     648.84  -0.1225 1.1217  1.4173  -0.0836 60.029  0"
        #insert_line = example_data.split()
        insert_line = line.split()
        if (len(insert_line) < 14):
            if (insert_line[0] == "140"):
                if (len(insert_line) < 12):
                    return;
                elif (insert_line[3] == "PVS5M0400p"):
                    return;
                else:
                    add_raw_production_sql = add_raw_production_sql_140
            else:
                print "line missing values, skipping... insert_line: ", insert_line
                return
        #print insert_line
        #print "attempting to parse date..."
        new_timestamp = datetime.datetime.strptime(insert_line[1], "%Y%m%d%H%M%S")
        #print new_timestamp
        insert_line[1] = new_timestamp
        check_existing_record_query = ("SELECT id FROM `sp_raw_production` WHERE src_timestamp=%s and device_serial=%s")
        check_existing_record_data = (insert_line[1], insert_line[2])
        try:
            fcursor.execute(check_existing_record_query, check_existing_record_data)
            #print(fcursor.statement)
        except:
            print(fcursor.statement)
            raise
    
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
                print "Insert SUCCESS! TableID: ", id
            else:
                print "Row exists ", id," not adding!"

        #print "Logging out of the DB!"
        cnx.commit()
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    sys.exit(main())
