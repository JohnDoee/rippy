python manage.py migrate
python manage.py collectstatic --noinput -c

exec supervisord -n -c /supervisor.conf