#!/usr/bin/env python
"""Q12 Bot

A small help for the Q12 contest. Automatically identifies the questions and
guesses the most likely answer.

"""

import os
import sys
import cv2
import argparse
from   pyautogui import screenshot, position
from   PIL import Image
import pytesseract
import webbrowser
from   urllib.parse import urlencode
import re
import json
import requests
from   bs4 import BeautifulSoup



# Settings
settings_file = './q12_bot/settings.json'
search_url = 'https://www.google.com/search?'
pixels_positions = {}


# Functions
# Calibrate screen
def calibrate_screen():
    if not os.path.isfile(settings_file):
        print('\n*** Starting calibration of your screen:\n')

        pixels_positions = {'question':[], 'answers':[]}
        print('Put mouse over the TOP LEFT corner of the QUESTION (do not click) and press ENTER.')
        input()
        pixels_positions['question'].append(position())
        print('Put mouse over the BOTTOM RIGHT corner of the QUESTION (do not click) and press ENTER.')
        input()
        pixels_positions['question'].append(position())
        for i in range(3):
            pixels_positions['answers'].append([])
            print('Put mouse over the TOP LEFT corner of the ANSWER ' + str(i + 1) + ' (do not click) and press ENTER.')
            input()
            pixels_positions['answers'][i].append(position())
            print('Put mouse over the BOTTOM RIGHT corner of the ANSWER ' + str(i + 1) + ' (do not click) and press ENTER.')
            input()
            pixels_positions['answers'][i].append(position())

        with open(settings_file, 'w') as outfile:
            json.dump(pixels_positions, outfile)
    else:
        print('Using previous calibration. (To recalibrate, delete the settings.json file).')
        with open(settings_file) as infile:
            pixels_positions = json.load(infile)
    return pixels_positions


# Take screenshot
def take_screenshot():
    tempfile = './q12_bot/' + '{}_screenshot.png'.format(os.getpid())
    screenshot_image = screenshot()
    screenshot_image.save(tempfile)
    image = cv2.imread(os.path.abspath(tempfile))
    os.remove(tempfile)
    return image

# Preprocess images
def preprocess_question(image, start, end):
    image = image[start[1]:end[1], start[0]:end[0]]
    image = cv2.bitwise_not(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return image


def preprocess_answer(image, start, end):
    image = image[start[1]:end[1], start[0]:end[0]]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return image


# Apply Tesseract OCR to get the text
def apply_ocr(image):
    tempfile = "./q12_bot/{}_for_ocr.png".format(os.getpid())
    cv2.imwrite(tempfile, image)
    text = pytesseract.image_to_string(Image.open(tempfile))
    text = text.replace('\n', ' ')
    os.remove(tempfile)
    return text


# Get number of google search results
def get_number_search_results(search_terms):
    r = requests.get('https://www.google.es/search', params={'q':search_terms})
    soup = BeautifulSoup(r.text, 'lxml')
    res = soup.find('div', {'id': 'resultStats'})
    try:
        number = int( re.sub('\D', '', res.text) )
    except ValueError:
        number = 0
    return number




# Script
def main(debug=False):
    pixels_positions = calibrate_screen()

    print('*** READY: Press ENTER to analyze the question when it is on screen.')

    while (1):
        input()
        print('Running new search!')
        image = take_screenshot()

        question_image = preprocess_question(image, pixels_positions['question'][0], pixels_positions['question'][1])
        question_text = apply_ocr(question_image)

        # debug
        if debug:
            print(question_text)


        # Preprocess answers images
        answer_results = []

        for i in range(len(pixels_positions['answers'])):
            answer_image = preprocess_answer(image, pixels_positions['answers'][i][0], pixels_positions['answers'][i][1])
            answer_text = apply_ocr(answer_image)

            # Launch google searches
            search_terms = ' '.join([question_text, answer_text])
            search = {'q': search_terms}
            webbrowser.open(search_url + urlencode(search))

            # Store number of google search results
            number_of_results = get_number_search_results(search_terms)
            answer_results.append(number_of_results)

            # debug
            if debug:
                print(answer_text)


        # Display a visual indicator of the amount of search results
        if max(answer_results) > 0:
            print('Number of search results for each answer:')
            for i in range(len(answer_results)):
                print(answer_results[i], int(answer_results[i] / max(answer_results) * 25) * '|' )

        print('Ready for the next one.')





if __name__ == "__main__":
    """When invoked as a script, run the main() function.
    """
    debug = sys.argv[1]=='-dbg' if len(sys.argv) > 1 else False
    main(debug)
