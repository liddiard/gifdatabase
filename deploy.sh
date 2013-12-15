yes 'yes' | python manage.py collectstatic --settings=gifdb.settings.prod
git push heroku master
