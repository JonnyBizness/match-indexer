# -*- coding: utf-8 -*-
import datetime
import glob
import os
import math
import time
import argparse
import importlib
import numpy as np
import cv2
import pygetwindow
import dxcam

from scripts.util import scaleDimension, drawLabel
from scripts.arguments import setupArguements, processArguments
from scripts.printinfo import printMatchInfo, printUsageInfo, writeOutput
from scripts.windowsizing import getWindowRegionInfo
from scripts.getstartggdata import getEventInfo

from classes.settings import Settings
from classes.match import Match

# do something with this later
# duplicated in utils. stupid.
colorBlue = (255, 0, 0)
colorRed = (0, 0, 255)
colorCyan = (255, 255, 0)
fontFace = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.7
fontColor = (255, 255, 255)
fontThickness = 2
borderThickness = 4
textPadding = 2


# Start the time... now!
timeStart = datetime.datetime.now().replace(microsecond=0)
# List of strings, joined in the end.




args = setupArguements()
settings = processArguments(args)

## move these into settings? and process args? and onl if the -w is there?
#application_region, applicationWidth, applicationHeight = getWindowRegionInfo(args.window)
#print('region?:', application_region)
#applicationResolution = (applicationWidth, applicationHeight)


### really these are more settings that could be put into a model but...i'll wait.
# Initialise ROI variables from layout file
templateScale = settings.layoutFile.layout['scale']
roiP1 = settings.layoutFile.layout['originPlayer1']
roiP2 = settings.layoutFile.layout['originPlayer2']
roiPw = settings.layoutFile.layout['widthPortrait']
roiPh = settings.layoutFile.layout['heightPortrait']

#score regions
#rename this shit
roip1Score = settings.layoutFile.layout['originScorep1']
roip2Score = settings.layoutFile.layout['originScorep2']
roiScoreWidth = settings.layoutFile.layout['widthScore']
roiScoreHeight = settings.layoutFile.layout['heightScore']


if "threshold" in settings.layoutFile.layout: 
    threshold = settings.layoutFile.layout['threshold']
else:
    threshold = 0.9 # Default
print("Detection Threshold: {0}".format(threshold))
scoreThreshold = 0.8


if settings.debug:
    print("original roiP1:", settings.layoutFile.layout['originPlayer1'])
    print("scaled roiP1:", roiP1)
    print("original roiP2:", settings.layoutFile.layout['originPlayer2'])
    print("scaled roiP2:", roiP2)


# No. of frames to skip: speeds up analysis
frameSkip = 30

# No. of seconds before we consider detection lost
detectThresholdSec = 6


#
# Process arguments
#
# Check filename
videoFile = args.filename
###############################################################################




# No. of frames to skip: speeds up analysis
frameSkip = 30

# No. of seconds before we consider detection lost
detectThresholdSec = 10

# Video input
cap = cv2.VideoCapture(videoFile)

# Determine frames per second of video
fps = cap.get(cv2.CAP_PROP_FPS)

# (OBS Hack) Incorrectly reports 62.5 fps
if fps == 62.5:
    fps = 60

# Get other video properties
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
totalFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

print('Video: {0}' . format(videoFile))
print('Frame width: {0:.0f}' . format(width))
print('Frame height: {0:.0f}' . format(height))
print('Frame rate: {0:.2f} fps' . format(fps))
print('Length: {0}' . format(
    time.strftime("%H:%M:%S", time.gmtime(totalFrames / fps))))
print('--')

# No. of Frames before we lose detection
detectThreshold = detectThresholdSec * fps

# Empty list to store template images
template_list1 = []
template_list2 = []
score_template_list = []
name_list = []
usage_list = []
nameIndex1 = 0
nameIndex2 = 0

##JB TODO:
# replace this with setting
# only look for this number, if found, that's end of match.
gameCount = 3

# Make a list of all Player 1 and 2 template images from a directory
p1Charfiles = glob.glob(settings.templatePath + '*-1p.jpg')
p2Charfiles = glob.glob(settings.templatePath + '*-2p.jpg')
#scoreFiles = glob.glob('.\scores\*.png')
score_folder = 'scores'
scoreFiles = sorted(os.listdir(score_folder), key=lambda x: int(os.path.splitext(x)[0]))

# Prepare the Player 1 and 2 templates
for file in p1Charfiles:
    image = cv2.imread(file, 0)
    # Resize
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    template_list1.append(resImage)

    # aditional function build list
    charaName = os.path.basename(file).replace('-1p.jpg', '').title()
    name_list.append(charaName)  # Build the character name list
    usage_list.append(0)  # Initialise usage values to 0

