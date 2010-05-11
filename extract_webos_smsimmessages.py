#!/usr/bin/env python

# extract SMS, write to std out

import os, sys, time
import sqlite3

DBFILE="PalmDatabase.db3"

# open database with sqlite3
if os.path.exists(DBFILE):
    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()
else:
	print "No database"

classSent = 0;
classRcvd = 2;


# get all messages

currFrom = ()
recipDict = {}
nameDict = {}

for text, first, last, status, address, errorCode, timeStamp, smsClass, messageType in c.execute('''
    SELECT com_palm_pim_FolderEntry.messageText, 
           com_palm_pim_Recipient.firstName, 
           com_palm_pim_Recipient.lastName, 
           com_palm_pim_FolderEntry.status, 
           com_palm_pim_Recipient.address,
           com_palm_pim_Recipient.errorCode,
           com_palm_pim_FolderEntry.timeStamp,
           com_palm_pim_FolderEntry.smsClass,
           com_palm_pim_FolderEntry.messageType
    FROM com_palm_pim_FolderEntry 
    JOIN com_palm_pim_Recipient 
      ON (com_palm_pim_FolderEntry.id = com_palm_pim_Recipient.com_palm_pim_FolderEntry_id) 
    ORDER BY com_palm_pim_FolderEntry.timeStamp'''):
    # get rid of crap rows
    if (text == '' or status is None):
        continue

    # now state machine, iterate through

    # save each
    if not recipDict.has_key(address):
        # no entries create lists
        recipDict[address] = []
        nameDict[address] = []
  
    direction = "" 
    if not (messageType == "IM"):
        if (smsClass == classRcvd):
	    direction = "Received"
        else:
	    direction = "Sent"

    if messageType == "IM":
        errorCode = ""

    recipDict[address].append((text, timeStamp, direction, errorCode))
    
    if not (first is None and last is None):
        nameDict[address] = (first, last)


# now extract from dictionaries and print to stdout
for address, textList in recipDict.iteritems():
    if (nameDict[address]):
        print '%s %s: (%s)' % (nameDict[address][0], nameDict[address][1], address)

    for text, timeStamp, direction, errorCode in textList:
        secs = int(timeStamp)/1000
        print '  %s %s %s %s' % (time.strftime("%a %d %b %y %H:%M", 
                                         time.gmtime(secs)),
                           direction, errorCode, text)
    print