import os, sys, nexmo
from os.path import join, dirname
from dotenv import load_dotenv
from os import environ
from flask import Flask

#get environment vars
envpath = join(dirname(__file__),"./.env")
load_dotenv(envpath)

#Instance of flask app, to get the application context needed for sqlalchemy
app = Flask(__name__)

#get the nexmo client
nexmo_client = nexmo.Client(
    application_id = environ.get('NEXMO_APPLICATION_ID'),
    private_key = environ.get('NEXMO_PRIVATE_KEY')
)

#Init the recordings array
recordings = []

#Importing needed models
if environ.get("DATABASE_ENGINE") == "firebase":
    from models.firebase import conferences, Conference
    Conferences = conferences()
    confs = Conferences.get_all()
elif environ.get("DATABASE_ENGINE") == "sqlalchemy":
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    from models.sqlengine import db, conferences, Conference
    db.init_app(app)
    with app.app_context():
        Conferences = conferences()
        confs = Conferences.get_all()

#Loop conferences
for conf in confs:
    #Add the recordings files that are not present in the static/conferences directory
    if conf["audio"] != "":
        #extract the recording_uuid and concat the extension
        filename = "{0}.mp3".format(conf["audio"].replace("https://api.nexmo.com/v1/files/",""))
        #verify if file exists in destination
        if not os.path.isfile(join(dirname(__file__),"./static/conferences/" + filename)):
            #if file doesnt exists add to the recording list
            recordings.append({ "filename": filename, "url": conf["audio"] })

#Download the recordings from the recording list
for recording in recordings:
    print("Getting recording audio: " + recording["filename"])
    audiopath = join(dirname(__file__),"./static/conferences/" + recording["filename"])
    #response is the audio - get the audio fromnexmo
    response = nexmo_client.get_recording(recording["url"])
    #save the audio file
    f=open(audiopath,"wb")
    f.write(response)
    f.close()