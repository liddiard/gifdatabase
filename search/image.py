import os
import urllib, cStringIO
from PIL import Image, ImageOps, ImageChops

from django.core.files.storage import default_storage as storage

THUMB_SIZE = 200,200

def imgFromUrl(url):
    try:
        file = cStringIO.StringIO(urllib.urlopen(url).read())
        img = Image.open(file)
        return img
    except IOError:
        return -1 # url is not a valid image or not accessible

def isAnimatedGif(img):
    try:
        img.seek(1)
    except EOFError:
        is_animated = False
    else:
        is_animated = True
    return is_animated

def saveThumb(img, filename, size=THUMB_SIZE):
    '''given a VALID image, generates and saves a thumbnail to S3'''
    # generate thumbnail
    width, height = img.size
    img = img.convert('RGB')
    img = ImageOps.fit(img, THUMB_SIZE, Image.ANTIALIAS, 0)
    
    # save to S3
    f = storage.open('thumb/%s.jpg' % filename, 'w')
    img.save(f, 'JPEG')
    f.close()
    return filename+'.jpg'

def imgurDoesNotExist(img):
    '''checks if an image is equal to the imgur "does not exist" image'''
    error_img = imgFromUrl("http://i.imgur.com/removed.png")
    try: # if the images are the same dimensions, we'll compare them
        diff = ImageChops.difference(img, error_img).getbbox()
        return diff is None
    except ValueError: # otherwise we get an error because the dimensions are
                       # different, so we know the input is NOT the DNE image
        return False