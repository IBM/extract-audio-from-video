from flask import Flask, render_template, request, redirect, jsonify
import os
from werkzeug import secure_filename
import time
import pipes
import json
import requests
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import math

app = Flask(__name__)

app.config["VIDEOS_UPLOAD"] = "static/raw/"
app.config["AUDIO_FILES"] = "static/audios/"
app.config["COS_VIDEOS"] = "videos/"
app.config["COS_AUDIOS"] = "audios/"

# Constants for IBM COS values
COS_ENDPOINT = ""
COS_API_KEY_ID = ""
COS_AUTH_ENDPOINT = ""
COS_RESOURCE_CRN = ""
COS_BUCKET_LOCATION = "us-standard"
bucket_name = ""

'''Cloud Object Storage Methods'''

with open('credentials.json', 'r') as credentialsFile:
    credentials = json.loads(credentialsFile.read())

# connect to IBM cloud object storage
endpoints = requests.get(credentials.get('endpoints')).json()
iam_host = (endpoints['identity-endpoints']['iam-token'])
cos_host = (endpoints['service-endpoints']
            ['cross-region']['us']['public']['us-geo'])

# Assign Bucket Name
try:
    bucket_name = credentials.get('bucket_name')
except Exception as e:
    bucket_name = "notassigned"

# Constrict auth and cos endpoint
auth_endpoint = "https://" + iam_host + "/oidc/token"
service_endpoint = "https://" + cos_host

# Constants for IBM COS values
COS_ENDPOINT = service_endpoint
COS_API_KEY_ID = credentials.get('apikey')
COS_AUTH_ENDPOINT = auth_endpoint
# eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003abfb5d29761c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"
COS_RESOURCE_CRN = credentials.get('resource_instance_id')

# Create client
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id=COS_API_KEY_ID,
                         ibm_service_instance_id=COS_RESOURCE_CRN,
                         ibm_auth_endpoint=COS_AUTH_ENDPOINT,
                         config=Config(signature_version="oauth"),
                         endpoint_url=COS_ENDPOINT
                         )


@app.route('/COSBucket',  methods=['GET', 'POST'])
def setupCOSBucket():
    if request.method == 'POST':
        temp = request.form
        bkt = json.loads(temp['bkt'])
        with open('credentials.json', 'r') as credentialsFile:
            cred = json.loads(credentialsFile.read())
        cred.update(bkt)
        print(json.dumps(cred, indent=2))
        with open('credentials.json', 'w') as fp:
            json.dump(cred, fp,  indent=2)
        return jsonify({'flag': 0})

@app.route('/initCOS')
def initializeCOS():
    try:
        global bucket_name
        flag = False
        buckets = cos.buckets.all()
        with open('credentials.json', 'r') as credentialsFile:
            cred = json.loads(credentialsFile.read())
        for bucket in buckets:
            if cred['bucket_name'] == bucket.name:
                flag = True
                bucket_name = cred['bucket_name']
                break
        if not flag:
            respo = create_bucket(bucket_name)
        else:
            respo = {"message": "Bucket \"" + bucket_name + "\" found!"}
    except ClientError as be:
        respo = {"message": "CLIENT ERROR: {0}\n".format(be)}
    except Exception as e:
        respo = {"message": " {0}".format(e)}

    return json.dumps(respo, indent=2)


def create_bucket(bucket_name):
    print("Creating new bucket: {0}".format(bucket_name))
    try:
        cos.Bucket(bucket_name).create(
            CreateBucketConfiguration={
                "LocationConstraint": COS_BUCKET_LOCATION
            }
        )
        respo = {"message": "Bucket: {0} created!".format(bucket_name)}
        return respo

    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
        respo = {"message": "CLIENT ERROR: {0}\n".format(be)}
        return respo
    except Exception as e:
        print("Unable to create bucket: {0}".format(e))
        respo = {"message": "Unable to create bucket: {0}".format(e)}
        return respo


def get_bucket_contents(bucket_name):
    myList = []
    print("Retrieving bucket contents from: {0}".format(bucket_name))
    try:
        files = cos.Bucket(bucket_name).objects.all()
        for file in files:
            myList.append([file.key, file.size])
            print("Item: {0} ({1} bytes).".format(file.key, file.size))
        return myList
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve bucket contents: {0}".format(e))


