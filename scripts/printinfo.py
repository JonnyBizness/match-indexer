# printinfo.py

import json

from classes.match import Match 

#
# Match Information
#
## tbh no point in making the json into string here i should just use the object
def printMatchInfo(mID, mStart, p1, p2, mDuration, outputFormat):

    print('output format?', outputFormat)
    # Seems unnessesary for this to be an arg. for now, just variable i can decide on later.
    # for json it will be mute point.
    includeId = True
    outString = ""

    # Output in csv
    if outputFormat == "csv":
        delim = ","

        if includeId:
            mIDString = str(mID) + delim  # Show the match IDs (sequential no)
        else:
            mIDString = ''  # Don't show the match IDs
            outString = mIDString + mStart + delim + p1 + delim + p2 + delim + mDuration

    # Output in json
    # this actually going to be my main type eventually.
    if outputFormat == "json":
        match = Match(mID, mStart, p1, p2, mDuration)
        json_output = json.dumps(match.to_dict(), indent=4)
        outString = json_output

    # Output in plain text document
    if outputFormat == "txt":
        if includeId:
            mIDString = str(mID) + '. ' # Show the match IDs (sequential no)
        else:
            mIDString = ''  # Don't show the match IDs
            outString = mIDString + mStart + " - " + p1 + " vs " + p2 + " (" + mDuration + ")"

    # Just print to console or?
    ##TODO: check this so it is just console
    else:   
        if includeId:
            mIDString = str(mID) + '. ' # Show the match IDs (sequential no)
        else:
            mIDString = ''  # Don't show the match IDs
            outString = mIDString + mStart + " - " + p1 + " vs " + p2 + " (" + mDuration + ")"

    print('outstring?', outString)
    
    return outString


#
# Usage Information
#
def printUsageInfo(usageList, name_list):
    
    print('Character Appearance in Video')
    print('-----------------------------')

    usageSummary = []
    for useIndex, useTotal in enumerate(usageList):
        usageSummary.append([name_list[useIndex], useTotal])

    # Filter Usage Summary list (remove characters not used)
    usageFiltered = [i for i in usageSummary if i[1] > 0]

    # Sort Usage Summary list (most to least used)
    usageSorted = sorted(usageFiltered, key=lambda t: t[1], reverse=True)

    # Output character name and play count
    for u in usageSorted:
        print(u[0] + ':', u[1])


def writeOutput(outputContent, outputFormat):
    filename = f"output.{outputFormat}"

    builtOutputString = "{"

    if outputFormat == "json":
        builtOutputString += ''.join(f"{line}," for line in outputContent)
        builtOutputString += "}"

    else:
        builtOutputString = ''.join(outputContent)

    with open(filename, "w") as file:
        file.write(builtOutputString)