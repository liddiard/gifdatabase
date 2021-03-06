from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.cache import cache

from registration.signals import user_activated
from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager

from gifdb.settings.base import S3_URL, OBFUSCATION_KEY
from search import image

DEFAULT_USER_ID = 1
TAG_MAX_LEN = 32
HOST_CHOICES = (('ig', 'imgur'),) # keys are ideally 2 letters,
                                  # cannot start with a number


# signals

def createUserScore(sender, **kwargs):
    u = kwargs.get('user')
    if u is not None:
        us = UserScore(user=u)
        us.save()
    else:
        print "user_activated signal caught, but UserScore not created"
user_activated.connect(createUserScore) # catch django_registration's
                                        # user_activated signal and create
                                        # necessary objects for user


# utility functions

def group(queryset, group, intermediate=False):
    if intermediate:
        for obj in queryset:
            obj.gif.group = group
    else:
        for obj in queryset:
            obj.group = group
    return queryset

def modifyUserScore(userObject, delta):
    u_score = UserScore.objects.get(user=userObject)
    u_score.score += delta
    u_score.save()

def queryRecentGifs():
    print "running query for recent gifs"
    queryset = group(Gif.objects.order_by('-date_added')[:9], 'recent')
    cache.set('recent_gifs', queryset)
    return queryset

def queryRecommendedGifs():
    print "running query for recommended gifs"
    queryset = group(Gif.objects.filter(date_added__gt=datetime.now()-\
                     timedelta(days=7)).order_by('-stars')[:9], "recommended")
    cache.set('recommended_gifs', queryset)
    return queryset


# models

class UserScore(models.Model): 
    user = models.OneToOneField(User, primary_key=True)
    score = models.IntegerField(default=0)
    
    def __unicode__(self):
        return "%s (%s)" % (self.user, self.score)

def getUserScore(user):
    if not user.is_authenticated:
        return None
    else:
        return UserScore.objects.get(user=user).score
User.getUserScore = getUserScore

def canTag(user):
    if getUserScore(user) > -10:
        return True
    else:
        return None
User.canTag = canTag

def canAddGif(user):
    if getUserScore(user) > -20:
        return True
    else:
        return None
User.canAddGif = canAddGif


class Gif(models.Model):
    filename = models.CharField(max_length=32, unique=True)
    host = models.CharField(max_length=2, choices=HOST_CHOICES, default='ig')
    tags = TaggableManager(through='TagInstance')
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    stars = models.PositiveIntegerField(default=0)

    def uid(self):
        return self.pk ^ OBFUSCATION_KEY
    
    def tagNames(self):
        return ', '.join(self.tags.names())
    tagNames.short_description = "tags"

    def tagList(self):
        return [tag for tag in TagInstance.objects.filter(content_object_id=self.id)]
    
    def getHostDomain(self):
        domain_list = {'ig': 'i.imgur.com'}
        return domain_list.get(self.host)
    
    def getUrl(self):
        domain = self.getHostDomain()
        return "http://%s/%s.gif" % (domain, self.filename)
    
    def getImgurThumb(self):
        domain = self.getHostDomain()
        return "http://%s/%ss.jpg" % (domain, self.filename)

    def getThumbFilename(self):
        return "%s-%s" % (self.host, self.filename)

    def getThumbUrl(self):
        thumb_url = {'s3': S3_URL, 'thumb': image.THUMB_DIR,
                     'host': self.host, 'file': self.filename}
        return "%(s3)s%(thumb)s/%(host)s-%(file)s.jpg" % thumb_url
    
    def adminThumb(self):
        return u'<img src="%s"/>' % self.getThumbUrl()
    adminThumb.short_description = "Thumbnail"
    adminThumb.allow_tags = True
    
    def clean(self):
        img = image.imgFromUrl(self.getUrl())
        if not img:
            raise ValidationError('''URL is not a valid image or not
                                  accessible.''')
        if image.imgurDoesNotExist(img):
            raise ValidationError("Image does not exist.")
        if not image.isAnimated(img):
            raise ValidationError("Image is not an animated GIF.")
    
    def __unicode__(self):
        return "[%s-%s]  %s" % (self.host, self.filename,
                            ', '.join(self.tags.names()))
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            img = image.imgFromUrl(self.getUrl())
            thumb_filename = self.getThumbFilename()
            image.saveThumb(img, thumb_filename)
            modifyUserScore(self.user_added, 1) # only increase user's score 
                                                # if gif is created, not updated
        super(Gif, self).save(force_insert, force_update, *args, **kwargs)
        cache.set('recent_gifs', queryRecentGifs)
    
    def delete(self):
        image.deleteThumb(self.getThumbFilename())
        modifyUserScore(self.user_added, -2)
        super(Gif, self).delete()
    
    class Meta:
        ordering = ["-date_added"]


