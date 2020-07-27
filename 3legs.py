import os, random
from os.path import join, dirname
from dotenv import load_dotenv
from os import environ
from functools import wraps
from flask import Flask, session, redirect, url_for, request, render_template, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
import google.auth.transport.requests
from conference import conference
import nexmo

#get environment vars
envpath = join(dirname(__file__),"./.env")
load_dotenv(envpath)

app = Flask(__name__)

cors = CORS(app)
#define secret_key to flask app to manage sessions
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

if environ.get("DATABASE_ENGINE") == "firebase":
    #from models import firebase
    #Users = firebase.users()
    from models.firebase import users, User, conferences, Conference, Participant
elif environ.get("DATABASE_ENGINE") == "sqlalchemy":
    #Indicates that Flask App is going to work With SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("SQLALCHEMY_DATABASE_URI")
    #Disable the Track Modifications to improve performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #print(environ.get("SQLALCHEMY_DATABASE_URI"))
    from models.sqlengine import db, users, User, conferences, Conference, Participant
    db.init_app(app)
    #Push App Context for Database creation or model initialization
    #with app.app_context():
        #Execute this 2 lines the first time you run the application. Then remove them or comment them
        #db.create_all()

#Create conference object. Each Object key is a conference instance. When conference finished the instance is destroyed
Conferences = {}
#Init Nexmo client
nexmo_client = nexmo.Client(
    application_id = environ.get('NEXMO_APPLICATION_ID'),
    private_key = environ.get('NEXMO_PRIVATE_KEY')
)

def get_session(key):
    value = None
    if key in session:
        value = session[key]
    return value

#create the decorator to check if user is logged in
def check_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_session("user") is None:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

#Send global values to all templates
@app.context_processor
def inject_global_variables():
    return dict(client_id=os.getenv("GOOGLE_CLIENT_ID"), site_url=os.getenv("SITE_URL"), user = get_session("user"))

