WADI INVESTMENT - Loan management starter
=========================================

Features
--------
- Agent self-registration with administrator approval
- Customer records and search
- Loan issuance: fixed 25% flat interest on principal, 30-day term
- Daily payment recording with optional M-Pesa / receipt reference
- Automatic principal + interest totals and balance calculation
- Missed scheduled instalments carry forward as arrears
- Overdue status based on unpaid scheduled amounts
- Dashboard, loan filtering, and Django admin records

Run locally in PyCharm
----------------------
1. Open the folder containing manage.py in PyCharm.
2. In the PyCharm terminal, run:
   python -m pip install -r requirements.txt
3. Create/apply database migrations:
   python manage.py makemigrations core
   python manage.py migrate
4. If you do not already have an administrator, create one:
   python manage.py createsuperuser
5. Start the app:
   python manage.py runserver
6. Open http://127.0.0.1:8000/
   Admin: http://127.0.0.1:8000/admin/

Approving agents
----------------
Log in to /admin/, open Agent profiles, and change the new agent's status to Approved.

Loan rules
----------
- Interest = principal * 25% (flat interest, calculated on the original amount).
- Total due = principal + interest.
- Term = 30 days.
- First scheduled instalment is due the day after the loan issue date.
- Unpaid scheduled instalments remain in arrears; the next due amount is the daily instalment plus arrears.
- No automatic penalty or additional interest is applied.
- Payments cannot exceed the remaining loan balance.

Important
---------
This project is for local development/testing. It currently uses SQLite and DEBUG=True.
Do not expose it publicly or use real customer data until production settings, a secure
SECRET_KEY, HTTPS, access controls, backups, and a hosted database have been configured.
SQLite on one computer does not synchronize data across computers or phones. For shared
use, deploy the app to a secure host and use a shared PostgreSQL database.