for file in p2Charfiles:
    image = cv2.imread(file, 0)
    # Resize
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    template_list2.append(resImage)

# prepare the score template? idk...
# for file in scoreFiles:
#     image = cv2.imread(file, 0)
#     resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
#     score_template_list.append(resImage)
for file in scoreFiles:
    file_path = os.path.join(score_folder, file)
    image = cv2.imread(file_path, 0)
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    score_template_list.append(resImage)


# Init variables
scoreDetected = False
p1ScoreDetected = False
p2ScoreDetected = False

frameCount = 0
character1Detected = False
character2Detected = False
thresholdCount1 = 0
thresholdCount2 = 0

matchCount = 0 #my way of determining using score
firstPass = True


# Text label properties
fontFace = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.7
fontColor = (255, 255, 255)
fontThickness = 2
borderThickness = 1
textPadding = 2
colorBlue = (255, 0, 0)
colorRed = (0, 0, 255)
colorCyan = (255, 255, 0)
colorFill = -1



###
###
# Time to get event info
###
###

# plan is to get the event info from startgg.
# make it in some format like:

# sets [
#     {
#         "set-name": 'winners final'
#         "total-matches": 3
#         "players": [
#             {
#                 "name": 'Kauliflower'
#                 "characters": ['Zangief']
#             },
#             {
#                 "name": 'Yami_Mahou'
#                 "characters": ['Ken']
#             }
#         ]
#     },
#     {
#         "set-name": 'losers semi'
#         "total-matches": 4
#         "players": [
#             {
#                 "name": 'AlistairBL'
#                 "characters": ['Cammy']
#             },
#             {
#                 "name": 'LunaFrost'
#                 "characters": ['Akuma', 'Blanka']
#             }
#         ]
#     }

# ]


## and then while going through the matches in the video, try marry them to a match in the above array.




#eventInfo = getEventInfo(1234)
#print('eventInfo', eventInfo)







###



print('settings.debug:', settings.debug)

## store the matches
matches = []
currentMatch = Match()

