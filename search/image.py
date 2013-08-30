import os
import urllib, cStringIO
from PIL import Image
from django.template import Library

THUMB_SIZE = 200,200

def generateThumb(url, size=THUMB_SIZE):
    '''must be passed a valid image url'''
    file = cStringIO.StringIO(urllib.urlopen(url).read())
    img = Image.open(file)
    width, height = img.size
    if width > height:
        delta = width - height
        left = int(delta/2)
        top = 0
        right = height + left
        bottom = height
    else:
        delta = height - width
        left = 0
        top = int(delta/2)
        right = width
        bottom = width + top
    img = img.crop((left, top, right, bottom))
    img = img.resize(THUMB_SIZE, Image.ANTIALIAS)
    img.save('thumb.thumb', 'gif')

def checkValidAnimatedGif(url):
    pass