#When user logged in using google, check if the email is administrator, then create the session.
@app.route('/login',methods=['POST'])
def login():
    #First recheck if user is a valid google user
    try:
        token = request.form.get("idtoken")
        client_id = environ.get("GOOGLE_CLIENT_ID")
        infoid = id_token.verify_oauth2_token(token, google.auth.transport.requests.Request(), client_id)
        if infoid['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        userid = infoid['sub']
        Users = users()
        #print(Users)
        user = Users.get_by("email",request.form.get("email"))
        #Check if user is administrator, if not just force logout
        if user is not None and (user["role"] == 'administrator'):
            #Creates the session
            session["user"] = { "username": user["name"], "email": user["email"] }
            return "session_created"
        else:
            #Destroy session in the server
            session.pop("user",None)
            #Destroy session in the client
            return "destroy_session"
    except ValueError:
        return "destroy_session"
        pass

#user logout
@app.route('/logout')
def logout():
    #Remove the session
    session.pop("user",None)
    #Destroy session from client, we pass signal
    return render_template('login.html', signal="kill", client_id=os.getenv("GOOGLE_CLIENT_ID"), site_url=os.getenv("SITE_URL"))
    

#We return to the main Application flow.
@app.route('/',methods=['GET','POST'])
def home():
    #users.add(User(name=""))
    #Users.add(User(name="Melvin", role="agent", phone="88804403"))
    #print(Users.get_all())
    #print(User.query.filter_by(role='agent').first().__dict__)
    if get_session("user") != None:
        return render_template('home.html',  client_id=os.getenv("GOOGLE_CLIENT_ID"), user = get_session("user") )
    else:
        return render_template('login.html', client_id=os.getenv("GOOGLE_CLIENT_ID"), site_url=os.getenv("SITE_URL"))

@app.route('/users',methods=['GET'])
@check_login
def roles():
    Users = users()
    return render_template('user.html', action="list", users = Users.get_all())

@app.route('/user',methods=['GET'])
@app.route('/user/<key>',methods=['GET'])
@check_login
def role(key = None):
    if key is None:
        return render_template('user.html', action="add")
    else:
        Users = users()
        return render_template('user.html', action="edit", role = Users.get_by("id",key))
        
@app.route('/user',methods=['POST','PUT'])
@check_login
def role_change():
    name = "{0} / {1}".format(request.form.get("first_name"), request.form.get("last_name"))
    role = request.form.get("role")
    phone = request.form.get("phone")
    email = request.form.get("email")
    status = request.form.get("status")
    id = request.form.get("id")
    Users = users()
    #if request.method == "POST":
    if request.form.get("_method") == "PUT":
        Users.update({"name": name, "role": role, "phone": phone, "email": email, "status": status}, id)
    else:
        Users.add(User(name = name, role = role, phone = phone, email = email, status = status))
        
    return redirect(url_for('roles'))

#API Methods
@app.route('/user/<key>',methods=['DELETE'])
@check_login
def role_delete(key):
    Users = users()
    Users.delete(key)
    return "deleted"

@app.route('/conferences',methods=['GET'])
@check_login
def all_conferences():
    Conferences = conferences()
    return render_template('conference.html', conferences = Conferences.get_all())

#Webhooks
#NCCO ANSWER
@app.route('/webhooks/answer', methods=['GET','POST'])
def answer():
    global nexmo_client
    global Conferences
    #get the incoming call number
    phone = request.args.get('from')
    #Identify if the number is a valid customer, agent or supervisor
    Users = users()
    anonymus = Users.get_by(field='phone', value=phone)
    if anonymus is None:
        print({"error": "Invalid participant"})
        return jsonify({"error": "Invalid participant"}), 400
    elif anonymus["role"] == 'customer':
        #Is a customer
        customer = anonymus
        #Check for available agents and supervisors
        agents = Users.filterby({'status':'active','role':'agent'}, single=False)
        #select random agent
        agent = None
        if agents is not None:
            agent = random.choice(agents)
        if agent is None:
            #Return custom NCCO
            print("return speech NCCO")
            return jsonify([
                {
                    "action": "talk",
                    "text": "Thanks for calling to the nexmo conference. In this moment all agents are busy. Please try later"
                }
            ])
        else:
            #Change status
            Users.update({"status":"busy"}, agent["id"])
            #Create the conference in function of the agent
            Conferences[agent["phone"]] = conference()
            Conferences[agent["phone"]].add_participant({'number':agent["phone"], 'role':agent["role"]})
            #Get the customer leg
            customer_leg = request.args.get('uuid')
            Conferences[agent["phone"]].add_participant({'number':customer["phone"], 'role':customer["role"], 'leg': customer_leg})
            #Call the agent with the agent ncco and return the customer NCCO to the customer
            response = nexmo_client.create_call(
                {
                    "to": [{
                        "type": "phone",
                        "number": agent["phone"]
                    }],
                    "from": {
                        "type": "phone",
                        "number": environ.get('NEXMO_NUMBER')
                    },
                    "ncco": Conferences[agent["phone"]].agent_ncco(),
                    "eventUrl": [
                        "{url_root}/webhooks/events".format(url_root=environ.get("SITE_URL"))
                    ]
                }
            )
            print("Return customer ncco")
            return jsonify(Conferences[agent["phone"]].customer_ncco())
    else:
        print("Simple answer")
        return "Answer Response", 200

@app.route('/webhooks/events', methods=['POST','GET'])
def events():
    global Conferences
    req = request.get_json()
    if(req is None):
        req = dict(request.args)
    print(req)
    if "status" in req:
        #If answered and phone is from agent. Then Check the conference for agent, call the supervisor number if available 
        #And send him the supervisor ncco
        if req["status"] == "answered":
            phone = req["to"]
            #Check if agent phone - for this a conference must exist for the agent.
            if phone in Conferences:
                #We check for supervisor if available
                Users = users()
                supervisor = Users.filterby({'status':'active','role':'supervisor'})
                if supervisor is not None:
                    #Make supervisor reservation
                    Users.update({"status":"busy"}, supervisor["id"])
                    #Add supervisor to conference
                    Conferences[phone].add_participant({'number':supervisor["phone"], 'role':supervisor["role"]})
                    #Add Agent Leg to agent participant
                    agent_leg = req['uuid']
                    Conferences[phone].set_leg(agent_leg, phone)
                    #Make call to supervidor to connect him to conference
                    response = nexmo_client.create_call(
                        {
                            "to": [{
                                "type": "phone",
                                "number": supervisor["phone"]
                            }],
                            "from": {
                                "type": "phone",
                                "number": environ.get('NEXMO_NUMBER')
                            },
                            "ncco": Conferences[phone].supervisor_ncco(),
                            "eventUrl": [
                                "{url_root}/webhooks/events".format(url_root=environ.get("SITE_URL"))
                            ]
                        }
                    )
        elif req["status"] in ["unanswered","completed","rejected"]:
            phone = req["to"]
            Users = users()
            user = Users.filterby({'phone':phone})
            if user is not None:
                if user["role"] in ["supervisor","agent"]:
                    Users.update({"status":"active"}, user["id"])
                    if req["status"] == "completed":
                        if user["role"] == "agent":
                            #If conversation is completed and role is agent. Then save the conference to database
                            conf = conferences()
                            conf.add(Conference(name = Conferences[phone].name, date = req["timestamp"], audio='', conference_uuid=req["conversation_uuid"] ))
                            conf_item = conf.get_by_name(Conferences[phone].name)
                            parts = Conferences[phone].get_participants()
                            for part in parts:
                                user_item = Users.filterby({'phone': part["number"] })
                                leg = part["leg"] if "leg" in part else ""
                                conf.add_participant(Participant(conference_id=conf_item["id"], user_id=user_item["id"], user_leg=leg))
                            #Restart the conference value 
                            Conferences[phone] = None
    if "recording_url" in req:
        conf = conferences()
        conf_item = conf.get_by("conference_uuid", req["conversation_uuid"], single=True)
        conf.update({"audio": req["recording_url"]},conf_item["id"])

    return "Events received", 200