class TagInstance(TaggedItemBase):
    content_object = models.ForeignKey('Gif', related_name=
                                       "%(app_label)s_%(class)s_items",
                                       verbose_name="on")
    ups = models.PositiveIntegerField(default=0)
    downs = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User, default=DEFAULT_USER_ID)

    def uid(self):
        return self.pk ^ OBFUSCATION_KEY
    
    def totalVotes(self):
        return self.ups + self.downs

    def score(self):
        try:
            return round(self.ups / float(self.totalVotes()), 2)
        except ZeroDivisionError:
            return 0.5
    
    def isBad(self):
        threshold = 0.4
        min_votes = 2
        return self.totalVotes() >= min_votes and self.score() < threshold
    
    def isVerified(self):
        threshold = 0.6
        min_votes = 1
        return self.totalVotes() >= min_votes and self.score() > threshold
    isVerified.boolean = True
    isVerified.short_description = "v"

    def hasBeenVotedOn(self):
        return self.ups + self.downs > 0

    def isNsfw(self):
        return self.tag.name.lower() == "nsfw"
    
    def __unicode__(self):
        data = {'host': self.content_object.host,
                'filename': self.content_object.filename,
                'tag': self.tag,
                'up': self.ups,
                'down': self.downs}
        return "%(up)s|%(down)s %(tag)s [%(host)s-%(filename)s]" % data
    
    __original_isBad = None
    __original_isVerified = None
    def __init__(self, *args, **kwargs):
        super(TagInstance, self).__init__(*args, **kwargs)
        self.__original_isBad = self.isBad()
        self.__original_isVerified = self.isVerified()
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        isBad_before = self.__original_isBad
        isVerified_before = self.__original_isVerified
        isBad_after = self.isBad()
        isVerified_after = self.isVerified()
        is_new = self.pk is None
        
        if is_new:
            super(TagInstance, self).save(force_insert, force_update, *args, 
                                          **kwargs)
        else:
            if not isVerified_before and isVerified_after:
                print "CASE 1"
                modifyUserScore(self.user_added, 1)
                super(TagInstance, self).save(force_insert, force_update, 
                                              *args, **kwargs)
            elif isVerified_before and not isVerified_after:
                print "CASE 2"
                modifyUserScore(self.user_added, -1)
                super(TagInstance, self).save(force_insert, force_update, 
                                              *args, **kwargs)
            # this should never get called in normal use because a bad tag
            # should be automatically deleted
            if isBad_before and not isBad_after:
                print "CASE 3"
                modifyUserScore(self.user_added, 1)
                super(TagInstance, self).save(force_insert, force_update, 
                                              *args, **kwargs)
            elif not isBad_before and isBad_after:
                print "CASE 4"
                modifyUserScore(self.user_added, -1)
                super(TagInstance, self).delete()
            else: # should never be called in normal operation
                super(TagInstance, self).save(force_insert, force_update, 
                                              *args, **kwargs)


class Flag(models.Model):
    gif = models.ForeignKey('Gif', related_name='current')
    FLAGGED_CHOICES = (('mi', '404 not found'),
                       ('in', 'inappropriate content'), ('du', 'duplicate'))
    reason = models.CharField(choices=FLAGGED_CHOICES, max_length=2)
    duplicate = models.ForeignKey('Gif', related_name='duplicate', null=True, 
                                  blank=True)
    user_flagged = models.ForeignKey(User)
    date_flagged = models.DateTimeField(auto_now_add=True)
    addressed = models.BooleanField(default=False)
    addressed.verbose_name = 'A'
    
    def __unicode__(self):
        return unicode(self.gif)


class SubstitutionProposal(models.Model):
    current_gif = models.ForeignKey('Gif')
    proposed_gif = models.CharField(max_length=32)
    host = models.CharField(max_length=2, choices=HOST_CHOICES, default='ig')
    date_proposed = models.DateTimeField(auto_now_add=True)
    user_proposed = models.ForeignKey(User)
    accepted = models.BooleanField(default=False)
    accepted.verbose_name = 'A'
    
    def __unicode__(self):
        return "%s > %s" % (self.current_gif, self.proposed_gif)


class TagVote(models.Model):
    user = models.ForeignKey(User)
    tag = models.ForeignKey('TagInstance')
    up = models.BooleanField()

    __original_up = None
    def __init__(self, *args, **kwargs):
        super(TagVote, self).__init__(*args, **kwargs)
        self.__original_up = self.up
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        is_new = self.pk is None
        super(TagVote, self).save(force_insert, force_update, *args, **kwargs)
        if is_new:
            if self.up:
                self.tag.ups += 1
            else:
                self.tag.downs += 1
            self.tag.save()
        elif self.up != self.__original_up:
            if self.up:
                self.tag.downs -= 1
                self.tag.ups += 1
            else:
                self.tag.downs += 1
                self.tag.ups -= 1
            self.tag.save()
        self.__original_up = self.up

    def delete(self):
        print "entered custom delete method"
        if self.up:
            print "decreasing tag ups"
            self.tag.ups -= 1
        else:
            print "decreasing tag downs"
            self.tag.downs -= 1
        self.tag.save()
        super(TagVote, self).delete()

    def __unicode__(self):
        if self.up:
            vote = "up"
        else:
            vote = "down"
        return "%s: %s on \"%s\"" % (self.user, vote, self.tag.tag)


class UserFavorite(models.Model):
    user = models.ForeignKey(User)
    gif = models.ForeignKey('Gif')
    date_favorited = models.DateTimeField(auto_now_add=True)
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            g_favorite = self.gif
            g_favorite.stars += 1
            g_favorite.save()
        super(UserFavorite, self).save(force_insert, force_update, *args,
                                       **kwargs)
        cache.set('recommended_gifs', queryRecommendedGifs)
    
    def delete(self):
        g_favorite = self.gif
        g_favorite.stars -= 1
        g_favorite.save()
        super(UserFavorite, self).delete()
    
    def __unicode__(self):
        return "%s: %s" % (self.user, self.gif)
    
    class Meta:
        ordering = ["-date_favorited"]
