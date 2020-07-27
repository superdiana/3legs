import argparse
import os
import sys
from os.path import join, dirname
from dotenv import load_dotenv
from os import environ
from flask import Flask

if not os.path.isfile(".env"):
    option = input("There is no .env file. Do you want to create it (y/n): ")
    if option.lower() == "y" or option.lower() == "yes":
        try:
            env = open(".env","a")
            print("DATA\n")
            option = input("What DataEngine do you prefer?: sqlalchemy/firebase (firebase by default): ")
            if option != "sqlalchemy":
                env.write('DATABASE_ENGINE="{0}"'.format('firebase')+"\n")
                option = input("Path to the firebase private key file: ")
                env.write('FIREBASE_PRIVATE_KEY="{0}"'.format(option)+"\n")
            else:
                env.write('DATABASE_ENGINE="{0}"'.format('sqlalchemy')+"\n")
                option = input('Enter the connection string. Default sqlite:///3legsapp.db : ')
                env.write('SQLALCHEMY_DATABASE_URI="{0}"'.format("sqlite:///3legsapp.db" if option in [None,''] else option)+"\n")
            print("APPLICATION\n")
            option = input("Enter your site url. E.g. http://localhost (default): ")
            env.write('SITE_URL="{0}"'.format('http://localhost' if option in [None,''] else option)+"\n")
            print("AUTHENTICATION\n")
            option = input('This site uses Google Sign In. Enter the client ID here: ')
            env.write('GOOGLE_CLIENT_ID="{0}"'.format(option)+"\n")
            print("NEXMO - VOICE API\n")
            option = input("Enter the Application ID: ")
            env.write('NEXMO_APPLICATION_ID="{0}"'.format(option)+"\n")
            option = input("Enter the PRIVATE KEY: ")
            env.write('NEXMO_PRIVATE_KEY="{0}"'.format(option)+"\n")
            print("NEXMO - GENERAL\n")
            option = input("Enter the API KEY: ")
            env.write('NEXMO_API_KEY="{0}"'.format(option)+"\n")
            option = input("Enter the API SECRET: ")
            env.write('NEXMO_API_SECRET="{0}"'.format(option)+"\n")
            option = input("Enter the NEXMO NUMBER: ")
            env.write('NEXMO_NUMBER="{0}"'.format(option)+"\n")
            print('Options saved successfully. Remember you can edit your .env file later if you want')
        except IOError as err:
            print("There was an error trying to create the .env file: {0}".format(err))
        finally:
            env.close()
    else:
        print("For creating users, .env definition is a requirement. Bye")
        sys.exit()

#get environment vars
envpath = join(dirname(__file__),"./.env")
load_dotenv(envpath)

#we define flask app just to stablish a context - necesary for using the flask sqlalchemy
app = Flask(__name__)

if environ.get("DATABASE_ENGINE") == "firebase":
    from models.firebase import users, User
elif environ.get("DATABASE_ENGINE") == "sqlalchemy":
    database_uri = environ.get("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    from models.sqlengine import db, users, User
    db.init_app(app)
    if 'sqlite' in database_uri:
        dbfile = database_uri.strip('sqlite:///') 
        if not os.path.isfile(dbfile):
            print('Sqlite DB File is not present. Creating...')
            with app.app_context():
                db.create_all()

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers()

parser_admin = subparser.add_parser('create')
parser_admin.add_argument('role', nargs='?', help='Admin creation')
parser_admin.set_defaults(parser='create')

args = parser.parse_args()

if vars(args) == {}:
    parser.print_help()
    sys.exit()

if args.parser == 'create':
    if(args.role == 'admin'):
        name = input('Insert the name: ')
        role = 'administrator'
        email = input('Insert the email: ')
        phone = input('Insert the phone: ')
        status = "active"
        #We use app context, Because we are using flask sqlalchemy and not sqlalchemy individually
        #But if we put from both doesn't bad just happends
        #if environ.get("DATABASE_ENGINE") == "sqlalchemy":
        with app.app_context():
            Users = users()
            Users.add(User(name=name, role=role, email=email, phone=phone, status=status))
    elif(args.role == 'user'):
        print('Hi: user')
    else:
        print('Invalid role')
