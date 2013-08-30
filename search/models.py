from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import TextInput
from search.image import saveThumb
from settings.base import AWS_URL

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, Tag
from taggit.forms import TagWidget

DEFAULT_USER_ID = 1
THUMB_DIR = "thumb"

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
    
    def getThumb(self):
        return S3_URL + THUMB_DIR + "%s-%s" % (self.host, self.filename)
    
    def __unicode__(self):
        return "[%s-%s]  %s" % (self.host, self.filename,
                            ', '.join(self.tags.names()))
    
    class Meta:
        ordering = ["-date_added"]

class GifAdmin(admin.ModelAdmin):
    fields = (('host', 'filename'), 'tags', ('user_added','date_added'))
    readonly_fields = ('date_added',)
    list_display = ('host', 'filename', 'listTags', 'user_added', 'date_added')
    list_display_links = ('filename',)
    formfield_overrides = {
        TaggableManager: {'widget': TagWidget(attrs={'size':'100'})},
    }

admin.site.register(Gif, GifAdmin)
admin.site.register(TagInstance, TagInstanceAdmin)