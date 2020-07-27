from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#Model Definitions
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)

class Conference(db.Model):
    __tablename__ = 'conferences'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    audio = db.Column(db.String, nullable=True)
    date = db.Column(db.Date, nullable=True)
    conference_uuid = db.Column(db.String, nullable=True)
    
class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    conference_id = db.Column(db.Integer, db.ForeignKey('conferences.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_leg = db.Column(db.String, nullable=True)

#Models Allows use methods with the same names or params of Other Engine
class ModelController:
    def __init__(self, model):
        global db
        self.model = model
        self.session = db.session
    def get_by(self, field, value, single=True):
        if field != "id":
            item = self.model.query.filter(getattr(self.model,field).like("{0}".format(value)))
            if single:
                return item.first().__dict__ if item != None and (item.first() is not None) else None
            else:
                items = []
                for it in item.all():
                    items.append(it.__dict__)
                return items if items != None else None
        else:
            item = self.model.query.get(value)
            return item.__dict__ if item != None else None
    def filterby(self, filters,single=True):
        query = self.model.query
        for field, value in filters.items():
            query = query.filter(getattr(self.model,field).like("{0}".format(value)))
        item = query
        if single:
            return item.first().__dict__ if item != None else None
        else:
            items = []
            for it in item.all():
                items.append(it.__dict__)
            return items if items != None else None
        
    def add(self, model):
        self.session.add(model)
        self.session.commit()
    def update(self, data, id):
         item = self.session.query(self.model).get(id)
         for key, value in data.items():
             setattr(item, key, value)
         self.session.commit()
    def delete(self, id):
        item = self.session.query(self.model).get(id)
        self.session.delete(item)
        self.session.commit()
    def get_all(self):
        records = self.model.query.all()
        items = []
        for record in records:
            items.append(record.__dict__)
        if len(items) > 0:
            return items
        else:
            return None

#Users
class users(ModelController):
    def __init__(self):
        super().__init__(User)
#Conferences and participants
class conferences(ModelController):
    def __init__(self):
        self.participants = []
        self.submodel = Participant
        super().__init__(Conference)
    def add(self, model):
        from datetime import datetime
        model.date = datetime.fromisoformat(model.date)
        super().add(model)
    def get_by_name(self, name):
        self.participants = []
        conference = self.model.query.filter_by(name=name).first().__dict__
        #parts = self.submodel.query.filter_by(conference_id=conference.id).all()
        #parts = self.submodel.query(User.name, User.phone, User.role, Participant.user_leg).join(User).filter_by(conference_id=conference.id).all()
        parts = self.session.query(User).join(Participant).filter_by(conference_id=conference["id"]).all()
        for part in parts:
            self.participants.append(part.__dict__)
        conference["participants"] = self.participants
        return conference
    def get_all(self):
        conferences = super().get_all()
        if conferences is not None:
            for conference in conferences:
                participants = []
                parts = self.session.query(User, Participant).join(Participant).filter_by(conference_id=conference["id"]).all()
                for part in parts:
                    part_user = part[0].__dict__
                    part_part = part[1].__dict__
                    part_user["user_leg"] = part_part["user_leg"]
                    participants.append(part_user)
                conference["participants"] = participants
            return conferences
        else:
            return None
    def add_participant(self, participant):
        self.session.add(participant)
        self.session.commit()