import uuid

#Join multiples array from matrix in a single one
def merge(matrix):
    increment = []
    for item in matrix:
        increment += item
    return increment

class conference():
    def __init__(self, key=None, secret=None, application_id=None, private_key=None, conference_name=None):
        self.name = "conference_{0}".format(uuid.uuid4()) if conference_name == None else conference_name
        self.participants = []
        self.roles = []
    def add_participant(self, participant):
        self.participants.append(participant)
    def get_participants(self):
        return self.participants
    def set_leg(self, leg, phone):
        index = self.get_index_by_number(phone)
        self.participants[index]["leg"] = leg
    def get_legs_by_role(self, role):
        legs = []
        filter_parts = [participant for participant in self.participants if participant['role'] == role]
        for filter_part in filter_parts:
            if "leg" in filter_part:
                legs.append(filter_part['leg'])
        return legs
    def get_role_by_number(self, number):
        filter_part = [participant for participant in self.participants if participant['number'] == number]
        if len(filter_part) > 0 and "role" in filter_part[0]:
            return filter_part[0]['role']
        else:
            return None
    def get_index_by_number(self, number):
        filter_part = [index for index, participant in enumerate(self.participants) if participant['number'] == number]
        if len(filter_part) > 0:
            return filter_part[0]
        else:
            return None
    def get_role_ncco(self, role, speak=None, hear=None):
        speak_legs = []
    #Customer can speak to everyone, but just can hear agent
    def customer_ncco(self):
        ncco = [
            {
	            "action": "conversation",
	            "name": self.name,
	            "startOnEnter": "false",
	            "musicOnHoldUrl": ["https://nexmo-community.github.io/ncco-examples/assets/voice_api_audio_streaming.mp3"],
	            "canSpeak": self.get_legs_by_role('agent') + self.get_legs_by_role('supervisor'),
	            "canHear": self.get_legs_by_role('agent')
	        }
        ]
        print(ncco)
        return ncco
    #Agent can hear/speak everyone
    def agent_ncco(self):
        ncco = [
            {
	            "action": "conversation",
	            "name": self.name,
	            "startOnEnter": "true",
	            "record": "true",
	            "canSpeak": self.get_legs_by_role('customer') + self.get_legs_by_role('supervisor'),
	            "canHear": self.get_legs_by_role('customer') + self.get_legs_by_role('supervisor')
	        }
        ]
        print(ncco)
        return ncco
    #Supervisor can hear everyone but just speak with agent
    def supervisor_ncco(self):
        ncco = [
            {
	            "action": "conversation",
	            "name": self.name,
	            "startOnEnter": "false",
	            "musicOnHoldUrl": ["https://nexmo-community.github.io/ncco-examples/assets/voice_api_audio_streaming.mp3"],
	            "canSpeak": self.get_legs_by_role('agent'),
	            "canHear": self.get_legs_by_role('customer') + self.get_legs_by_role('agent')
	        }
        ]
        print (ncco)
        return ncco
    