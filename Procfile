web: daphne -p $PORT -b 0.0.0.0 mysite.asgi:application
chatworker: python manage.py runworker --settings=mysite.settings 
scripts: python reset_online_count_script.py
