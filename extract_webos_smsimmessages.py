#!/usr/bin/env python

# extract SMS, write to std out

import os, sys, time, codecs
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

#wrap for UTF-8 characters
sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

for text, first, last, status, address, errorCode, timeStamp, smsClass, messageType, uniqueAttachmentFolderName in c.execute('''
    SELECT com_palm_pim_FolderEntry.messageText, 
           com_palm_pim_Recipient.firstName, 
           com_palm_pim_Recipient.lastName, 
           com_palm_pim_FolderEntry.status, 
           com_palm_pim_Recipient.address,
           com_palm_pim_Recipient.errorCode,
           com_palm_pim_FolderEntry.timeStamp,
           com_palm_pim_FolderEntry.smsClass,
           com_palm_pim_FolderEntry.messageType,
           com_palm_pim_FolderEntry.uniqueAttachmentFolderName
    FROM com_palm_pim_FolderEntry 
    JOIN com_palm_pim_Recipient 
      ON (com_palm_pim_FolderEntry.id = com_palm_pim_Recipient.com_palm_pim_FolderEntry_id) 
    ORDER BY com_palm_pim_FolderEntry.timeStamp'''):
    # get rid of crap rows
    if (status is None):
        continue

    # now state machine, iterate through

    # save each
    if not recipDict.has_key(address):
        # no entries create lists
        recipDict[address] = []
        nameDict[address] = []
  
    direction = "" 
    if not (messageType.lower()) == "im":
        if (smsClass == classRcvd):
	    direction = "Received"
        else:
	    direction = "Sent"

    if messageType.lower() == "im":
        errorCode = ""

    recipDict[address].append((text, timeStamp, direction, errorCode, messageType, uniqueAttachmentFolderName))
    
    if not (first is None and last is None):
        nameDict[address] = (first, last)
        #print address,first,last,timeStamp,direction,errorCode,text

# now extract from dictionaries and print to stdout
for address, textList in recipDict.iteritems():

    if (nameDict[address]):
        print '%s %s: (%s)' % (nameDict[address][0], nameDict[address][1], address)

    for text, timeStamp, direction, errorCode, messageType, uniqueAttachmentFolderName in textList:
        secs = int(timeStamp)/1000
        if (direction.lower() == "received" and errorCode.lower() == "pending"):
            errorCode=""
            
        if (messageType.lower() == "mms"):
            print '  %s %s %s %s %s %s' % (time.strftime("%a %d %b %y %H:%M", 
                                             time.gmtime(secs)),
                               direction, errorCode, messageType, text, uniqueAttachmentFolderName)
        else:    
            print '  %s %s %s %s %s' % (time.strftime("%a %d %b %y %H:%M", 
                                             time.gmtime(secs)),
                               direction, errorCode, messageType, text)
        
    print
