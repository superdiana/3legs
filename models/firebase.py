import firebase_admin, os
from firebase_admin import credentials
from os.path import join, dirname
from dotenv import load_dotenv
from firebase_admin import firestore

#get environment vars
envpath = join(dirname(__file__),"./.env")
load_dotenv(envpath)

#get the credentials
credits = credentials.Certificate(os.getenv("FIREBASE_PRIVATE_KEY"))
#credits = credentials.Certificate(join(dirname(__file__),"../firebase.json"))
#Init the application
firebase_admin.initialize_app(credits)

class model:
    def __init__(self,key):
        self.key = key
        self.db = firestore.client()
        self.collection = self.db.collection(self.key)
    def get_by(self, field, value, single=True):
        if field != "id":
            docs = list(self.collection.where(field,u'==',u'{0}'.format(value)).stream())
            item = None
            if docs != None:
                if len(docs) > 0:
                    if single:
                        item = docs[0].to_dict()
                        item['id'] = docs[0].id
                    else:
                        item = []
                        for doc in docs:
                            element = doc.to_dict()
                            element['id'] = doc.id
                            item.append(element)
                        if len(item) == 0:
                            item = None
        else:
            document = self.collection.document(u'{id}'.format(id=value)).get()
            item = document.to_dict()
            item["id"] = document.id
        return item
    def filterby(self, filters, single=True):
        query = self.collection
        for field, value in filters.items():
            query = query.where(u'{}'.format(field), u'==', u'{}'.format(value))
        docs = list(query.stream())
        items = []
        for doc in docs:
            item = None
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
        if len(items) > 0:
            if single:
                return items[0]
            else:
                return items
        else:
            return None
    def get_all(self):
        docs = self.collection.stream()
        items = []
        for doc in docs:
            item = None
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
        if len(items) > 0:
            return items
        else:
            return None
    def add(self, data, id=None):
        if id == None:
            self.collection.add(data)
        else:
            self.collection.document(u'{0}'.format(id)).set(data)
        return True
    def update(self, data, id):
        if id != None:
            if data != None:
                doc = self.collection.document(u'{id}'.format(id=id))
                doc.update(data)
        return False
    def delete(self, id):
        self.collection.document(u'{id}'.format(id=id)).delete()
    
class User:
    def __init__(self, name = '', role = '', phone = '', email = '', status = ''):
        self.name = name
        self.role = role
        self.phone = phone
        self.email = email
        self.status = status
        
class Conference:
    def __init__(self, name = '', date = '', conference_uuid = '', audio = '', participants = []):
        self.name = name
        self.date = date
        self.participants = participants
        self.conference_uuid = conference_uuid
        self.audio = audio

class Participant:
    def __init__(self, user_id = '', user_leg = '', conference_id = ''):
        self.user_id = user_id
        self.user_leg = user_leg
        self.conference_id = conference_id

class users(model):
    def __init__(self):
        super().__init__(u'users')
    def add(self, data, id = None):
        if type(data) is User:
            super().add(data.__dict__,id)
        else:
            super().add(data,id)

class conferences(model):
    def __init__(self):
        self.Users = users()
        super().__init__(u'conferences')
    def add(self, data, id = None):
        if type(data) is Conference:
            super().add(data.__dict__,id)
        else:
            super().add(data,id)
    def get_by_name(self, name):
        docs = list(self.collection.where(u'name',u'==',u'{0}'.format(name)).stream())
        item = None
        if docs != None:
            if len(docs) > 0:
                item = docs[0].to_dict()
                item['id'] = docs[0].id
        return item
    def get_by_id(self, id):
        return self.get_by("id", id)
    def add_participant(self, participant):
        conf = self.get_by_id(participant.conference_id)
        user = self.Users.get_by('id',participant.user_id)
        participants = []
        if 'participants' in conf:
            participants = conf['participants']
        participants.append({"name":user['name'], "role":user['role'], "phone":user['phone'], "user_leg": participant.user_leg})
        self.update({"participants": participants}, participant.conference_id)