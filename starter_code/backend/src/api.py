import os
import json
from os import environ as env
from flask import Flask, request, jsonify, abort,url_for, session, redirect, render_template

from urllib.parse import quote_plus, urlencode
from sqlalchemy import exc
from flask_cors import CORS
from dotenv import find_dotenv, load_dotenv
from authlib.integrations.flask_client import OAuth
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key=env.get("APP_SECRET_KEY")
setup_db(app)
CORS(app)

oauth = OAuth(app)


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

@app.route('/')
def home():
    return jsonify({
        'success': True,
        'message': 'welcome to the coffee shop'

    })

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback",_external=True)
    )

@app.route("/callback", methods=["GET","POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"]=token
    return redirect("/")




# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def drinks():
    drinks = Drink.query.all()


    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks],
    }), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drink_details(payload):
    if request.method == "GET":
        drinks = Drink.query.all()

        
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks],
        }), 200

#AssertionError: expected response to have status code 200 but got 401
'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(payload):
    data = request.get_json()
    if 'title' and 'recipe' not in data:
        abort(422)

    try:
        title = data['title']

        recipe = data['recipe']
        if type(recipe) is dict:
            recipe = [recipe]

        drink = Drink(title=title, recipe=json.dumps(recipe))

        drink.insert()

        

        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        }), 200
    except:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    try:
        data = request.get_json()
        if 'title' in data:
            drink.title = data['title']

        if 'recipe' in data:
            drink.recipe = json.dumps(data['recipe'])

        drink.update()


        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        }), 200


    except:
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    #check if the drink to be deleted exist
    if not drink:
        abort(404)

    try:
    #if it exist delete it
        drink.delete()

        return jsonify({
            'success': True,
            'deleted_Drink': id,
        }), 200
    except:
        abort(422)




# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'Bad Request'
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'Unauthorized'
    }), 401

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Not Found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'Method Not Allowed'
    }), 405

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }), 500

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code