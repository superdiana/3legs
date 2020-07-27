import nexmo, json
from flask import Flask, request, escape, jsonify

app = Flask(__name__)

conversation_name = 'conference-vegapp'

participants = [
    {
        "number":"50588888888",
        "role":"supervisor"
    },
    {
        "number":"50588804403",
	"role":"agent"
    },
    {
        "number":"50582327486",
	"role":"customer"
    }
]

def get_legs_by_role(role):
    global participants
    legs = []
    filter_parts = [participant for participant in participants if participant['role'] == role]
    for filter_part in filter_parts:
        if "leg" in filter_part:
             legs.append(filter_part['leg'])
    return legs

def get_role_by_number(number):
    global participants
    filter_part = [participant for participant in participants if participant['number'] == number]
    if len(filter_part) > 0 and "role" in filter_part[0]:
        return filter_part[0]['role']
    else:
        return None

def get_index_by_number(number):
    global participants
    filter_part = [index for index, participant in enumerate(participants) if participant['number'] == number]
    if len(filter_part) > 0:
        return filter_part[0]
    else:
        return None

#Customer use case
#Customer can speak with agents and supervisor. But can hear just the agent voice
def customer_ncco():
    global conversation_name
    return [
        {
	    "action": "conversation",
	    "name": conversation_name,
	    "startOnEnter": "false",
	    "musicOnHoldUrl": ["https://nexmo-community.github.io/ncco-examples/assets/voice_api_audio_streaming.mp3"],
	    "canSpeak": get_legs_by_role('agent') + get_legs_by_role('supervisor'),
	    "canHear": get_legs_by_role('agent')
	}
    ]

#When the agent enters the conference start and the application start recording.
#This ncco allows agents to hear and speak with everyone
def agent_ncco():
    global conversation_name
    return [
        {
	    "action": "conversation",
	    "name": conversation_name,
	    "startOnEnter": "true",
	    "record": "true",
	    "canSpeak": get_legs_by_role('customer') + get_legs_by_role('supervisor'),
	    "canHear": get_legs_by_role('customer') + get_legs_by_role('supervisor')
	}
    ]

#Supervisor can hear everyone, but just speaks with agents
def supervisor_ncco():
    global conversation_name
    return [
        {
	    "action": "conversation",
	    "name": conversation_name,
	    "startOnEnter": "false",
	    "musicOnHoldUrl": ["https://nexmo-community.github.io/ncco-examples/assets/voice_api_audio_streaming.mp3"],
	    "canSpeak": get_legs_by_role('agent'),
	    "canHear": get_legs_by_role('customer') + get_legs_by_role('agent')
	}
    ]

@app.route('/')
def home():
    name = request.args.get('name','Flask')
    return f'Hi, {escape(name)}'

@app.route('/webhooks/answer')
def ncco():
    #we define global participants here because we are going to modify
    global participants
    #get ncco by role
    role = get_role_by_number(request.args.get('from'))
    ncco = None
    if role == None:
        print({"error": "Invalid participant"})
        return jsonify({"error": "Invalid participant"}), 400
    else:
	#we assume the caller exists, so we pass the leg
	#get the caller index
        index = get_index_by_number(request.args.get('from')) 
	#assign the leg
        participants[index]['leg'] = request.args.get('uuid')
        if role == 'customer':
            ncco = customer_ncco()
        elif role == 'agent':
            ncco = agent_ncco()
        elif role == 'supervisor':
            ncco = supervisor_ncco()
    if ncco == None:
        print({"error": "Invalid role, no ncco was found"})
        return jsonify({"error": "Invalid role, no ncco was found"}), 400
    else:
        print(ncco)
        return jsonify(ncco)


#event_url in this case indicates the application what option has been choosen by the user
#the event_url returns the new NCCO depending of what option have been choosen
@app.route('/webhooks/events', methods=['POST','GET'])
def events():
    req = request.get_json()
    print(req)
    return 'Event response'
