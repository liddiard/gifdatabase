from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, Tag

class TagInstance(TaggedItemBase):
    content_object = models.ForeignKey('Gif', related_name=
                                       "%(app_label)s_%(class)s_items")
    ups = models.IntegerField(default=0)
    downs = models.IntegerField(default=0)
    
    def __unicode__(self):
        data = {'host': self.content_object.host,
                'filename': self.content_object.filename,
                'tag': self.tag,
                'up': self.ups,
                'down': self.downs}
        return "[%(host)s-%(filename)s] %(up)s|%(down)s %(tag)s" % data               

class Gif(models.Model):
    filename = models.CharField(max_length=32)
    HOST_CHOICES = (('ig', 'imgur.com'), ('mi', 'minus.com'))
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    tags = TaggableManager(through=TagInstance)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    
    class Meta:
        ordering = ["-date_added"]
    
    def __unicode__(self):
        return "[%s-%s]  %s" % (self.host, self.filename,
                            ', '.join(self.tags.names()))

admin.site.register(TagInstance)
admin.site.register(Gif)
