from django.contrib import admin

from taggit.forms import TagWidget
from taggit.managers import TaggableManager

from .models import (UserScore, Gif, TagInstance, Flag, SubstitutionProposal,
                     TagVote, UserFavorite)


class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
admin.site.register(UserScore, UserScoreAdmin)


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


class TagInstanceAdmin(admin.ModelAdmin):
    list_display = ('isVerified', 'tag', 'ups', 'downs', 'content_object',
                    'user_added', 'date_added')
    list_display_links = ('tag',)
    fields = (('tag', 'content_object'), ('ups', 'downs'),
              ('user_added', 'date_added'))
    readonly_fields = ('date_added', 'tag', 'content_object')
    date_hierarchy = 'date_added'
admin.site.register(TagInstance, TagInstanceAdmin)


class FlagAdmin(admin.ModelAdmin):
    list_display = ('addressed', 'gif', 'reason', 'user_flagged', 'date_flagged')
    list_display_links = ('addressed', 'gif')
    readonly_fields = ('date_flagged',)
admin.site.register(Flag, FlagAdmin)


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


class TagVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'up')
    list_filter = ('user', 'tag')
admin.site.register(TagVote, TagVoteAdmin)


class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'gif', 'date_favorited')
admin.site.register(UserFavorite, UserFavoriteAdmin)
