#util.py
import numpy as np
import cv2

# can i not pass in the original and target? mmmm
def scaleDimension(original_value, original_res=(1920, 1080), target_res=(2560, 1440), dimension=None):
    original_width, original_height = original_res
    target_width, target_height = target_res

    # Calculate scaling factors
    scale_x = target_width / original_width
    scale_y = target_height / original_height

    # Check if input is a tuple (x, y) or a single dimension (width or height)
    if isinstance(original_value, tuple):
        scaled_x = int(original_value[0] * scale_x)
        scaled_y = int(original_value[1] * scale_y)
        return (scaled_x, scaled_y)
    else:
        # Check which dimension to scale if specified
        if dimension == "width":
            return int(original_value * scale_x)
        elif dimension == "height":
            return int(original_value * scale_y)
        else:
            # Default: scale as both width and height
            scaled_value_x = int(original_value * scale_x)
            scaled_value_y = int(original_value * scale_y)
            return scaled_value_x, scaled_value_y



# Text label properties
fontFace = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 0.7
fontColor = (255, 255, 255)
fontThickness = 2
borderThickness = 1
textPadding = 2

colorFill = -1


#
# Draw Label function
#
def drawLabel(text, img, origin, bgcolor):

    textSize, textBaseline = cv2.getTextSize(text, fontFace, fontScale, fontThickness)
    labelOrigin = (origin[0] - int(borderThickness / 2), origin[1] - textSize[1] - borderThickness - textPadding * 2)
    labelSize = (textSize[0] + textPadding * 2, textSize[1] + borderThickness + textPadding * 2)
    cv2.rectangle(img, labelOrigin, tuple(np.add(labelOrigin, labelSize)), bgcolor, colorFill)
    textOrigin = (origin[0] + textPadding, origin[1] - textPadding - borderThickness)
    cv2.putText(img, text, textOrigin, fontFace, fontScale, fontColor, fontThickness)