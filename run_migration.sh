#!/bin/bash

# Run the migration to add profile_image field
python manage.py makemigrations
python manage.py migrate

# Start the server again
python manage.py runserver
