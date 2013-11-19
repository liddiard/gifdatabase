from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from search import image
from gifdb.settings.base import S3_URL

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
from taggit.forms import TagWidget

DEFAULT_USER_ID = 1
HOST_CHOICES = (('ig', 'imgur'),) # keys are ideally 2 letters,
                                  # cannot start with a number

def modifyUserScore(userObject, delta):
    u_score = UserScore.objects.get(user=userObject)
    u_score.score += delta
    u_score.save()

class UserScore(models.Model): 
    user = models.OneToOneField(User, primary_key=True)
    score = models.IntegerField(default=0)
    
    def __unicode__(self):
        return "%s (%s)" % (self.user, self.score)

def getUserScore(user):
    try:
        return UserScore.objects.get(user=user).score
    except UserScore.DoesNotExist:
        return ""
User.getUserScore = getUserScore

class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
admin.site.register(UserScore, UserScoreAdmin)

class Gif(models.Model):
    filename = models.CharField(max_length=32, unique=True)
    host = models.CharField(max_length=2, choices=HOST_CHOICES, default='ig')
    tags = TaggableManager(through='TagInstance')
    date_added = models.DateTimeField(auto_now_add=True)
    user_added = models.ForeignKey(User)
    stars = models.PositiveIntegerField(default=0)
    
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
    
    def delete(self):
        image.deleteThumb(self.getThumbFilename())
        modifyUserScore(self.user_added, -2)
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
    list_display = ('adminThumb', 'filename', 'host', 'tagNames', 'user_added',
                    'date_added')
    list_display_links = ('filename', 'adminThumb')
    formfield_overrides = {
        TaggableManager: {'widget': TagWidget(attrs={'size':'100'})},
    }
    date_hierarchy = 'date_added'
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
    
    def isBad(self):
        threshold = 0.4
        if self.score() < threshold:
            return True
        else:
            return False
    
    def isVerified(self):
        threshold = 0.6
        min_votes = 2
        total_votes = self.ups + self.downs
        if self.score() >= threshold and total_votes >= min_votes:
            return True
        else:
            return False
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
            pass 
        else:
            if not isVerified_before and isVerified_after:
                modifyUserScore(self.user_added, 1)
            elif isVerified_before and not isVerified_after:
                modifyUserScore(self.user_added, -1)
            if isBad_before and not isBad_after:
                modifyUserScore(self.user_added, 1)
            elif not isBad_before and isBad_after:
                modifyUserScore(self.user_added, -1)
        super(TagInstance, self).save(force_insert, force_update, *args,
                                      **kwargs)

class TagInstanceAdmin(admin.ModelAdmin):
    list_display = ('isVerified', 'tag', 'ups', 'downs', 'content_object',
                    'user_added', 'date_added')
    list_display_links = ('tag',)
    fields = (('tag', 'content_object'), ('ups', 'downs'),
              ('user_added', 'date_added'))
    readonly_fields = ('date_added', 'tag', 'content_object')
    date_hierarchy = 'date_added'
admin.site.register(TagInstance, TagInstanceAdmin)

class Flag(models.Model):
    gif = models.ForeignKey('Gif')
    #FLAGGED_CHOICES = (('nf', '404 not found'),
    #                   ('ic', 'inappropriate content'), ('ot', 'other'))
    #reason = models.CharField(choices=FLAGGED_CHOICES, max_length=2)
    message = models.CharField(max_length=500)
    date_flagged = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return unicode(self.gif)

class FlagAdmin(admin.ModelAdmin):
    list_display = ('gif', 'message', 'date_flagged')
    readonly_fields = ('date_flagged',)
admin.site.register(Flag, FlagAdmin)

class SubstitutionProposal(models.Model):
    current_gif = models.ForeignKey('Gif')
    proposed_gif = models.CharField(max_length=32)
    host = models.CharField(max_length=2, choices=HOST_CHOICES)
    date_proposed = models.DateTimeField(auto_now_add=True)
    user_proposed = models.ForeignKey(User)
    accepted = models.BooleanField(default=False)
    accepted.verbose_name = 'A'
    
    def __unicode__(self):
        return "%s > %s" % (self.current_gif, self.proposed_gif)

class SubstitutionProposalAdmin(admin.ModelAdmin):
    list_display = ('accepted', 'current_gif', 'proposed_gif', 'user_proposed',
                    'date_proposed')
    list_filter = ('accepted',)
    readonly_fields = ('accepted',)
    actions = ('accept_substitution_proposal',)
    
    def accept_substitution_proposal(modeladmin, request, queryset):
        for proposal in queryset:
            proposal.accepted = True
            old = proposal.current_gif
            old.filename = proposal.proposed_gif
            old.host = proposal.host
            proposal.save()
            old.save()
            modifyUserScore(proposal.user_proposed, 1)
admin.site.register(SubstitutionProposal, SubstitutionProposalAdmin)

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

class TagVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'up')
    list_filter = ('user', 'tag')
admin.site.register(TagVote, TagVoteAdmin)

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
    
    def delete(self):
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

