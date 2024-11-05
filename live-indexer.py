# -*- coding: utf-8 -*-
import datetime
import glob
import os
import math
import time

import numpy as np
import cv2
import pygetwindow
import dxcam

from scripts.util import scaleDimension, drawLabel
from scripts.arguments import setupArguements, processArguments
from scripts.printinfo import printMatchInfo, printUsageInfo
from scripts.windowsizing import getWindowRegionInfo


from classes.settings import Settings


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


args = setupArguements()
settings = processArguments(args)
application_region, applicationWidth, applicationHeight = getWindowRegionInfo(args.window)
print('region?:', application_region)
applicationResolution = (applicationWidth, applicationHeight)


### really these are more settings that could be put into a model but...i'll wait.
# Initialise ROI variables from layout file
templateScale = settings.layoutFile.layout['scale']
templateResolution = settings.layoutFile.layout['templateResolution']
# roiP1 = scaleDimension(settings.layoutFile.layout['originPlayer1'], templateResolution, applicationResolution)
# roiP2 = scaleDimension(settings.layoutFile.layout['originPlayer2'], templateResolution, applicationResolution)
# roiPw = scaleDimension(settings.layoutFile.layout['widthPortrait'], templateResolution, applicationResolution, "width")
# roiPh = scaleDimension(settings.layoutFile.layout['heightPortrait'], templateResolution, applicationResolution, "height")

roiP1 = settings.layoutFile.layout['originPlayer1']
roiP2 = settings.layoutFile.layout['originPlayer2']
roiPw = settings.layoutFile.layout['widthPortrait']
roiPh = settings.layoutFile.layout['heightPortrait']


if "threshold" in settings.layoutFile.layout: 
    threshold = settings.layoutFile.layout['threshold']
else:
    threshold = 0.9 # Default
print("Detection Threshold: {0}".format(threshold))


if settings.debug:
    print("original roiP1:", settings.layoutFile.layout['originPlayer1'])
    print("scaled roiP1:", roiP1)
    print("original roiP2:", settings.layoutFile.layout['originPlayer2'])
    print("scaled roiP2:", roiP2)



'''
layout is made at 1920x1080
but i play at 2560x1440

I need to scale the game down?
I should also detect region i guess
'''


# No. of frames to skip: speeds up analysis
frameSkip = 30

# No. of seconds before we consider detection lost
detectThresholdSec = 6


# Video input
##cap = cv2.VideoCapture(videoFile)
camera = dxcam.create(device_idx=0, output_idx=0)
print('dx camera created')

### i feel like i need this? but at same time something was working without.
camera.start(target_fps=30, video_mode=True, region=application_region)
print('camera started')

# Determine frames per second of video
##fps = cap.get(cv2.CAP_PROP_FPS)
fps = 30


# No. of Frames before we lose detection
detectThreshold = detectThresholdSec * fps

# Empty list to store template images
template_list1 = []
template_list2 = []
name_list = []
usage_list = []
nameIndex1 = 0
nameIndex2 = 0



# Make a list of all Player 1 and 2 template images from a directory
files1 = glob.glob(settings.templatePath + '*-1p.jpg')
files2 = glob.glob(settings.templatePath + '*-2p.jpg')

# Prepare the Player 1 and 2 templates
for myfile in files1:
    image = cv2.imread(myfile, 0)
    # Resize
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    template_list1.append(resImage)
    charaName = os.path.basename(myfile).replace('-1p.jpg', '').title()
    name_list.append(charaName)  # Build the character name list
    usage_list.append(0)  # Initialise usage values to 0

print('check templateList1:', template_list1)
print('check namelist:', name_list)

for myfile in files2:
    image = cv2.imread(myfile, 0)
    # Resize
    resImage = cv2.resize(image, None, fx=templateScale, fy=templateScale, interpolation=cv2.INTER_LINEAR)
    template_list2.append(resImage)

print('check templateList2:', template_list2)


# Init variables
frameCount = 0
matchDetected1 = False
matchDetected2 = False
thresholdCount1 = 0
thresholdCount2 = 0
previouslyDetected = False
matchCount = 0
firstPass = True


print('preview rect??:', roiP1)
print('preview rect??:', (roiP1[0] + roiPw, roiP1[1] + roiPh))

if settings.previewVideo:
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('frame', int(applicationWidth * settings.previewScale), int(applicationHeight * settings.previewScale))

