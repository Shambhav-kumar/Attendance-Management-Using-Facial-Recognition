import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime
import time

# Initialize Firebase
cred = credentials.Certificate("Keys.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "",
    'storageBucket': ""
})

bucket = storage.bucket()

# Setup Camera feed
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
cap.set(cv2.CAP_PROP_FPS, 240)

# Reading files for the background
path_Background = cv2.imread('C:/Users//OneDrive/Documents/VScode/miniproj/attendance/Resource/background.png')
path_mode = 'C:/Users//OneDrive/Documents/VScode/miniproj/attendance/Resource/Modes'

# Reading mode files and storing it in modeList
modeList = os.listdir(path_mode)
imgList = [cv2.imread(os.path.join(path_mode, img)) for img in modeList]

# Loading our encoded file
with open('EncodeFile.p', 'rb') as file:
    encode_list_with_ids = pickle.load(file)
encode_list, student_ids = encode_list_with_ids

modeType = 0
counter = 0
id = -1
imgStudent = []

frame_skip = 1  # Adjust the frame skip count
frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        continue

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    img = cv2.flip(img, 1)
    path_Background[162:162 + 480, 55:55 + 640] = img
    path_Background[44:44 + 633, 808:808 + 414] = imgList[modeType]

    # Lowering the img quality for processing
    img_small = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

    # Finding the location of faces in real-time and finding encoding
    live_faces = face_recognition.face_locations(img_small)
    face_encodings = face_recognition.face_encodings(img_small, live_faces)

    if live_faces:
        for encodeFace, faceloc in zip(face_encodings, live_faces):
            matches = face_recognition.compare_faces(encode_list, encodeFace)
            facedis = face_recognition.face_distance(encode_list, encodeFace)

            matchIndex = np.argmin(facedis)

            if matches[matchIndex] and 0.1 <= facedis[matchIndex] <= 0.5:  # Only load if confidence is in range
                id = student_ids[matchIndex]

                if counter == 0:
                    cvzone.putTextRect(path_Background, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", path_Background)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

                if counter == 1:
                    studentinfo = db.reference(f'students/{id}').get()
                    print(studentinfo)

                    # Get the image from the database
                    blob = bucket.get_blob(f'Images/{id}.png')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    # Update the attendance
                    datetimeObject = datetime.strptime(studentinfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)

                    if secondsElapsed > 30:
                        ref = db.reference(f'students/{id}')
                        studentinfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentinfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        path_Background[44:44 + 633, 808:808 + 414] = imgList[modeType]

                if 20 < counter <= 40:  # Adjusted counter range for mode 2
                    modeType = 2
                path_Background[44:44 + 633, 808:808 + 414] = imgList[modeType]

                if modeType != 3:
                    if counter < 20:
                        cv2.putText(path_Background, str(studentinfo['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)

                        cv2.putText(path_Background, str(studentinfo['Subject']), (1006, 550), cv2.FONT_HERSHEY_COMPLEX, .5,
                                    (255, 255, 255), 1)
                        cv2.putText(path_Background, str(id), (1006, 493), cv2.FONT_HERSHEY_COMPLEX, .5, (255, 255, 255), 1)
                        cv2.putText(path_Background, str(studentinfo['Semester']), (1025, 612), cv2.FONT_HERSHEY_COMPLEX,
                                    .5, (255, 255, 255), 1)

                        (w, h), _ = cv2.getTextSize(studentinfo['Name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(path_Background, str(studentinfo['Name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)

                        path_Background[175:175 + 216, 909:909 + 216] = imgStudent

                    counter += 1

                    if counter > 40:  # Adjusted counter reset point
                        counter = 0
                        modeType = 0
                        studentinfo = []
                        imgStudent = []
                        path_Background[44:44 + 633, 808:808 + 414] = imgList[modeType]

    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", path_Background)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
