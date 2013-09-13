from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from search import image
from gifdb.settings.base import S3_URL

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, Tag
from taggit.forms import TagWidget

DEFAULT_USER_ID = 1
HOST_CHOICES = (('ig', 'imgur'), ('mi', 'minus'))

def modifyUserScore(self, delta):
    u_score = UserScore.objects.get(user=self.user_added)
    u_score.score += delta
    u_score.save()

class UserScore(models.Model): 
    user = models.OneToOneField(User, primary_key=True)
    score = models.IntegerField(default=0)
    
    def __unicode__(self):
        return "%s (%s)" % (self.user, self.score)

class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
admin.site.register(UserScore, UserScoreAdmin)

class Gif(models.Model):
    filename = models.CharField(max_length=32)
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    tags = TaggableManager(through='TagInstance')
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    stars = models.PositiveIntegerField(default=0)
    
    def listTags(self):
        return ', '.join(self.tags.names())
    listTags.short_description = "tags"
    
    def getHostDomain(self):
        domain_list = {'ig': 'i.imgur.com', 'mi': 'minus.com'}
        return domain_list.get(self.host)
    
    def getUrl(self):
        domain = self.getHostDomain()
        return "http://%s/%s.gif" % (domain, self.filename)
    
    def getThumbUrl(self):
        thumb_url = {'s3': S3_URL, 'thumb': image.THUMB_DIR,
                     'host': self.host, 'file': self.filename}
        return "%(s3)s/%(thumb)s/%(host)s-%(file)s.jpg" % thumb_url
    
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
    
    __original_filename = None
    def __init__(self, *args, **kwargs):
        super(Gif, self).__init__(*args, **kwargs)
        self.__original_host = self.host
        self.__original_filename = self.filename
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if (self.filename != self.__original_filename or
            self.host != self.__original_host):
            img = image.imgFromUrl(self.getUrl())
            old_thumb_filename = "%s-%s" % (self.__original_host,
                                            self.__original_filename)
            new_thumb_filename = "%s-%s" % (self.host, self.filename)
            image.saveThumb(img, new_thumb_filename)
            image.deleteThumb(old_thumb_filename)
        is_new = self.pk is None
        if is_new: # only increase user's score if gif is created, not updated
            modifyUserScore(self, 1)
        super(Gif, self).save(force_insert, force_update, *args, **kwargs)
        self.__original_host = self.host
        self.__original_filename = self.filename
    
    def delete(self):
        modifyUserScore(self, -2)
        super(Gif, self).delete()
    
    class Meta:
        ordering = ["-date_added"]

class GifAdmin(admin.ModelAdmin):
    def displayGif(self, obj):
        return u'<img src="%s"/>' % obj.getUrl()
    displayGif.short_description = ''
    displayGif.allow_tags = True
    
    fields = (('host', 'filename'), ('displayGif', 'tags'),
              ('user_added','date_added'), ('stars',))
    readonly_fields = ('date_added', 'displayGif', 'stars')
    list_display = ('adminThumb', 'filename', 'host', 'listTags', 'user_added',
                    'date_added')
    list_display_links = ('filename', 'adminThumb')
    formfield_overrides = {
        TaggableManager: {'widget': TagWidget(attrs={'size':'400'})},
    }
admin.site.register(Gif, GifAdmin)

class TagInstance(TaggedItemBase):
    content_object = models.ForeignKey('Gif', related_name=
                                       "%(app_label)s_%(class)s_items",
                                       verbose_name="on")
    ups = models.PositiveIntegerField(default=0)
    downs = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User, default=DEFAULT_USER_ID)
    
    def score(self):
        try:
            total = self.ups + self.downs
            return round(self.ups / float(total), 2)
        except ZeroDivisionError:
            return 0.5
    
    def isBadTag(self):
        threshold = 0.4
        if self.score(self) < threshold:
            return True
        else:
            return False
    
    def isVerified(self):
        threshold = 0.6
        min_votes = 2
        total_votes = self.ups + self.downs
        if self.score >= threshold and total_votes >= min_votes:
            return True
        else:
            return False
    isVerified.boolean = True
    isVerified.short_description = "v"
    
        
    def __unicode__(self):
        data = {'host': self.content_object.host,
                'filename': self.content_object.filename,
                'tag': self.tag,
                'up': self.ups,
                'down': self.downs}
        return "%(up)s|%(down)s %(tag)s [%(host)s-%(filename)s]" % data

class TagInstanceAdmin(admin.ModelAdmin):
    list_display = ('isVerified', 'tag', 'ups', 'downs', 'content_object',
                    'user_added', 'date_added')
    list_display_links = ('tag',)
    fields = (('tag', 'content_object'), ('ups', 'downs'),
              ('user_added', 'date_added'))
    readonly_fields = ('date_added', 'tag', 'content_object')
admin.site.register(TagInstance, TagInstanceAdmin)

class Flag(models.Model):
    gif = models.ForeignKey('Gif')
    #FLAGGED_CHOICES = (('in', 'inappropriate content'),)
    #reason = models.CharField(choices=FLAGGED_CHOICES, max_length=2)
    message = models.CharField(max_length=500)
    
    def __unicode__(self):
        return self.gif
admin.site.register(Flag)

class SubstitutionProposal(models.Model):
    current_gif = models.ForeignKey('Gif')
    proposed_gif = models.CharField(max_length=32)
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    date_proposed = models.DateTimeField(auto_now_add=True)
    user_proposed = models.ForeignKey(User)
    
    def __unicode__(self):
        return "%s > %s" % (self.current_gif, self.proposed_gif)

class SubstitutionProposalAdmin(admin.ModelAdmin):
    list_display = ('current_gif', 'proposed_gif', 'user_proposed',
                    'date_proposed')
admin.site.register(SubstitutionProposal, SubstitutionProposalAdmin)

class TagVote(models.Model):
    user = models.ForeignKey(User)
    tag = models.ForeignKey('TagInstance')
    up = models.BooleanField()
    
    def __unicode__(self):
        if self.up:
            vote = "up"
        else:
            vote = "down"
        return "%s: %s on %s" % (self.user, vote, self.tag.name)

class TagVoteAdmin(admin.ModelAdmin):
    list_display = ('up', 'tag', 'user')
admin.site.register(TagVote, TagVoteAdmin)

class UserFavorite(models.Model):
    user = models.ForeignKey(User)
    gif = models.ForeignKey('Gif')
    date_favorited = models.DateTimeField(auto_now_add=True)
    
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.pk is None:
            g_favorite = self.gif
            g_favorite.stars += 1
            g_favorite.save()
        super(UserFavorite, self).save(force_insert, force_update, *args,
                                       **kwargs)
    
    def delete(self): # TODO: fix
        g_favorite = self.gif
        g_favorite.stars -= 1
        g_favorite.save()
        super(UserFavorite, self).delete()
    
    def __unicode__(self):
        return "%s: %s" % (self.user, self.gif)
    
    class Meta:
        ordering = ["-date_favorited"]

class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'gif', 'date_favorited')
admin.site.register(UserFavorite, UserFavoriteAdmin)