#
# Start capture
#    
##while True:
##while cap.isOpened():
while camera.is_capturing:
  
    # Exit on pressing 'q'
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break


    unscaled_frame = camera.get_latest_frame() 
    frame = cv2.resize(unscaled_frame, (1920, 1080))# Will block until new frame. not sure i want.


    if frame is not None:

        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)  # convert RGBA to BGR for OpenCV



        



        ###
        # TODO: I think this frame skip is like...so we only check every x? 
        ###

        # Frame skipping logic
        if frameSkip > 0 and matchCount % frameSkip != 0:
            matchCount += 1
            continue
        ## if ret:
        frameCount += 1
        # Let's only check every few frames as defined by frameCount
        if frameSkip > 0 and frameCount % frameSkip != 0:
            continue



        #
        # Player 1 ROI: frame[ row_range (y-coord), col_range (x-coord) ]
        #
        img1_roi = frame[roiP1[1]:roiP1[1] + roiPh, roiP1[0]:roiP1[0] + roiPw]
        img1_gray = cv2.cvtColor(img1_roi, cv2.COLOR_BGR2GRAY)

        

        #
        # Player 1 Check
        #
        if matchDetected1:

            print('some match found, idk')

            # Keep monitoring the previously matched template
            w1, h1 = template_list1[nameIndex1].shape[::-1]
            res1 = cv2.matchTemplate(img1_gray, template_list1[nameIndex1], cv2.TM_CCOEFF_NORMED)
            loc1 = np.where(res1 >= threshold)

            if len(loc1[0]):
                # Still detected
                thresholdCount1 = 0
                textName1 = name_list[nameIndex1]

                print('found match so:', textName1)

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

            #print('looping looking for match?:')

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
        
            # print('roiP2:', roiP2)
            # print('roiPw', roiPw)
            # print('roiPh', roiPh)
            

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
        if matchDetected1 and matchDetected2 and firstPass:
            firstPass = False
            previouslyDetected = True
            matchStart = frameCount / fps
            matchStartText = format(datetime.timedelta(seconds=math.trunc(matchStart)))
            # Print match start info
            # print(str(matchCount)+".", name_list[nameIndex1], "vs", name_list[nameIndex2], "started on", matchStartText)

        #
        # If we previously detected a match but now we don't, then record the end of match
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
            printMatchInfo(args, matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration)
            usage_list[nameIndex1] += 1  # Increment character usage (P1)
            usage_list[nameIndex2] += 1  # Increment character usage (P2)

        

        # Draw P1 ROI
        # Draw P2 ROI
        if settings.previewVideo:
            cv2.rectangle(frame, roiP1, (roiP1[0] + roiPw, roiP1[1] + roiPh), colorCyan, borderThickness)
            cv2.rectangle(frame, roiP2, (roiP2[0] + roiPw, roiP2[1] + roiPh), colorCyan, borderThickness)            
            cv2.imshow('frame', frame)


    # some kind of error so want to settings.debug
    elif frame is None:    
        # Check if the camera is running
        if not camera:
            print("settings.debug: Camera is not initialized properly.")
            
        # Print camera settings for more insight
        if hasattr(camera, 'settings'):
            print(f"settings.debug: Camera settings - {camera.settings}")
            
        # If capturing a specific window, check if the title matches
        if hasattr(camera, 'window'):
            print(f"settings.debug: Target window - {camera.window}")

        print("Warning: Frame is None. Retrying...")
        time.sleep(0.1)  # Brief pause to reduce repeated calls
        continue  # Skip this iteration and try again

    # intended intentional end
    else:
        print("end of video reached according to this thingy")
        print("indicating frame is none?", frame)
        # End of video reached, but check that a match wasn't in progress
        if matchDetected1 and matchDetected2 and previouslyDetected:
            matchCount += 1
            matchEnd = frameCount / fps
            matchEndText = format(datetime.timedelta(seconds=matchEnd))
            matchDuration = time.strftime("%H:%M:%S", time.gmtime(matchEnd - matchStart))
            # print(str(matchCount) + ".", matchStartText, "-", name_list[nameIndex1], "vs", name_list[nameIndex2], "(" + matchDuration + ")")
            printMatchInfo(args, matchCount, matchStartText, name_list[nameIndex1], name_list[nameIndex2], matchDuration)
            usage_list[nameIndex1] += 1  # Increment character usage (P1)
            usage_list[nameIndex2] += 1  # Increment character usage (P2)
        break



##cap.release()
print('not true? stopping')

# Get screen size from dxcam
## width, height = camera.display_res(device_idx=0) #chatgpt fail.
#height, width = frame.shape[:2]

##print('Video: {0}' . format(videoFile))
print('Frame width: {0:.0f}' . format(applicationWidth))
print('Frame height: {0:.0f}' . format(applicationHeight))
print('Frame rate: {0:.2f} fps' . format(fps))


##print('Length: {0}' . format(
 ##   time.strftime("%H:%M:%S", time.gmtime(totalFrames / fps))))
print('--')

camera.stop()
cv2.destroyAllWindows()

timeEnd = datetime.datetime.now().replace(microsecond=0)
print('--')
print('Total matches:', matchCount)
print('Processing Time started:', timeStart)
print('Processing Time ended:', timeEnd)
print('Processing Time taken:', (timeEnd - timeStart))
print('')
printUsageInfo(usage_list, name_list)

