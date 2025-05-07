import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("Keys.json")

firebase_admin.initialize_app(cred, {

    'databaseURL':"",
    'storageBucket': ""
})







#Location for the student images
location_img = 'Images'

imgList = os.listdir(location_img)

student_ids =[]
list_img=[]

for path in imgList:
    list_img.append(cv2.imread(os.path.join(location_img, path)))
    student_ids.append(os.path.splitext(path)[0])
    
    
    
    #uploading the images to the database


    fileName=f'{location_img}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)
# print(student_ids)

def encoding(imagelist):
    encoded_list=[]
    for img in imagelist:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        # print("128 encodings",encode)
        # print(len(encode))
        encoded_list.append(encode)
    return encoded_list

print("Encoding in progress")

encode_list=encoding(list_img)
encode_list_with_ids=[encode_list,student_ids]
print("Successful")


file=open("EncodeFile.p",'wb')
pickle.dump(encode_list_with_ids,file)
file.close()
print("Encoded file created successfully")
