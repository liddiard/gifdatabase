from django.conf.urls import url
from search import views

urlpatterns = [

    # user preferences
    url(r'^preferences/$', views.AccountPreferencesView.as_view(), 
        name='account_preferences'),
    
    # new user registration
    url(r'^create/$', views.RegistrationView.as_view(), 
        name='registration_register'), # form
    url(r'^create/complete/$', views.RegistrationCompleteView.as_view(),
        name='registration_complete'),

    # new user activation
    url(r'^activate/complete/$', views.ActivationCompleteView.as_view(), 
        name='registration_activation_complete'),
    url(r'^activate/(?P<activation_key>\w+)/$', views.ActivationView.as_view(),
        name='registration_activate'),

    # password change
    url(r'^password/change/$', views.PasswordChangeView.as_view(), 
        name='password_change'), # form
    url(r'^password/change/done/$', views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),

    # password reset
    url(r'^password/reset/$', views.PasswordResetView.as_view(), 
        name='password_reset'), # form
    url(r'^password/reset/done/$', views.PasswordResetDoneView.as_view(), 
        name='password_reset_done'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^password/reset/complete/$', views.PasswordResetCompleteView.as_view(), 
        name='password_reset_complete'),

    # registration closed
    url(r'^create/closed/$', views.RegistrationClosedView.as_view(), 
        name='registration_disallowed'),

    # account deletion
    url(r'^delete/$', views.AccountDeleteView.as_view(), name='account_delete'),
    url(r'^delete/complete/$', views.AccountDeleteCompleteView.as_view(), 
        name='account_delete_complete'),
]
