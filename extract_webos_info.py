#!/usr/bin/env python

import os, sys, time, codecs
import sqlite3
import datetime
import optparse

# defines
prog_version="%prog 0.2"

def dumpmessages(c,type,printHeader):
    """Dump messages in PalmDatabase.db3 file - types: txt, im"""
    classSent = 0;
    classRcvd = 2;

    currFrom = ()
    recipDict = {}
    nameDict = {}

    if (type == "sms"):
        msgType = "SMS"
        print("got sms")
    elif (type == "mms"):
        msgType = "MMS"
        print("got mms")
    elif (type == "im"):
        msgType = "IM"
    where = (msgType,)
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
        LEFT OUTER JOIN com_palm_pim_Recipient 
          ON (com_palm_pim_FolderEntry.id = com_palm_pim_Recipient.com_palm_pim_FolderEntry_id)
        WHERE messageType = ? 
        ORDER BY com_palm_pim_FolderEntry.timeStamp''', where):
        # get rid of bad rows
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

        # fix im directions based on errorCode
        if messageType.lower() == "im":
            if (errorCode == "Pending"):
                direction = "Received"
            else:
                direction = "Sent"
            errorCode = ""

        recipDict[address].append((text, timeStamp, direction, errorCode, messageType, uniqueAttachmentFolderName))
    
        if not (first is None and last is None):
            nameDict[address] = (first, last)
            #print address,first,last,timeStamp,direction,errorCode,text

    # now extract from dictionaries and print to stdout
    for address, textList in recipDict.iteritems():

        if (nameDict[address]):
            print('{0} {1} ({2}):'.format(nameDict[address][0], nameDict[address][1], address))
        else:
            print('- - ({0}):'.format(address))

        if (printHeader):
            if (messageType.lower() == "mms"):
                print ('  {0:20} {1:9} {2:9} {3:11} {4:10} {5}'.format("Date/Time","Direction","ErrorCode","MessageType","Text","AttachmentPath"))
            else:
                print ('  {0:20} {1:9} {2:9} {3:11} {4:10}'.format("Date/Time","Direction","ErrorCode","MessageType","Text"))
        
        for text, timeStamp, direction, errorCode, messageType, uniqueAttachmentFolderName in textList:
            secs = int(timeStamp)/1000
            if (direction.lower() == "received" and errorCode.lower() == "pending"):
                errorCode=""
            
            if (messageType.lower() == "mms"):
                print ('  {0:20} {1:9} {2:9} {3:11} {4:10} {5}'.format(time.strftime("%a %d %b %y %H:%M", 
                                                 time.gmtime(secs)),
                                   direction, errorCode, messageType, text, uniqueAttachmentFolderName))
            else:    
                print('  {0:20} {1:9} {2:9} {3:11} {4:10}'.format(time.strftime("%a %d %b %y %H:%M", 
                                                 time.gmtime(secs)),
                                   direction, errorCode, messageType, text))
        
        print
    
def dumpentries(c,header):
    """Dumps phonebook entries from a PalmDatabase.db3"""
    
    # first get list of numbers
    numList = {}
    get_num_stmt = '''SELECT com_palm_superlog_Superlog.number,
                             com_palm_pim_Person.firstName,
                             com_palm_pim_Person.lastName
                      FROM com_palm_superlog_Superlog
                      LEFT OUTER JOIN com_palm_pim_Person ON (com_palm_superlog_Superlog.contactId = com_palm_pim_Person.id)
                      '''
    c.execute(get_num_stmt)
    for row in c:
        # create list of numbers to get detail on
        (phNumber,firstName,lastName) = row
        if not numList.has_key(phNumber):
            if not (firstName is None and lastName is None): 
                numList[phNumber] = [firstName, lastName]
            else:
                numList[phNumber] = ['Unknown', '']
    
    detail_stmt = '''SELECT com_palm_superlog_Superlog.displayName,
                     com_palm_superlog_Superlog.type,
                     com_palm_superlog_Superlog.startTime,
                     com_palm_superlog_Superlog.duration
              FROM com_palm_superlog_Superlog
              WHERE number = ?
              ORDER BY startTime'''
    
    for number, name_info in numList.iteritems():
        (firstName,lastName) = name_info
        print("{0} {1} ({2:10}):".format(firstName, lastName, number))
        if header:
            print("    {0:10} {1:15} {2}".format("Calltype","Date/Time","Duration (hms)"))
        c.execute(detail_stmt, (number,))
        for row in c:
            (displayName,callType,startTime,callDuration) = row
            calldateTime = time.strftime("%m/%d/%y %H:%M",time.localtime(int(startTime)/1000))
            calldurationHMS = str(datetime.timedelta(seconds=int(callDuration)/1000))
            print("    {0:10} {1:15} {2}".format(callType,calldateTime,calldurationHMS))
            
    

# parse options    
usage = "usage: %prog [options] dbfile.db3"
parser = optparse.OptionParser(usage, version=prog_version)
parser.add_option("-s","--sms",action="store_true", dest="getsms",help="Get all SMS messages from db")
parser.add_option("-m","--mms",action="store_true", dest="getmms",help="Get all MMS messages from db")
parser.add_option("-i","--im",action="store_true", dest="getim", help="Get all IM messages from db")
parser.add_option("-p","--phone",action="store_true", dest="getph", help="Get the call log from db")
parser.add_option("-d","--header",action="store_true", dest="header", help="Print header to describe output")

(options, args) = parser.parse_args()
if len(args) != 1:
    parser.error("Incorrect number of arguments, expected 1\ttry --help")

DBFILE = args[0]

# open database with sqlite3
if os.path.exists(DBFILE):
    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()
else:
	print "ERROR: Database file %s doesn't exist" % DBFILE
	sys.exit(1)

#wrap for UTF-8 characters
sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

if (options.getsms):
    dumpmessages(c,"sms",options.header)

if (options.getmms):
    dumpmessages(c,"mms",options.header)

if (options.getim):
    dumpmessages(c,"im",options.header)

if (options.getph):
    dumpentries(c,options.header)

print("Done")

#cleanup cursor
c.close()