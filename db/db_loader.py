#!/usr/bin/python

import mysql.connector
from mysql.connector import errorcode
import datetime, time
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='This utility loads the Mysql DB with SunPower raw data (reported up to their portal) read from a logfile.  Here is some example log lines for what should be contained in that file:\n\n\t130     20170108161000  414051636007015 AC_Module_Type_C                18.7783 0.0144  245.3928        0.1376  0.017   55.3412 0.3274  5.5     60.0006 0\n\t140     20170108171000  PVS5M508095c    PVS5M0400c      125     648.84  -0.1225 1.1217  1.4173  -0.0836 60.029  0')
parser.add_argument("-f","--file", help="Log filename",required=True)
args = parser.parse_args()
#fname = "/mnt/mydrive/logs/20170107.txt"
#fname = "/mnt/mydrive/logs/test.txt"
fname = args.file

try:
    cnx = mysql.connector.connect(user='solar', password='password', host='127.0.0.1', database='solar')
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    print "We are logged in!"
    add_raw_production_sql_130 = ("INSERT INTO sp_raw_production "
               "(message_type, src_timestamp, device_serial, device_description, watts, v1, v2, v3, v4, v5, v6, v7, v8, v9) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    add_raw_production_sql_140 = ("INSERT INTO sp_raw_production "
               "(message_type, src_timestamp, device_serial, device_description, v1, watts, v2, v3, v4, v5, v6, v7) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    with open(fname) as f:
        fileContent = f.read().splitlines()
    for x in fileContent:
        add_raw_production_sql = add_raw_production_sql_130
        cursor = cnx.cursor()
        fcursor = cnx.cursor()
        #example_data = "130     20170108161000  414051636007015 AC_Module_Type_C                18.7783 0.0144  245.3928        0.1376  0.017   55.3412 0.3274  5.5     60.0006 0"
        #example_data = "140     20170108171000  PVS5M508095c    PVS5M0400c      125     648.84  -0.1225 1.1217  1.4173  -0.0836 60.029  0"
        #insert_line = example_data.split()
        insert_line = x.split()
        if (len(insert_line) < 14):
            if (insert_line[0] == "140"):
                if (len(insert_line) < 12):
                    continue;
                elif (insert_line[3] == "PVS5M0400p"):
                    continue;
                else:
                    add_raw_production_sql = add_raw_production_sql_140
            else:
                print "line missing values, skipping... insert_line: ", insert_line
                continue
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

    print "Logging out of the DB!"
    cnx.commit()
    cursor.close()
    cnx.close()
