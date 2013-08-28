from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

# Create your models here.
class Gif(models.Model):
    filename = models.CharField(max_length=32)
    HOST_CHOICES = (('ig', 'imgur.com'), ('mi', 'minus.com'))
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    tags = TaggableManager()
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    
    class Meta:
        ordering = ["-date_added"]
    
    def __unicode__(self):
        return "[%s-%s]  %s" % (self.host, self.filename,
                            ', '.join(self.tags.names()))

admin.site.register(Gif)