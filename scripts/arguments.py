# arguments.py
import os
import argparse
import importlib

from classes.settings import Settings  # Importing within function to prevent circular import
    

#
# Setup Argument Parser
#

def is_valid_directory(p, arg):
    dirName = arg.strip("\"")  # Remove trailing double-quote
    if not os.path.isdir(dirName):
        p.error('The directory {} does not exist!'.format(dirName))
    else:
        # File exists so return the directory
        return dirName


def setupArguements():
    parser = argparse.ArgumentParser(description='Generate a fighting game match index with timestamps and characters used.')

    parser.add_argument(
        'layout',
        help='Name of the layout to use',
        metavar='LAYOUT')

    parser.add_argument('-c', help='Output CSV format', action='store_true')

    parser.add_argument('-i', help='Include clock detection', action='store_true')

    parser.add_argument('-n', help='Show match number sequentially in output', action='store_true')

    parser.add_argument('-d', help='Show some additional content stuff', action='store_true')

    #parser.add_argument('-p', help='Preview while indexing (press \'Q\' to quit the preview)', action='store_true')
    parser.add_argument('-p', '--previewScale', type=float, required=True, help="Preview scale as a decimal (e.g., 0.5 for half-size)")
    
    parser.add_argument(
        '-t',
        help='Path to templates folder (default: \"templates\" in current folder)',
        metavar='DIR', type=lambda x: is_valid_directory(parser, x))

    parser.add_argument('-z', help='Zoom preview window down to 50%% (used with the -p option)', action='store_true')

    # parser.add_argument(
    #     '-w',
    #     help='Application windows title',
    #     metavar='ApplicationTitle', type=str)
    parser.add_argument('-w', '--window', type=str, required=True, help="Title of the application window to capture")

    return parser.parse_args()


#
# Process arguments
#
def processArguments(args):
    settings = Settings()
    # Check templates
    if args.t:
        settings.templatePath = os.path.join(args.t,'')
        print('Custom templates path: {0}'.format(settings.templatePath))
    else:
        settings.templatePath = os.path.join('templates','')
        print('Default templates path: {0}'.format(settings.templatePath))

    # Check layouts
    if not os.path.isfile(os.path.join('./layouts', args.layout + '.py')):
        print("Layout {0}.py file does not exist in layouts/".format(args.layout))
        exit()
    else:
        settings.layoutFile = importlib.import_module("layouts." + args.layout)
        print('Layout: {0}'.format(args.layout))

    # Check clock detection inclusion
    if args.i:
        settings.includeClock = True
        print("Clock detection: included")
    else:
        settings.includeClock = False
        print("Clock detection: excluded")

    # Check preview
    if args.previewScale:
        settings.previewVideo = True
        settings.previewScale = args.previewScale
        print("Preview: on")
    else:
        settings.previewVideo = False
        print("Preview: off")

    # TO-DO: Make the settings.debug flag more useful
    settings.debug = False
    if args.d:
        settings.debug = True

    return settings