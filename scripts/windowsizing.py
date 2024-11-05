# windowsizing.py
import pygetwindow

def getWindowRegionInfo(application_title):

    # Get the window using pygetwindow
    try:
        window = pygetwindow.getWindowsWithTitle(application_title)[0]  # Get the first matching window
    except IndexError:
        print(f"Window with title '{application_title}' not found. Defaulting to 1920x1080")
        #window = pygetwindow.getWindowsWithTitle(application_title)[0]  # Get the first matching window
        return (0, 0, 1920, 1080), 1920, 1080
        #exit()

    # Get the window position and size
    left, top, width, height = window.left, window.top, window.width, window.height

    # Fix region if it's negative.
    if left < 0 or top < 0:
        left, top = 0, 0

    region = (left, top, left + width, top + height)  # Define the region

    return region, width, height