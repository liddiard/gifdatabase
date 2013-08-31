from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import TextInput
from search.image import THUMB_DIR, imgFromUrl, saveThumb, deleteThumb
from gifdb.settings.base import S3_URL

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, Tag
from taggit.forms import TagWidget

DEFAULT_USER_ID = 1

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

class Gif(models.Model):
    filename = models.CharField(max_length=32)
    HOST_CHOICES = (('ig', 'imgur'), ('mi', 'minus'))
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    tags = TaggableManager(through=TagInstance)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    
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
        thumb_url = {'s3': S3_URL, 'thumb': THUMB_DIR,
                     'host': self.host, 'file': self.filename}
        return "%(s3)s/%(thumb)s/%(host)s-%(file)s.jpg" % thumb_url
    
    def adminThumb(self):
        return u'<img src="%s"/>' % self.getThumbUrl()
    adminThumb.short_description = "Thumbnail"
    adminThumb.allow_tags = True
    
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
            img = imgFromUrl(self.getUrl())
            old_thumb_filename = "%s-%s" % (self.__original_host,
                                            self.__original_filename)
            new_thumb_filename = "%s-%s" % (self.host, self.filename)
            saveThumb(img, new_thumb_filename)
            deleteThumb(old_thumb_filename)
        super(Gif, self).save(force_insert, force_update, *args, **kwargs)
        self.__original_filename = self.filename
    
    class Meta:
        ordering = ["-date_added"]

class GifAdmin(admin.ModelAdmin):
    def displayGif(self, obj):
        return u'<img src="%s"/>' % obj.getUrl()
    displayGif.short_description = ''
    displayGif.allow_tags = True
    
    fields = (('host', 'filename'), ('displayGif', 'tags'),
              ('user_added','date_added'))
    readonly_fields = ('date_added', 'displayGif')
    list_display = ('adminThumb', 'filename', 'host', 'listTags', 'user_added',
                    'date_added')
    list_display_links = ('filename', 'adminThumb')
    formfield_overrides = {
        TaggableManager: {'widget': TagWidget(attrs={'size':'400'})},
    }

admin.site.register(Gif, GifAdmin)
admin.site.register(TagInstance, TagInstanceAdmin)