###
###
# Start capture
###
###
while cap.isOpened():
    ret, frame = cap.read()

    if ret:
        frameCount += 1

        # Let's only check every few frames as defined by frameCount
        if frameSkip > 0 and frameCount % frameSkip != 0:
            continue

        #
        # Determine ROI(region of interest) images for detection
        #
        # p1 char name
        img1_roi = frame[roiP1[1]:roiP1[1] + roiPh, roiP1[0]:roiP1[0] + roiPw]
        img1_gray = cv2.cvtColor(img1_roi, cv2.COLOR_BGR2GRAY)
        # p2 char name
        img2_roi = frame[roiP2[1]:roiP2[1] + roiPh, roiP2[0]:roiP2[0] + roiPw]
        img2_gray = cv2.cvtColor(img2_roi, cv2.COLOR_BGR2GRAY)
        # p1 score
        p1imgScore_roi = frame[roip1Score[1]:roip1Score[1] + roiScoreHeight, roip1Score[0]:roip1Score[0] + roiScoreWidth]
        p1imgScore_gray = cv2.cvtColor(p1imgScore_roi, cv2.COLOR_BGR2GRAY)
        # p2 score
        p2imgScore_roi = frame[roip2Score[1]:roip2Score[1] + roiScoreHeight, roip2Score[0]:roip2Score[0] + roiScoreWidth]
        p2imgScore_gray = cv2.cvtColor(p2imgScore_roi, cv2.COLOR_BGR2GRAY)

        # Draw ROIs
        if settings.previewVideo:
            cv2.rectangle(frame, roiP1, (roiP1[0] + roiPw, roiP1[1] + roiPh), colorCyan, borderThickness)
            cv2.rectangle(frame, roiP2, (roiP2[0] + roiPw, roiP2[1] + roiPh), colorCyan,borderThickness)
            cv2.rectangle(frame, roip1Score, (roip1Score[0] + roiScoreWidth, roip1Score[1] + roiScoreHeight), colorCyan, borderThickness)
            cv2.rectangle(frame, roip2Score, (roip2Score[0] + roiScoreWidth, roip2Score[1] + roiScoreHeight), colorCyan, borderThickness)
            #cv2.rectangle(frame, roiScore, (roiScore[0] + roiScoreWidth, roiScore[1] + roiScoreHeight), colorCyan, borderThickness)

        #
        ## If people are quick we might detect an 0-1 or 0-2, but we only care that match ends when it's x-3 or 3-x 
        ## Get my syntax right. match is the overal. each score is a game. i'm currently determining a game end. not a match!
        #

        ### first look for scores
        if not scoreDetected:
            #### p1 ####
            p1ScoreFound = None
            p1BestMatchValue = 0
            for scoreIndex, scoreTemplate in enumerate(score_template_list):
                p1Match = cv2.matchTemplate(p1imgScore_gray, score_template_list[scoreIndex], cv2.TM_CCOEFF_NORMED)
                maxP1MatchValue = np.max(p1Match)
                if maxP1MatchValue >= scoreThreshold and maxP1MatchValue > p1BestMatchValue:
                    p1ScoreFound = str(scoreIndex)
                    p1BestMatchValue = maxP1MatchValue

            #### p2 ####
            p2ScoreFound = None
            p2BestMatchValue = 0
            for scoreIndex, scoreTemplate in enumerate(score_template_list):
                p2Match = cv2.matchTemplate(p2imgScore_gray, score_template_list[scoreIndex], cv2.TM_CCOEFF_NORMED)
                maxP2MatchValue = np.max(p2Match)
                if maxP2MatchValue >= scoreThreshold and maxP2MatchValue > p2BestMatchValue:
                    p2ScoreFound = str(scoreIndex)
                    p2BestMatchValue = maxP2MatchValue


            #### both scores ####
            if(p1ScoreFound is not None and p2ScoreFound is not None):
                # Detected successfully
                scoreDetected = True
                #scoreGameCount +=1 #if needed....

                # END OF CURRENT MATCH.
                if (int(p1ScoreFound) == 3 or int(p2ScoreFound) == 3):
                    print('Match Ended')
                    print('# (Match no:' + str(matchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)), 'score: ' + str(p1ScoreFound) + ' - ' + str(p2ScoreFound))
                    
                    matchEnd = frameCount / fps - detectThresholdSec
                    matchDuration = time.strftime("%H:%M:%S", time.gmtime(matchEnd - matchStart))
                    
                    # apend match to matches before kicking off new match
                    # match = Match(matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration, p1ScoreFound, p2ScoreFound)
                    #matches.append(match)

                    #update current match details
                    currentMatch.mID = matchCount
                    currentMatch.mStart = matchStartText
                    currentMatch.mDuration = matchDuration
                    currentMatch.p1Score = p1ScoreFound
                    currentMatch.p2Score = p2ScoreFound
                    
                    # apend currentMatch to list of matches
                    matches.append(currentMatch)
                    
                    ## reset for next match
                    # increase match count
                    matchCount += 1
                    # try use match start from characters?
                    firstPass = True
                    # feels like i shouldn't have to reset these but it should delay the new match started til it detects?
                    character1Detected = False
                    character2Detected = False

                if settings.debug:
                    print('Start of detecting Scores - for match:', matchCount)
                    print('P1! score found:', p1ScoreFound, ' - ', p1BestMatchValue)
                    print('P2! score found:', p2ScoreFound, ' - ', p2BestMatchValue)
                    #print('### (score no: ' + str(matchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
        else:
            ### look for the score detection to drop before looking for scores again.
            p1BestMatchValue = 0
            p2BestMatchValue = 0
            p1Match = cv2.matchTemplate(p1imgScore_gray, score_template_list[int(p1ScoreFound)], cv2.TM_CCOEFF_NORMED)
            p2Match = cv2.matchTemplate(p2imgScore_gray, score_template_list[int(p1ScoreFound)], cv2.TM_CCOEFF_NORMED)
            maxP1MatchValue = np.max(p1Match)
            if maxP1MatchValue <= (scoreThreshold - 0.5): #slightly lower threshold
                p1ScoreFound = None
            maxP2MatchValue = np.max(p2Match)
            if maxP2MatchValue <= (scoreThreshold - 0.5):
                p2ScoreFound = None
             #### both scores disapeared ####
            if(p1ScoreFound is None and p2ScoreFound is None):
                scoreDetected = False
                if settings.debug:
                    print('End of detecting Scores - new game must be starting')
                    # print('### (score no: ' + str(matchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))



        

        #
        # Player 1 Check
        #
        if not character1Detected:
            # For all images in template, look for match - this is first look for character
            for templateIndex1, template1 in enumerate(template_list1):
                w1, h1 = template1.shape[::-1]
                res1 = cv2.matchTemplate(img1_gray, template1, cv2.TM_CCOEFF_NORMED)
                loc1 = np.where(res1 >= threshold)

                if len(loc1[0]):
                    thresholdCount1 = 0
                    character1Detected = True
                    nameIndex1 = templateIndex1
                    if settings.debug:
                        print('### P1', name_list[nameIndex1], '(template no: ' + str(nameIndex1) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break   
        else:
            # previously matched on a character, keep looking for that character until it disapears.
            w1, h1 = template_list1[nameIndex1].shape[::-1]
            res1 = cv2.matchTemplate(img1_gray, template_list1[nameIndex1], cv2.TM_CCOEFF_NORMED)
            loc1 = np.where(res1 >= threshold)

            if len(loc1[0]):    
                thresholdCount1 = 0
                textName1 = name_list[nameIndex1]

                # if not already mentioned. add to match.
                if textName1 not in currentMatch.p1Characters:
                    print('appending ' + textName1)
                    currentMatch.p1Characters.append(textName1)


                if settings.previewVideo:
                    for pt1 in zip(*loc1[::-1]):
                        detOrigin = (roiP1[0] + pt1[0], roiP1[1] + pt1[1])
                        detSize = (w1, h1)
                        cv2.rectangle(frame, detOrigin, tuple(np.add(detOrigin, detSize)), colorRed, borderThickness)
                        drawLabel(textName1, frame, detOrigin, colorRed)

            # No longer detecting character
            else:
                if thresholdCount1 > detectThreshold:
                    character1Detected = False
                else:
                    thresholdCount1 += 1 + frameSkip

            

        #
        # Player 2 Check
        #
        if not character2Detected:
            # For all images in template, look for match - this is first look for character
            for templateIndex2, template2 in enumerate(template_list2):
                w2, h2 = template2.shape[::-1]
                res2 = cv2.matchTemplate(img2_gray, template2, cv2.TM_CCOEFF_NORMED)
                loc2 = np.where(res2 >= threshold)

                if len(loc2[0]):                    
                    thresholdCount2 = 0
                    character2Detected = True
                    nameIndex2 = templateIndex2
                    if settings.debug:
                        print('### P2', name_list[nameIndex2], '(template no: ' + str(nameIndex2) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break
        else:
            # previously matched on a character, keep looking for that character until it disapears.
            w2, h2 = template_list2[nameIndex2].shape[::-1]
            res2 = cv2.matchTemplate(img2_gray, template_list2[nameIndex2], cv2.TM_CCOEFF_NORMED)
            loc2 = np.where(res2 >= threshold)

            if len(loc2[0]):
                thresholdCount2 = 0
                textName2 = name_list[nameIndex2]

                if textName2 not in currentMatch.p2Characters:
                    print('appending ' + textName2)
                    currentMatch.p2Characters.append(textName2)

                if settings.previewVideo:
                    for pt2 in zip(*loc2[::-1]):
                        detOrigin = (roiP2[0] + pt2[0], roiP2[1] + pt2[1])
                        detSize = (w2, h2)
                        cv2.rectangle(frame, detOrigin, tuple(np.add(detOrigin, detSize)), colorBlue, borderThickness)
                        drawLabel(textName2, frame, detOrigin, colorBlue)

            # No longer detecting character
            else:
                if thresholdCount2 > detectThreshold:
                    character2Detected = False
                else:
                    thresholdCount2 += 1 + frameSkip

            

        #
        # Are we detecting a match for the first time?
        # this is wrong because assumes single character per person.
        #
        if character1Detected and character2Detected and firstPass:
            print('NEW MATCH STARTED')

            # new match starting so reset current match
            currentMatch = Match()


            firstPass = False
            previouslyDetected = True
            matchStart = frameCount / fps
            matchStartText = format(datetime.timedelta(seconds=math.trunc(matchStart)))

        #     matchEnd = frameCount / fps - detectThresholdSec
        #     matchEndText = format(datetime.timedelta(seconds=matchEnd))
        #     matchDuration = time.strftime("%H:%M:%S", time.gmtime(matchEnd - matchStart))
        #     usage_list[nameIndex1] += 1  # Increment character usage (P1)
        #     usage_list[nameIndex2] += 1  # Increment character usage (P2)

        # Preview video during processsing, if enabled
        if settings.previewVideo:
            # cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('frame', int(width/2), int(height/2))
            cv2.imshow('frame', frame)
            if cv2.waitKey(11) & 0xFF == ord('q'):
                break

    else:
        print('End of video')
        break

cap.release()
cv2.destroyAllWindows()
timeEnd = datetime.datetime.now().replace(microsecond=0)
print('--')
print('Total matches:', matchCount)
print('Processing Time started:', timeStart)
print('Processing Time ended:', timeEnd)
print('Processing Time taken:', (timeEnd - timeStart))
print('')
printUsageInfo(usage_list, name_list)
writeOutput(matches, settings.outputFormat)