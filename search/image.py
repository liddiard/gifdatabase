import os
import urllib, cStringIO
from PIL import Image, ImageOps
from django.template import Library

THUMB_SIZE = 200,200

def imgFromUrl(url):
    # should throw IOError if there's a problem
    file = cStringIO.StringIO(urllib.urlopen(url).read())
    img = Image.open(file)
    return img

def isAnimatedGif(img):
    try:
        img.seek(1)
    except EOFError:
        is_animated = False
    else:
        is_animated = True
    return is_animated

def generateThumb(img, size=THUMB_SIZE):
    '''must be passed a valid image url'''
    width, height = img.size
    img = img.convert('RGB')
    img = ImageOps.fit(img, THUMB_SIZE, Image.ANTIALIAS, 0)
    img.save('thumb.thumb', 'jpg')