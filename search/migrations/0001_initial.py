# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserScore'
        db.create_table(u'search_userscore', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('score', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'search', ['UserScore'])

        # Adding model 'Gif'
        db.create_table(u'search_gif', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('host', self.gf('django.db.models.fields.CharField')(default='ig', max_length=2)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user_added', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('stars', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'search', ['Gif'])

        # Adding model 'TagInstance'
        db.create_table(u'search_taginstance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'search_taginstance_items', to=orm['taggit.Tag'])),
            ('content_object', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'search_taginstance_items', to=orm['search.Gif'])),
            ('ups', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('downs', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user_added', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['auth.User'])),
        ))
        db.send_create_signal(u'search', ['TagInstance'])

        # Adding model 'Flag'
        db.create_table(u'search_flag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gif', self.gf('django.db.models.fields.related.ForeignKey')(related_name='current', to=orm['search.Gif'])),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('duplicate', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='duplicate', null=True, to=orm['search.Gif'])),
            ('user_flagged', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_flagged', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('addressed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'search', ['Flag'])

        # Adding model 'SubstitutionProposal'
        db.create_table(u'search_substitutionproposal', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('current_gif', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['search.Gif'])),
            ('proposed_gif', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('host', self.gf('django.db.models.fields.CharField')(default='ig', max_length=2)),
            ('date_proposed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user_proposed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('accepted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'search', ['SubstitutionProposal'])

        # Adding model 'TagVote'
        db.create_table(u'search_tagvote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['search.TagInstance'])),
            ('up', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'search', ['TagVote'])

        # Adding model 'UserFavorite'
        db.create_table(u'search_userfavorite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('gif', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['search.Gif'])),
            ('date_favorited', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'search', ['UserFavorite'])


    def backwards(self, orm):
        # Deleting model 'UserScore'
        db.delete_table(u'search_userscore')

        # Deleting model 'Gif'
        db.delete_table(u'search_gif')

        # Deleting model 'TagInstance'
        db.delete_table(u'search_taginstance')

        # Deleting model 'Flag'
        db.delete_table(u'search_flag')

        # Deleting model 'SubstitutionProposal'
        db.delete_table(u'search_substitutionproposal')

        # Deleting model 'TagVote'
        db.delete_table(u'search_tagvote')

        # Deleting model 'UserFavorite'
        db.delete_table(u'search_userfavorite')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'search.flag': {
            'Meta': {'object_name': 'Flag'},
            'addressed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_flagged': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duplicate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'duplicate'", 'null': 'True', 'to': u"orm['search.Gif']"}),
            'gif': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current'", 'to': u"orm['search.Gif']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'user_flagged': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'search.gif': {
            'Meta': {'ordering': "['-date_added']", 'object_name': 'Gif'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'host': ('django.db.models.fields.CharField', [], {'default': "'ig'", 'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stars': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user_added': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'search.substitutionproposal': {
            'Meta': {'object_name': 'SubstitutionProposal'},
            'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_gif': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['search.Gif']"}),
            'date_proposed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'host': ('django.db.models.fields.CharField', [], {'default': "'ig'", 'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'proposed_gif': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user_proposed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'search.taginstance': {
            'Meta': {'object_name': 'TagInstance'},
            'content_object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'search_taginstance_items'", 'to': u"orm['search.Gif']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'downs': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'search_taginstance_items'", 'to': u"orm['taggit.Tag']"}),
            'ups': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user_added': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': u"orm['auth.User']"})
        },
        u'search.tagvote': {
            'Meta': {'object_name': 'TagVote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['search.TagInstance']"}),
            'up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'search.userfavorite': {
            'Meta': {'ordering': "['-date_favorited']", 'object_name': 'UserFavorite'},
            'date_favorited': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gif': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['search.Gif']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'search.userscore': {
            'Meta': {'object_name': 'UserScore'},
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['search']