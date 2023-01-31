import cv2
import pytesseract
import numpy as np
import csv
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--path_video", help="Path to the video file")
parser.add_argument("--path_result", help="Path to the result file")
args = parser.parse_args()
path_video = args.path_video
path_output = args.path_result


# Путь к запускаемому файлу Tesseract. Может быть изменен или удален по требованию.
pytesseract.pytesseract.tesseract_cmd = 'Tesseract/tesseract.exe'


# Load the video
video = cv2.VideoCapture(path_video)


# Define the range of red
lower_red = (0,50,50)
upper_red = (10,255,255)

# Define the range of blue
lower_blue = (110,50,50)
upper_blue = (130,255,255)

# Define the range of black
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 255, 30])

# Define the range of white
lower_white = np.array([0, 0, 200])
upper_white = np.array([180, 30, 255])


## ROIs of needed regions
left_name = 256, 639, 268, 40
time = 571, 626, 135, 58
right_name = 740, 641, 274, 40
left_color = 531, 657, 12, 10
right_color = 725, 656, 10, 9
first_round = 618, 629, 2, 4
second_round = 631, 630, 5, 3
third_round = 644, 629, 2, 1


# Increasing the size of image and grayscacling for better accuracy
def preprocess_frame(img):
    img = cv2.resize(img,(150, 100))
    img = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return(img)



def detect_round(first_round, second_round, third_round):
    # third round
    x, y, w, h = third_round
    roi = frame[y:y + h, x:x + w]

    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Create a mask for each range of colors
    mask_black = cv2.inRange(hsv, lower_black, upper_black)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # Find contours in the mask
    contours_black = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    contours_white = cv2.findContours(mask_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    # Check if white contour was found
    if len(contours_white) > 0:
        return 3
    else:

        # Second round
        x, y, w, h = second_round
        roi = frame[y:y + h, x:x + w]

        # Convert the image to the HSV color space
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Create a mask for each range of colors
        mask_black = cv2.inRange(hsv, lower_black, upper_black)
        mask_white = cv2.inRange(hsv, lower_white, upper_white)

        # Find contours in the mask
        contours_black = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours_white = cv2.findContours(mask_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        # Check if white contour was found
        if len(contours_white) > 0:
            return 2
        else:
            return 1


frame_n = 0
id = 0
fields = ['frame_number', 'First_fighter', 'Second_fighter', 'First_fighter_color', 'Second_fighter_color', 'time_left', 'round']



while True:

    # Read a frame from the video
    ret, frame = video.read()

    # Check if the video has ended
    if not ret:
        break

    # Name on the left
    x, y, w, h = left_name[0], left_name[1], left_name[2], left_name[3]

    # Extract the ROI from the frame
    roi = frame[y:y + h, x:x + w]

    # Use OCR to extract the text from the ROI
    text_ln = pytesseract.image_to_string(roi)

    # Name on the right
    x, y, w, h = right_name[0], right_name[1], right_name[2], right_name[3]

    # Extract the ROI from the frame
    roi = frame[y:y + h, x:x + w]

    # Use OCR to extract the text from the ROI
    text_rn = pytesseract.image_to_string(roi)

    # Color in the left
    x, y, w, h = left_color
    roi = frame[y:y + h, x:x + w]

    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Create a mask for each range of colors
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Find contours in the mask
    contours_red = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    contours_blue = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    # Check if any contours were found
    first_color = None
    second_color = None
    if len(contours_red) > 0:
        first_color = 'Red'
        second_color = 'Blue'

    if len(contours_blue) > 0:
        first_color = 'Blue'
        second_color = 'Red'




    # Если одно из имен или один из цветов не обнаружено, переходим к следующему кадру
    if len(text_ln) == 0 or len(text_rn) == 0 or first_color == None or second_color == None:
        frame_n = frame_n + 1
        continue


    # Time left
    x, y, w, h = time[0], time[1], time[2], time[3]

    # Extract the ROI
    roi = frame[y:y + h, x:x + w]
    # Preprocessing
    roi = preprocess_frame(roi)
    # Use OCR to extract the text from the ROI
    text_time = pytesseract.image_to_string(roi)


    # Calling the function to detect round number
    round_n = detect_round(first_round, second_round, third_round)

    # Columns to be added to the csv file
    row = [
        [frame_n, text_ln, text_rn, first_color, second_color, text_time, round_n]]

    # Если появилось всплывающее окно в первый раз, то создаем CSV файл
    if id == 0:
        filename = path_output
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            csvwriter.writerows(row)
    # Дополняем файл
    else:
        filename = path_output
        with open(filename, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(row)

    frame_n = frame_n + 1
    id = id + 1

video.release()


