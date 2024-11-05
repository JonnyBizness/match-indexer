# printinfo.py


#
# Match Information
#
def printMatchInfo(args, mID, mStart, p1, p2, mDuration):

    # Output in csv
    if args.c:
        delim = ","

        if args.n:
            mIDString = str(mID) + delim  # Show the match IDs (sequential no)
        else:
            mIDString = ''  # Don't show the match IDs

        outString = mIDString + mStart + delim + p1 + delim + p2 + delim + mDuration

    # Output in plain text
    else:
        if args.n:
            mIDString = str(mID) + '. ' # Show the match IDs (sequential no)
        else:
            mIDString = ''  # Don't show the match IDs

        outString = mIDString + mStart + " - " + p1 + " vs " + p2 + " (" + mDuration + ")"

    print(outString)


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