def get_item(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(
        bucket_name, item_name))
    try:
        file = cos.Object(bucket_name, item_name).get()
        return file["Body"].read()
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))


def delete_item(bucket_name, item_name):
    print("Deleting item: {0}".format(item_name))
    try:
        cos.Object(bucket_name, item_name).delete()
        print("Item: {0} deleted!".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to delete item: {0}".format(e))


def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(
            item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))


'''Flask Helper Methods'''


def scanAvailableVideoFiles():
    availableFiles = os.listdir(app.config["VIDEOS_UPLOAD"])
    return availableFiles


def scanAvailableAudioFiles():
    availableFiles = os.listdir(app.config["AUDIO_FILES"])
    return availableFiles


def videoToAudio():
    for file in scanAvailableVideoFiles():
        print(file)
        if file.split('.')[0] in [x.split('.')[0] for x in scanAvailableAudioFiles()]:
            print("file already converted! Skipping...")
            myFlag = {"flag": 0}
            continue
        else:
            fileName = app.config["VIDEOS_UPLOAD"] + file
            try:
                file, file_extension = os.path.splitext(fileName)
                file = pipes.quote(file)
                filename = file.split('/')
                video_to_wav = 'ffmpeg -i ' + file + file_extension + \
                    ' -vn -f flac -ab 192000 -vn ' + \
                    app.config["AUDIO_FILES"] + filename[2] + '.flac'
                print(video_to_wav)
                os.system(video_to_wav)
                item_name = app.config["COS_AUDIOS"] + filename[2] + '.flac'
                file_path = app.config["AUDIO_FILES"] + filename[2] + '.flac'

                multi_part_upload(bucket_name, item_name, file_path)

                myFlag = {"flag": 0}
            except OSError as err:
                myFlag = {"flag": 1}

    return json.dumps(myFlag, indent=2)


def deleteFiles(fileName, fileType):
    try:
        fileNameLocal = fileName.split('/')[1]
        if fileType == 'video':
            fileToDelete = 'rm static/raw/' + fileNameLocal
        elif fileType == 'audio':
            fileToDelete = 'rm static/audios/' + fileNameLocal

        os.system(fileToDelete)
        item_name = fileName

        delete_item(bucket_name, item_name)

        myFlag = {"flag": 0}
    except OSError as err:
        myFlag = {"flag": 1}

    return json.dumps(myFlag, indent=2)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    try:
        if request.method == 'POST':
            if request.files:
                videos = request.files.getlist("video")
                for f in videos:
                    filename_converted = f.filename.replace(
                        " ", "-").replace("'", "").lower()
                    f.save(os.path.join(
                        app.config["VIDEOS_UPLOAD"], secure_filename(filename_converted)))

                    item_name = app.config["COS_VIDEOS"]+filename_converted
                    file_path = app.config["VIDEOS_UPLOAD"]+filename_converted

                    multi_part_upload(bucket_name, item_name, file_path)

        myResponse = {"message": 1}
    except Exception as e:
        print("Unable {0}".format(e))
        myResponse = {"message": str(e)}

    return json.dumps(myResponse, indent=2)


@app.route('/getAudioFiles')
def getAudioFiles():
    jsonList = []
    for file in get_bucket_contents(bucket_name):
        if file[0][0] == 'a':
            myDict = {'audioFile': file[0], 'fileSize': convert_size(file[1])}
            jsonList.append(myDict)
    return json.dumps(jsonList, indent=2)


@app.route('/getVideoFiles')
def getVideoFiles():
    jsonList = []
    for file in get_bucket_contents(bucket_name):
        if file[0][0] == 'v':
            myDict = {'videoFile': file[0], 'fileSize': convert_size(file[1])}
            jsonList.append(myDict)
    return json.dumps(jsonList, indent=2)


@app.route('/convert')
def convert():
    return videoToAudio()


@app.route('/deleteUploadedFile')
def deleteUploadedFile():
    fileName = request.args['fileName']
    fileType = request.args['fileType']
    return deleteFiles(fileName, fileType)


@app.route('/')
def index():
    return render_template('index.html')


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


port = os.getenv('VCAP_APP_PORT', '8081')
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=port)
