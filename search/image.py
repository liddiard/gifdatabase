import os
import urllib, cStringIO
from PIL import Image, ImageOps
from django.template import Library

THUMB_SIZE = 200,200

def generateThumb(url, size=THUMB_SIZE):
    '''must be passed a valid image url'''
    file = cStringIO.StringIO(urllib.urlopen(url).read())
    img = Image.open(file)
    width, height = img.size
    if img.mode != 'RGB': # could probably be skipped for this implementation
                          # because all gifs are indexed, not RGB
        img = img.convert('RGB')
    img = ImageOps.fit(img, THUMB_SIZE, Image.ANTIALIAS, 0)
    img.save('thumb.thumb', 'bmp')

def checkValidAnimatedGif(url):
    pass