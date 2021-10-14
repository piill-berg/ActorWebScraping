import requests
from requests import sessions
import urllib.parse
from login import AAusername, AApassword

import re

from datetime import datetime

from bs4 import BeautifulSoup

from helpers import cleanString, countNestedListElements, getPageTitle

# A lot of the runtime data is gathered in the parsing process, which is why so much boiler-plate
# information is here and not in the main.

totalDateTime = str(datetime.now()) # datetime object which is split into two variables.
rawDigitsTime = totalDateTime[11:]
rawDigitsDate = totalDateTime[:10]
# print("rawDigitsDate: ",rawDigitsDate)
rawDate = rawDigitsDate[-2:]
# print(rawDigitsDate[-2:])


dataDict = {
    "ID" : None
    ,
    "date" : rawDigitsDate
    ,
    "time" : rawDigitsTime
    ,
    "forDate" : rawDate
    ,
    "isMaxCalls" : False # This can read up to 25 calls on ActorsAccess. Did we reach that?
    ,
    "matchedRoles" : 0
    ,
    "matchedCalls" : 0
}

REGIONURLS = {
    'LOS ANGELES' : '1',
    'CHICAGO' : '4',
    'South Central' : '7',
    'Southeast' : '9',
    'Pacific (Hawaii)' : '8',
    'Rocky Mountains' : '10',
    'Northwest' : '11',
    'Central Atlantic' : '12',
    'Atlantic Canada' : '13',
    'Alberta' : '14',
    'Canadian Praries' : '16',
    'Midwest' : '19',
    'New England' : '20',
    'North Central' : '21',
    'Northwest Territories' : '22',
    'Nunavut' : '23',
    'Quebec' : '24',
    'San Francisco / NorCal' : '25',
    'TORONTO' : '26',
    'VANCOUVER' : '27',
    'Yukon' : '28',
    'NEW YORK' : '32',
}
USERREGION = "NEW YORK"
USERRACE = ["white", "caucasian"]
USERAGE = range(17,26)
# print(USERAGE)
USERGENDER = ["male","man"]
USERVARS = [USERRACE,USERGENDER,USERAGE]

REGIONNUM = REGIONURLS[USERREGION]

ROOTURL = "https://actorsaccess.com"

def AACallIsToday(callPage, globalDay):
    # print("Checking whether a call was today...")
    soup = BeautifulSoup(callPage.text, 'html.parser')
    # print(soup.title)

    callInfo = str(soup.td)
    # print("\ncallInfo:\n","<>"*30,"\n",callInfo + "\n","<>"*30,"\n")
    index = callInfo.find('>') + 1
    char = callInfo[index:index + 2]
    char = char.lower()

    # print("character is: " + char)

    if char == globalDay:
        return True
    else:
        return False

"""
The inList is matchedDescs, which can be found in parseActorsAccess.

The function itself returns data about the number of roles/calls matched for the data file.
"""
from reader import descUserMatched

