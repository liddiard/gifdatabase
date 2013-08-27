from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

# from taggit.managers import TaggableManager
# from taggit.models import TaggedItemBase

# Create your models here.
class Gif(models.Model):
    filename = models.CharField(max_length=32)
    HOST_CHOICES = (('ig', 'imgur.com'), ('mi', 'minus.com'))
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    tags = models.ManyToManyField(TagInstance)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey('User')
    
    def __unicode__(self):
        return "%s on %s-%s" % (', '.join([ti.tag.name for ti in self.tags_set.all()]), self.host, self.filename)
    
    class Meta:
        ordering = ["-date_added"]

class TagInstance(models.model):
    tag = models.ForeignKey('Tag')
    gif = models.ForeignKey('Gif')
    ups = models.IntegerField()
    downs = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey('User')
    
    def rating(self):
        try:
            total_votes = self.ups + self.downs
            return self.ups/total_votes
        except ZeroDivisionError:
            return 0.5
    
    def __unicode__(self):
        return "%s on %s-%s" % (self.tag.name, self.gif.host, self.gif.filename)

class Tag(models.Model):
    name = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey('User')
    
    def __unicode__(self):
        return self.name

admin.site.register(Gif, TagInstance, Tag)