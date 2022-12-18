from flask import Flask, request, Response, jsonify,json;
from configuration import Configuration;
from models import database, User, Role;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_;
import re;
from adminDecorator import roleCheck;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

#potrebno je namestiti BOOLEAN tip u JSON objektu
@application.route ( "/register", methods = ["POST"] )
def register ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );
    forename = request.json.get ( "forename", "" );
    surname = request.json.get ( "surname", "" );
    isCustomer = request.json.get ( "isCustomer");

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;
    forenameEmpty = len ( forename ) == 0;
    surnameEmpty = len ( surname ) == 0;
    isCustomerEmpty = isCustomer == None;

    print(f"isCustomer={isCustomer}", flush = True);

    if (forenameEmpty):
        return Response(json.dumps({"message":"Field forename is missing."}), status=400);
    if (surnameEmpty):
        return Response(json.dumps({"message":"Field surname is missing."}), status=400);
    if (emailEmpty):
        return Response(json.dumps({"message":"Field email is missing."}), status=400);
    if (passwordEmpty):
        return Response(json.dumps({"message":"Field password is missing."}), status=400);
    if( isCustomerEmpty ):
        return Response(json.dumps({"message":"Field isCustomer is missing."}), status=400);

    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b';
    if not re.fullmatch(email_regex, email):
        return Response(json.dumps({"message":"Invalid email."}), status=400);

    regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$";
    pattern = re.compile(regex);
    validPassword = re.search(pattern, password);
    if not validPassword:
        return Response(json.dumps({"message":"Invalid password."}), status=400);

    exists = User.query.filter( User.email == email ).first() is not None;
    if exists:
        return Response(json.dumps({"message":"Email already exists."}), status=400);

    customerRole = Role.query.filter(Role.name == "customer").first();
    warehousemanRole = Role.query.filter(Role.name == "warehouseman").first();
    if isCustomer:
        user = User ( email = email, password = password, forename = forename, surname = surname, roleId = customerRole.id );
    else:
        user = User(email=email, password=password, forename=forename, surname=surname, roleId = warehousemanRole.id );

    database.session.add ( user );
    database.session.commit ( );

    return Response ( status = 200 );

jwt_instance = JWTManager (application);

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );

    emailEmpty = len ( email ) == 0;
    passwordEmpty = len ( password ) == 0;

    if (emailEmpty):
        return Response(json.dumps({"message": "Field email is missing."}), status=400);
    if (passwordEmpty):
        return Response(json.dumps({"message": "Field password is missing."}), status=400);

    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b';
    if not re.fullmatch(email_regex, email):
        return Response(json.dumps({"message": "Invalid email."}), status=400);

    user = User.query.filter ( and_ ( User.email == email, User.password == password ) ).first ( );

    if ( not user ):
        return Response(json.dumps({"message": "Invalid credentials."}), status=400);

    additionalClaims = {
            "forename": user.forename,
            "surname": user.surname,
            "role": [ str ( user.role ) ]
        #mozda treba isCustomer za magacionera i kupca da se doda
    }

    accessToken = create_access_token ( identity = user.email, additional_claims = additionalClaims );
    refreshToken = create_refresh_token ( identity = user.email, additional_claims = additionalClaims );

    # return Response ( accessToken, status = 200 );
    #return jsonify ( accessToken = accessToken, refreshToken = refreshToken );
    return Response(json.dumps({"accessToken": accessToken, "refreshToken":refreshToken}), status=200);

@application.route ( "/refresh", methods = ["POST"] )
@jwt_required ( refresh = True )
def refresh ( ):

    if request.headers.get('Authorization')==None:
        return Response ( json.dumps( { "msg" : "Missing Authorization Header" } ), status = 401);

    identity = get_jwt_identity ( );
    refreshClaims = get_jwt ( );

    additionalClaims = {
            "forename": refreshClaims["forename"],
            "surname": refreshClaims["surname"],
            "role": refreshClaims["role"]
        #mozda treba isCustomer za magacionera i kupca da se doda
    };

    #return Response ( jsonify( accessToken = create_access_token ( identity = identity, additional_claims = additionalClaims )), status = 200 );
    return Response(json.dumps({"accessToken": create_access_token ( identity = identity, additional_claims = additionalClaims )}), status=200);

@application.route ( "/delete", methods = ["POST"] )
@roleCheck ( role = "admin" )
def delete ( ):

    if request.headers.get('Authorization')==None:
        return Response ( json.dumps( { "msg" : "Missing Authorization Header" } ), status = 401);

    email = request.json.get("email", "");

    emailEmpty = len(email) == 0;

    if (emailEmpty):
        return Response(json.dumps({"message": "Field email is missing."}), status=400);

    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b';
    if not re.fullmatch(email_regex, email):
        return Response(json.dumps({"message": "Invalid email."}), status=400);

    exists = User.query.filter(User.email == email).first() is not None;
    print(f"exists={exists}", flush=True);
    if not exists:
        return Response(json.dumps({"message": "Unknown user."}), status=400);

    User.query.filter(User.email == email).delete();
    database.session.commit();

    return Response ( status = 200 );

@application.route ( "/", methods = ["GET"] )
def index ( ):
    return "Hello world!"

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5002 );