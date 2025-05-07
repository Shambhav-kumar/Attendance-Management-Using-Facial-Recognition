import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("Keys.json")

firebase_admin.initialize_app(cred, {

    'databaseURL':"add your database"
})

ref = db.reference("students")

data = {
        "1":
        {
            "Name":"",
            "Subject":"Physics",
            "total_attendance":8,
            "Semester":4,
            "last_attendance_time":"2024-07-11 00:54:34"

        },



}

for key, value in data.items():
    ref.child(key).set(value)