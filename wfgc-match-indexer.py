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
roiScore = settings.layoutFile.layout['originScore']
roiScoreWidth = settings.layoutFile.layout['widthScore']
roiScoreHeight = settings.layoutFile.layout['heightScore']

if settings.includeClock:
    roiClk = settings.layoutFile.layout['originClock']
    roiCw = settings.layoutFile.layout['widthClock']
    roiCh = settings.layoutFile.layout['heightClock']

if "threshold" in settings.layoutFile.layout: 
    threshold = settings.layoutFile.layout['threshold']
else:
    threshold = 0.9 # Default
print("Detection Threshold: {0}".format(threshold))
scoreThreshold = 0.9


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


if settings.includeClock: clockThresholdSec = 1

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
if settings.includeClock: clockThreshold = clockThresholdSec * fps

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
scoreFiles = glob.glob('.\scores\*.png')

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

# Prepare the Clock template
if settings.includeClock:
    clockImage = cv2.imread(settings.templatePath + 'clock.jpg', 0)
    clockTemplate = cv2.resize(clockImage, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)

# prepare the score template? idk...
for file in scoreFiles:
    image = cv2.imread(file, 0)
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    score_template_list.append(resImage)


# Init variables
scoreDetected = False

frameCount = 0
matchDetected1 = False
matchDetected2 = False
thresholdCount1 = 0
thresholdCount2 = 0
previouslyDetected = False
matchCount = 0 #original way using characters disapearing?
scoreMatchCount = 0 #my way of determining using score
firstPass = True
if settings.includeClock:
    clockDetected = False
    clockCount = 0
    firstPassClock = True
    clockPreviouslyOn = False
