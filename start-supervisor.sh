python manage.py migrate
python manage.py collectstatic --noinput -c
python manage.py cleanup_active

exec supervisord -n -c /supervisor.conf