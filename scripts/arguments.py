# arguments.py
import os
import argparse
import importlib

from classes.settings import Settings  # Importing within function to prevent circular import

### TODO: default some of these arguments so it's sf6 anyyway, no need to keep saying it when i'm customizing this for sf ranbats anyway.

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

def is_valid_file(p, arg):
    fileName = arg.strip("\"")  # Remove trailing double-quote
    if not os.path.isfile(fileName):
        p.error('The file {} does not exist!'.format(fileName))
    else:
        # File exists so return the directory
        return fileName



def setupArguements():
    parser = argparse.ArgumentParser(description='Generate a fighting game match index with timestamps and characters used.')

    ### template and layout, probably could combine these, none would exist without the other.
    parser.add_argument('-l', '--layout', help='Name of the layout to use', metavar='LAYOUT')
    parser.add_argument('-t', '--template', help='Path to templates folder (default: \"templates\" in current folder)', type=lambda x: is_valid_directory(parser, x))

    #include clock in detection? (JB never used, could be useful as additional checking)
    parser.add_argument('-i', '--includeClock', help='Include clock detection', action='store_true')
    

    

    #preview window and optional scale
    parser.add_argument('-p', '--preview', type=float, nargs='?', const=0.5, help="Preview with scale as a decimal (e.g., 0.5 for half-size)")
    
    #what type of file to be saved as
    parser.add_argument('-of', '--outputFormat', type=str, help='Output format for results (txt, csv, json)')  

    ### window or file to be used.
    parser.add_argument('-f', '--filename', type=lambda x: is_valid_file(parser, x), required=False, help='Path to file you wish to assess')
    parser.add_argument('-w', '--window', type=str, required=False, help="Title of the application window to capture")

    #Debugging
    parser.add_argument('-d', '--debug' , help='Show some additional debugging values', action='store_true')

    return parser.parse_args()


#
# Process arguments
#
def processArguments(args):
    settings = Settings()
    
    # Check templates
    if args.template:
        settings.templatePath = os.path.join(args.template,'')
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
    if args.includeClock:
        settings.includeClock = True
        print("Clock detection: included")
    else:
        settings.includeClock = False
        print("Clock detection: excluded")

    # Check preview
    if args.preview is not None:
        settings.previewVideo = True
        settings.previewScale = args.preview if args.preview is not None else 0.5
        print("Preview: on")
    else:
        settings.previewVideo = False
        print("Preview: off")
    
    #output format
    if args.outputFormat is not None:
        settings.outputFormat = args.outputFormat
    else:
        settings.outputFormat = ""

    # TO-DO: Make the settings.debug flag more useful
    settings.debug = False
    if args.debug:
        settings.debug = True

    return settings