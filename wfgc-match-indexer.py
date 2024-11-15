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
matches = []



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
previouslyDetected = False
matchCount = 0 #original way using characters disapearing?
scoreMatchCount = 0 #my way of determining using score
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
                # Get the maximum value of the match for each region
                maxP1MatchValue = np.max(p1Match)

                # Update p1ScoreFound if a higher-confidence match is found
                if maxP1MatchValue >= scoreThreshold and maxP1MatchValue > p1BestMatchValue:
                    p1ScoreFound = str(scoreIndex)
                    p1BestMatchValue = maxP1MatchValue
            
            #### p2 ####
            p2ScoreFound = None
            p2BestMatchValue = 0
            for scoreIndex, scoreTemplate in enumerate(score_template_list):
                
                p2Match = cv2.matchTemplate(p2imgScore_gray, score_template_list[scoreIndex], cv2.TM_CCOEFF_NORMED)
                # Get the maximum value of the match for each region
                maxP2MatchValue = np.max(p2Match)

                # Update p2ScoreFound if a higher-confidence match is found
                if maxP2MatchValue >= scoreThreshold and maxP2MatchValue > p2BestMatchValue:
                    p2ScoreFound = str(scoreIndex)
                    p2BestMatchValue = maxP2MatchValue


            #### both scores ####
            if(p1ScoreFound is not None and p2ScoreFound is not None):
                # Detected successfully
                scoreDetected = True
                #scoreGameCount +=1 #if needed....

                if (int(p1ScoreFound) == 3 or int(p2ScoreFound) == 3):
                    scoreMatchCount += 1
                    print('Match Ended')
                    print('# (Match no:' + str(scoreMatchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)), 'score: ' + str(p1ScoreFound) + ' - ' + str(p2ScoreFound))

                if settings.debug:
                    print('Start of detecting Scores - for match:', scoreMatchCount)
                    print('P1! score found:', p1ScoreFound, ' - ', p1BestMatchValue)
                    print('P2! score found:', p2ScoreFound, ' - ', p2BestMatchValue)
                    #print('### (score no: ' + str(scoreMatchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
        else:
            ### now looking for the scores to disapear - to confirm what the score was?

            #### p1 ####
            p1ScoreFound = None
            p1BestMatchValue = 0
            for scoreIndex, scoreTemplate in enumerate(score_template_list):
                
                p1Match = cv2.matchTemplate(p1imgScore_gray, score_template_list[scoreIndex], cv2.TM_CCOEFF_NORMED)
                # Get the maximum value of the match for each region
                maxP1MatchValue = np.max(p1Match)

                # Update p1ScoreFound if a higher-confidence match is found
                if maxP1MatchValue >= scoreThreshold and maxP1MatchValue > p1BestMatchValue:
                    p1ScoreFound = str(scoreIndex)
                    p1BestMatchValue = maxP1MatchValue
            
            #### p2 ####
            p2ScoreFound = None
            p2BestMatchValue = 0
            for scoreIndex, scoreTemplate in enumerate(score_template_list):
                
                p2Match = cv2.matchTemplate(p2imgScore_gray, score_template_list[scoreIndex], cv2.TM_CCOEFF_NORMED)
                # Get the maximum value of the match for each region
                maxP2MatchValue = np.max(p2Match)

                # Update p2ScoreFound if a higher-confidence match is found
                if maxP2MatchValue >= scoreThreshold and maxP2MatchValue > p2BestMatchValue:
                    p2ScoreFound = str(scoreIndex)
                    p2BestMatchValue = maxP2MatchValue
            
             #### both scores ####
            if(p1ScoreFound is None and p2ScoreFound is None):
                scoreDetected = False
                if settings.debug:
                    print('End of detecting Scores - new game must be starting')
                    # print('### (score no: ' + str(scoreMatchCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))



        

        #
        # Player 1 Check
        #
        # if 'match' detected, keep looking for it til it disapears
        if character1Detected:

            # Keep monitoring the previously matched template
            w1, h1 = template_list1[nameIndex1].shape[::-1]
            res1 = cv2.matchTemplate(img1_gray, template_list1[nameIndex1], cv2.TM_CCOEFF_NORMED)
            loc1 = np.where(res1 >= threshold)

            if len(loc1[0]):
                # Still detected
                thresholdCount1 = 0
                textName1 = name_list[nameIndex1]
                if settings.previewVideo:
                    for pt1 in zip(*loc1[::-1]):
                        # Draw the detected rectangle
                        detOrigin = (roiP1[0] + pt1[0], roiP1[1] + pt1[1])
                        detSize = (w1, h1)
                        cv2.rectangle(frame, detOrigin, tuple(np.add(detOrigin, detSize)), colorRed, borderThickness)

                        # Draw the detection label above the rectangle
                        drawLabel(textName1, frame, detOrigin, colorRed)
            else:
                # No match
                if thresholdCount1 > detectThreshold:
                    # Detection loss timeout
                    character1Detected = False
                    firstPass = True
                else:
                    # Start timer on detection loss
                    thresholdCount1 += 1 + frameSkip
        else:
        #this else is the initial look for a match
            # Loop until we find a matching template
            for templateIndex1, template1 in enumerate(template_list1):

                w1, h1 = template1.shape[::-1]
                res1 = cv2.matchTemplate(img1_gray, template1, cv2.TM_CCOEFF_NORMED)
                loc1 = np.where(res1 >= threshold)

                if len(loc1[0]):
                    # Detected successfully
                    thresholdCount1 = 0
                    character1Detected = True
                    nameIndex1 = templateIndex1
                    if settings.debug:
                        print('### P1', name_list[nameIndex1], '(template no: ' + str(nameIndex1) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break

        

        #
        # Player 2 Check
        #
        if character2Detected:

            # Keep monitoring the previously matched template
            w2, h2 = template_list2[nameIndex2].shape[::-1]
            res2 = cv2.matchTemplate(img2_gray, template_list2[nameIndex2], cv2.TM_CCOEFF_NORMED)
            loc2 = np.where(res2 >= threshold)

            if len(loc2[0]):
                # Still detected
                thresholdCount2 = 0
                textName2 = name_list[nameIndex2]
                if settings.previewVideo:
                    for pt2 in zip(*loc2[::-1]):
                        # Draw the detected rectangle
                        detOrigin = (roiP2[0] + pt2[0], roiP2[1] + pt2[1])
                        detSize = (w2, h2)
                        cv2.rectangle(frame, detOrigin, tuple(np.add(detOrigin, detSize)), colorBlue, borderThickness)

                        # Draw the detection label above the rectangle
                        drawLabel(textName2, frame, detOrigin, colorBlue)
            else:
                # No match
                if thresholdCount2 > detectThreshold:
                    character2Detected = False
                else:
                    thresholdCount2 += 1 + frameSkip
        else:

            # Loop until we find a matching template
            for templateIndex2, template2 in enumerate(template_list2):

                w2, h2 = template2.shape[::-1]
                res2 = cv2.matchTemplate(img2_gray, template2, cv2.TM_CCOEFF_NORMED)
                loc2 = np.where(res2 >= threshold)

                if len(loc2[0]):
                    # Detected
                    thresholdCount2 = 0
                    character2Detected = True
                    nameIndex2 = templateIndex2
                    if settings.debug:
                        print('### P2', name_list[nameIndex2], '(template no: ' + str(nameIndex2) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break

        #
        # Are we detecting a match for the first time?
        #
        if character1Detected and character2Detected and firstPass:
            firstPass = False
            previouslyDetected = True
            matchStart = frameCount / fps
            matchStartText = format(datetime.timedelta(seconds=math.trunc(matchStart)))
            # Print match start info
            # print(str(matchCount)+".", name_list[nameIndex1], "vs", name_list[nameIndex2], "started on", matchStartText)

        #
        # If we previously detected a match but now we don't, then record the end of match
        # this seems like a kind of fragile way to detect end of match.
        # alos the variable names are fucked. matchdetected? i think it should be character?
        #
        if not character1Detected and not character2Detected and previouslyDetected:
            firstPass = True
            previouslyDetected = False
            matchCount += 1
            matchEnd = frameCount / fps - detectThresholdSec
            matchEndText = format(datetime.timedelta(seconds=matchEnd))
            matchDuration = time.strftime("%H:%M:%S", time.gmtime(matchEnd - matchStart))
            # Print match end info
            # print(str(matchCount)+".", name_list[nameIndex1], "vs", name_list[nameIndex2], "ended on", time.strftime('%H:%M:%S', time.gmtime(matchEnd)))
            # Print match info
            #print(str(matchCount) + ".", matchStartText, "-", name_list[nameIndex1], "vs", name_list[nameIndex2], "(" + matchDuration + ")")
            #matches.append(printMatchInfo(matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration, settings.outputFormat))

            match = Match(matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration)
            matches.append(match)

            usage_list[nameIndex1] += 1  # Increment character usage (P1)
            usage_list[nameIndex2] += 1  # Increment character usage (P2)

        # Preview video during processsing, if enabled
        if settings.previewVideo:
            # cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            # cv2.resizeWindow('frame', int(width/2), int(height/2))
            cv2.imshow('frame', frame)
            if cv2.waitKey(11) & 0xFF == ord('q'):
                break

    else:
        # End of video reached, but check that a match wasn't in progress
        if character1Detected and character2Detected and previouslyDetected:
            matchCount += 1
            matchEnd = frameCount / fps
            matchEndText = format(datetime.timedelta(seconds=matchEnd))
            matchDuration = time.strftime("%H:%M:%S", time.gmtime(matchEnd - matchStart))
            
            print(str(matchCount) + ".", matchStartText, "-", name_list[nameIndex1], "vs", name_list[nameIndex2], "(" + matchDuration + ")")
            #matches.append(printMatchInfo(matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration, settings.outputFormat))

            match = Match(matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration)
            matches.append(match)

            usage_list[nameIndex1] += 1  # Increment character usage (P1)
            usage_list[nameIndex2] += 1  # Increment character usage (P2)
        break

cap.release()
cv2.destroyAllWindows()
timeEnd = datetime.datetime.now().replace(microsecond=0)
print('--')
print('Total matches based on characters:', matchCount)
print('Total matches based on scoreMatchCount:', scoreMatchCount)
print('Processing Time started:', timeStart)
print('Processing Time ended:', timeEnd)
print('Processing Time taken:', (timeEnd - timeStart))
print('')
printUsageInfo(usage_list, name_list)
writeOutput(matches, settings.outputFormat)