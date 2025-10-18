# Membership Club Application (MCARS)

A Django-based membership management system for clubs and organizations.

## Features

- Membership registration and management
- Different IFT-MCARS types and plans
- Family membership support
- Member portal with profile management
- Admin dashboard for membership approval and management
- Payment processing
- Email notifications

## Installation

1. Clone the repository
   ```
   git clone <repository-url>
   cd MCARS
   ```

2. Create a virtual environment and activate it
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run migrations
   ```
   python manage.py migrate
   ```

   5. Initialize IFT-MCARS types
   ```
   python manage.py initialize_membership_types
   ```

   or use the standalone script:
   ```
   python scripts/initialize_data.py
   ```

6. Create a superuser
   ```
   python manage.py createsuperuser
   ```

7. Run the development server
   ```
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Folder Structure

```
MCARS/
├── MCARS/              # Project settings
├── Members/            # Main application
│   ├── management/     # Custom management commands
│   ├── migrations/     # Database migrations
│   ├── models.py       # Data models
│   ├── views.py        # View controllers
│   ├── forms.py        # Form definitions
│   ├── urls.py         # URL routing
│   └── utils.py        # Utility functions
├── scripts/            # Standalone scripts
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
└── manage.py           # Django management script
```

## Usage

### Adding New IFT-MCARS Types

You can add new IFT-MCARS types through the Django admin interface or by modifying the `initialize_membership_types.py` script and running it again.

### Member Registration

Users can register for membership by visiting the registration page and selecting a plan. After registration, an admin must approve the membership before the user gains full access.

### Admin Approval

Admins can view pending membership approvals in the manager dashboard and approve or reject applications.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
