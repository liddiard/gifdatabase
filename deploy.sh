yes 'yes' | python manage.py collectstatic --settings=gifdb.settings.base
git push heroku master