else:
    clockDetected = True


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
        # Setup Clock ROI: frame[ row_range (y-coord), col_range (x-coord) ]
        #
        if settings.includeClock:
            imgClk_roi = frame[roiClk[1]:roiClk[1] + roiCh, roiClk[0]:roiClk[0] + roiCw]
            imgClk_gray = cv2.cvtColor(imgClk_roi, cv2.COLOR_BGR2GRAY)
            # Draw Clock ROI
            if settings.previewVideo:
                cv2.rectangle(frame, roiClk, (roiClk[0] + roiCw, roiClk[1]+roiCh), colorCyan, borderThickness)

            w3, h3 = clockTemplate.shape[::-1]
            res3 = cv2.matchTemplate(imgClk_gray, clockTemplate, cv2.TM_CCOEFF_NORMED)
            loc3 = np.where(res3 >= threshold)

            if len(loc3[0]):
                # Detected
                if (clockCount > clockThreshold) and not clockDetected:
                    clockDetected = True
                    clockCount = 0
                else:
                    clockCount += 1 + frameSkip
            else:
                # Not detected
                if (clockCount > clockThreshold) and clockDetected:
                    clockDetected = False
                    clockCount = 0
                else:
                    clockCount += 1 + frameSkip

            if clockDetected and firstPassClock:
                firstPassClock = False
                clockPreviouslyOn = True

            if not clockDetected and clockPreviouslyOn:
                firstPassClock = True
                clockPreviouslyOn = False

            if settings.previewVideo and clockDetected:
                for pt3 in zip(*loc3[::-1]):
                    # Draw the detected rectangle
                    cv2.rectangle(frame,
                                (roiClk[0] + pt3[0], roiClk[1] + pt3[1]),
                                (roiClk[0] + pt3[0] + w3, roiClk[1] + pt3[1] + h3),
                                colorBlue,
                                borderThickness)

        #
        # Player 1 ROI: frame[ row_range (y-coord), col_range (x-coord) ]
        #
        img1_roi = frame[roiP1[1]:roiP1[1] + roiPh, roiP1[0]:roiP1[0] + roiPw]
        img1_gray = cv2.cvtColor(img1_roi, cv2.COLOR_BGR2GRAY)

        # Draw P1 ROI
        if settings.previewVideo:
            cv2.rectangle(frame, roiP1, (roiP1[0] + roiPw, roiP1[1] + roiPh), colorCyan, borderThickness)



        #
        # Detect round end stuff?
        # roiScore 
        # roiScoreWidth 
        # roiScoreHeight 
        #

        ##TODO: output the rectangle the whole time so i can check roi?
        ##move all that previw into same place?

        # image within the region of interest for the score!
        imgScore_roi = frame[roiScore[1]:roiScore[1] + roiScoreHeight, roiScore[0]:roiScore[0] + roiScoreWidth]
        imgScore_gray = cv2.cvtColor(imgScore_roi, cv2.COLOR_BGR2GRAY)
        if settings.previewVideo:
            cv2.rectangle(frame, roiScore, (roiScore[0] + roiScoreWidth, roiScore[1] + roiScoreHeight), colorCyan, borderThickness)

        if scoreDetected:
            # this continues to run while having a score.
            # Keep monitoring the previously matched template
            w1, h1 = score_template_list[gameCount].shape[::-1]
            res1 = cv2.matchTemplate(imgScore_gray, score_template_list[gameCount], cv2.TM_CCOEFF_NORMED)
            loc1 = np.where(res1 >= scoreThreshold)
            
            # image detected on frame.
            if len(loc1[0]):
                thresholdCountScore = 0
                textName1 = "game: " + str(gameCount)
                print('score detected:', textName1)

                if settings.previewVideo:
                    for pt1 in zip(*loc1[::-1]):
                        # Draw the detected rectangle
                        detOrigin = (roiScore[0] + pt1[0], roiScore[1] + pt1[1])
                        detSize = (w1, h1)
                        cv2.rectangle(frame, detOrigin, tuple(np.add(detOrigin, detSize)), colorRed, borderThickness)

                        # Draw the detection label above the rectangle
                        drawLabel(textName1, frame, detOrigin, colorRed)
            else:
                ## this should be a 1 off when we've detected a match end? 
                ## end of match and end of detection
                print('end of detection - match end:', scoreMatchCount)
                # No match
                if thresholdCountScore > detectThreshold:
                    # Detection loss timeout
                    scoreDetected = False
                    firstPass = True
                else:
                    # Start timer on detection loss
                    thresholdCountScore += 1 + frameSkip
        else:

            ##in here see if we find any score at all.
            ## can be heavy, we loop over the templates rather than using single image so this logic applies best to the characters
            ## for score i can maybe get rid of this.

            # Loop until we find a matching template
            #for templateIndex1, template1 in enumerate(score_template_list):
            res1 = cv2.matchTemplate(imgScore_gray, score_template_list[gameCount], cv2.TM_CCOEFF_NORMED)
            loc1 = np.where(res1 >= scoreThreshold)
            if len(loc1[0]):

                # This runs once upon first finding a score matching.

                print('start of detection - match end:', scoreMatchCount)
                # Detected successfully
                thresholdCountScore = 0
                scoreDetected = True
                scoreMatchCount += 1

                if settings.debug:
                    print('### (score no: ' + str(gameCount) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    #break
                    ##hmmm this was causing some issue breaking the whole thing. idk why it existed.



        

        #
        # Player 1 Check
        #
        # if 'match' detected, keep looking for it til it disapears
        if matchDetected1:

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
                    matchDetected1 = False
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
                    matchDetected1 = True
                    nameIndex1 = templateIndex1
                    if settings.debug:
                        print('### P1', name_list[nameIndex1], '(template no: ' + str(nameIndex1) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break

        #
        # Player 2 ROI: frame[ row_range (y-coord), col_range (x-coord) ]
        #
        img2_roi = frame[roiP2[1]:roiP2[1] + roiPh, roiP2[0]:roiP2[0] + roiPw]
        img2_gray = cv2.cvtColor(img2_roi, cv2.COLOR_BGR2GRAY)
        # Draw P2 ROI
        if settings.previewVideo:
            cv2.rectangle(frame,
                          roiP2,
                          (roiP2[0] + roiPw, roiP2[1] + roiPh),
                          colorCyan,
                          borderThickness)

        #
        # Player 2 Check
        #
        if matchDetected2:

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
                    matchDetected2 = False
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
                    matchDetected2 = True
                    nameIndex2 = templateIndex2
                    if settings.debug:
                        print('### P2', name_list[nameIndex2], '(template no: ' + str(nameIndex2) + ')', 'matched on:', time.strftime('%H:%M:%S', time.gmtime(frameCount / fps)))
                    break

        #
        # Are we detecting a match for the first time?
        #
        if clockDetected and matchDetected1 and matchDetected2 and firstPass:
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
        if not matchDetected1 and not matchDetected2 and previouslyDetected:
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
        if matchDetected1 and matchDetected2 and previouslyDetected:
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
print('Total matches:', matchCount)
print('Processing Time started:', timeStart)
print('Processing Time ended:', timeEnd)
print('Processing Time taken:', (timeEnd - timeStart))
print('')
printUsageInfo(usage_list, name_list)
writeOutput(matches, settings.outputFormat)