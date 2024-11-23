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
import json

from scripts.util import scaleDimension, drawLabel
from scripts.arguments import setupArguements, processArguments
from scripts.printinfo import printMatchInfo, printUsageInfo, writeOutput
from scripts.windowsizing import getWindowRegionInfo
from scripts.getstartggdata import getEventInfo

from classes.settings import Settings
from classes.match import Match


#TODO: come from input params probably
eventId = 1250662

eventInfo = getEventInfo(1250662)
print('Eventual data:', json.dumps(eventInfo, indent=4))