def readAACall(href,inList,userSession):
    # Gets the URL, then checks for session timeout and if so retries.
    typeBools = (type(href) == str, type(inList) == list, type(userSession) == sessions.Session)
    if not all(typeBools):
        print(typeBools)
        raise TypeError("Usage Types: readAACall(string, list, sessions.Session)")

    # print("inList :", inList)

    desiredUrl = ROOTURL + href
    session = userSession
    s = session.get(desiredUrl)
    title = getPageTitle(s)
    # print(title)
    if 'login' in title:
        while True:
            print('Redirected to Login Page, retrying...')
            s = session.get(desiredUrl)
            if 'login' not in title:
                break
    soup = BeautifulSoup(s.text, 'html.parser')
    # print(soup.title)
    # print("<>" * 30)

    rawCall = ""
    for td in soup.select('td'):
        # print(td.attrs)    
        if not td.attrs:
            rawCall = td
    # print(rawCall)
    rawCall = str(rawCall)
    descs = []
    names = []
    # break

    rawCallSoup = BeautifulSoup(rawCall, 'html.parser')
    # print(rawCallSoup)
    # print(rawCallSoup.text)

    nameRegex = re.compile("\[\s?(.+?)\s?\]")
    text = str(rawCallSoup.text)

    nameIter = re.finditer(nameRegex,text)
    nameMatchObjects = []
    for iterObject in nameIter:
        nameMatchObjects.append(iterObject)        
    for i,matchObject in enumerate(nameMatchObjects):
        # print(matchObject)
        names.append(matchObject.group(1))
        desc = ""
        if i == len(nameMatchObjects)-1:
            desc = text[matchObject.end():]
        else:
            endIndex = text.find("[",matchObject.end())
            # print(endIndex)
            desc = text[matchObject.end():endIndex]
        descs.append(desc)

    # print(descs)
    # print("<>" * 30)
    # print(names)
    # print("<>" * 30)


    if len(names) != len(descs):
        big = 'descriptions'
        small = 'names'
        if len(names) > len(descs):
            big = 'names'
            small = 'descriptions'
        raise ValueError("Found more {} than {}.".format(big,small))


    # Variables for data appendage to csv
    matchedCalls = len(inList)
    currentRoles = int((countNestedListElements(inList) - matchedCalls) / 2)
 
    matchedDescsOnCall = []
    for i,d in enumerate(descs):
        # print("description: ",d,"\nname: ",names[i])
        descName = names[i]
        readableDesc = descName + " " + d # Each description includes the name
        readableDesc = cleanString(readableDesc)
        if d == "":
            d = "No description found."
        # print("description on-call number: ", i+1)
        # print("text:\n", d)
        if descUserMatched(USERVARS,readableDesc):
            currentRoles += 1
            # print("currentRoles :", currentRoles)
            matchedDescsOnCall.append([descName,d])
            print("role matched for user ({})".format(currentRoles))
    if len(matchedDescsOnCall) > 0:
        matchedCalls += 1
        # print("call matched for user ({})".format(len(inList)+1))
        matchedDescsOnCall.append(href)
        inList.append(matchedDescsOnCall)
    # print("finished reading a call")

    newRolesAmount = currentRoles
    newMatchedCallsAmount = matchedCalls
    # print(descs)
    # print("<>" * 30)
    # print(names)
    # print("<>" * 30)
    return (newRolesAmount,newMatchedCallsAmount)
# print(readAACall("/projects/?view=breakdowns&breakdown=718453&region=32",[],requests.Session()))
# print(readAACall('/projects/index.cfm?view=breakdowns&breakdown=720452&region=32',[],requests.Session()))
# print("final:\n",readAACall('/projects/?view=breakdowns&breakdown=720768&region=32',[],requests.Session()))

def parseActorsAccess(currentDate):

    dataDict["forDate"] = currentDate

    session = requests.Session()
    print("logging in...")
    # Log in and navigate to the calls page
    login = {'username' : AAusername, 'password' : AApassword}
    s = session.post('https://actorsaccess.com/index.cfm?login&loginSecure', data = login)
    s = session.get('https://actorsaccess.com/projects/index.cfm?region={}'.format(urllib.parse.quote_plus(REGIONNUM)))

    soup = BeautifulSoup(s.text, 'html.parser')
    callrows = soup.select('.element')

    # print(len(callrows))
    callHrefs = []

    for row in callrows:
        regex = re.compile('">\d\d/(\d\d)/\d\d')
        rowDate = re.search(regex, str(row))
        rowDate = rowDate.group(1)
        # print(rowDate, rawDate)
        if rowDate == str(currentDate):
            hrefReg = re.compile('href="(.*)"')
            rowHref = re.search(hrefReg,str(row))
            rowHref = rowHref.group(1)
            rowHref = cleanString(rowHref)
            # print(rowHref)
            callHrefs.append(rowHref)
    # print(len(callHrefs))
      
    for i,href in enumerate(callHrefs):
        gobacks = (len('region=' + REGIONNUM))
        callHrefs[i] = href[:-gobacks] + '&' + href[-gobacks:]    
    # print("callHrefs: ", callHrefs)

    matchedDescs = []
    if len(callHrefs) == 0:
        print("No calls posted today!")
        return 2
    elif len(callHrefs) == 25:
        print("max number of calls reached, possible misses...")
        dataDict["isMaxCalls"] = True
    print("reading calls...")
    for href in callHrefs:
        # print(href)
        dataDictTuple = readAACall(href,matchedDescs,session)
        dataDict["matchedRoles"] = dataDictTuple[0]
        dataDict["matchedCalls"] = dataDictTuple[1]
    # print(matchedDescs)
    return matchedDescs

def readBackstageCall():
    pass

def parseBackstage():
    pass