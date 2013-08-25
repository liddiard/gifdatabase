from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

# Create your models here.
class Gif(models.Model):
    url = models.CharField(max_length=200)
    tags = TaggableManager()
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    nsfw = models.BooleanField()
    
    class Meta:
        ordering = ["-date_added"]
    
    def __unicode__(self):
        return "%s | %s" % (', '.join(self.tags.names()), self.url)

admin.site.register(Gif)