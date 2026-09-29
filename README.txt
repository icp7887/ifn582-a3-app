SETUP
1. python -m venv venv
2. Activate: venv\Scripts\activate (Windows) | source venv/bin/activate (Mac/Linux)
3. pip install flask flask-wtf flask-mysqldb
4. In MySQL: SOURCE project/database.sql;
5. Update DB credentials in project/__init__.py if needed
6. python run.py  ->  http://127.0.0.1:5000
