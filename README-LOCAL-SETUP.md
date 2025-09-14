# HMS Local Development Setup

## Quick Start

### Option 1: Using Batch Files (Recommended)
1. **Start Backend Server**:
   - Double-click `start-backend.bat`
   - This will start the Django server at http://127.0.0.1:8000

2. **Start Frontend Server**:
   - Double-click `start-frontend.bat`
   - This will start the Vite server at http://localhost:5173

3. **Create Admin User**:
   - Double-click `create-superuser.bat`
   - Follow the prompts to create an admin user

### Option 2: Manual Commands

#### Backend Setup:
```bash
cd "M:\hms\Newhms-fixed-v11\backend"
venv\Scripts\activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 127.0.0.1:8000
```

#### Frontend Setup:
```bash
cd "M:\hms\Newhms-fixed-v11\frontend\hms-frontend"
npm run dev
```

#### Create Superuser:
```bash
cd "M:\hms\Newhms-fixed-v11\backend"
venv\Scripts\activate
python manage.py createsuperuser
```

## Access URLs

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **Django Admin**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/schema/swagger-ui/

## Default Configuration

The application is configured with:
- **Database**: SQLite (local file)
- **Debug Mode**: Enabled
- **CORS**: Allow all origins (development only)
- **Email Backend**: Console (emails printed to console)
- **Cache**: In-memory (no Redis required)
- **Celery**: Eager mode (no broker required)

## Creating Test Data

After creating a superuser, you can:
1. Access Django Admin at http://127.0.0.1:8000/admin/
2. Create test hospitals, users, patients, etc.
3. Use the frontend application at http://localhost:5173

## Environment Variables

All environment variables are configured in `backend/.env`:
- `DJANGO_DEBUG=true` - Enable debug mode
- `CORS_ALLOW_ALL_ORIGINS=true` - Allow frontend to connect
- `CELERY_TASK_ALWAYS_EAGER=true` - Run tasks synchronously

## Troubleshooting

### Backend Issues:
- If migrations fail: `python manage.py migrate --run-syncdb`
- If static files missing: `python manage.py collectstatic --noinput`
- Check `.env` file exists in backend directory

### Frontend Issues:
- If dependencies missing: `npm install`
- If build fails: `npm run build`
- Check Node.js version compatibility

### Port Conflicts:
- Backend runs on port 8000
- Frontend runs on port 5173 (default Vite port)
- Change ports if needed in respective configuration files

## Features Available

The HMS includes modules for:
- **User Management** - Authentication, roles, permissions
- **Patient Management** - Registration, medical records
- **Appointments** - Scheduling, calendar management
- **Electronic Health Records (EHR)** - Medical history, documents
- **Pharmacy** - Medication management, prescriptions
- **Laboratory** - Test orders, results
- **Billing** - Invoice generation, payment tracking
- **Analytics** - Reports, dashboards
- **Feedback** - Patient feedback system
- **HR** - Staff management
- **Facilities** - Hospital resource management

## Next Steps

1. Run both servers using the batch files
2. Create a superuser using the create-superuser script
3. Access the frontend at http://localhost:5173
4. Login with your admin credentials
5. Explore the various modules and features

## Notes

- This setup is for local development only
- All data is stored in a local SQLite database
- Changes to code will auto-reload in both backend and frontend
- Backend API is fully functional with JWT authentication
