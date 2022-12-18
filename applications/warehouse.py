from flask import Flask, request, Response, json;
from flask_jwt_extended import JWTManager;
from redis import Redis;
import io;
import csv;

from roleDecorator import roleCheck
from configuration import Configuration
from models import database

application = Flask ( __name__ );
application.config.from_object ( Configuration );

jwt = JWTManager ( application );

@application.route ( "/update", methods = ["POST"] )
@roleCheck ( role = "warehouseman" )
def update ( ):

    if request.headers.get('Authorization')==None:
        return Response ( json.dumps( { "msg" : "Missing Authorization Header" } ), status = 401);

    file = request.files.get("file", None);

    if file is None :
        return Response(json.dumps({"message": "Field file is missing."}), status=400);

    content = file.stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);

    products = [];
    index = 0;
    for row in reader:
        if len(row)<4:
            return Response(json.dumps( { "message" : f"Incorrect number of values on line {index}."} ), status=400);
        try:
            if int(row[2]) <= 0:
                return Response(json.dumps( { "message" : f"Incorrect quantity on line {index}."} ), status=400);
        except ValueError:
            return Response(json.dumps( { "message" : f"Incorrect quantity on line {index}."} ), status=400);

        try:
            if float(row[3]) <= 0:
                return Response(json.dumps( { "message" : f"Incorrect price on line {index}."} ), status=400);
        except ValueError:
            return Response(json.dumps( { "message" : f"Incorrect price on line {index}."} ), status=400);

        product = { "categories":row[0], "name":row[1], "deliveryQuantity": int(row[2]), "deliveryPrice": float(row[3])}
        products.append(product);
        index += 1;

    with Redis ( host = Configuration.REDIS_HOST ) as redis:
        for product in products:
            redis.rpush ( Configuration.REDIS_PRODUCTS_LIST, json.dumps(product) );

    return Response ( status = 200 );

@application.route ( "/products", methods = ["GET"] )
@roleCheck ( role = "warehouseman" )
def products ( ):
    with Redis(host=Configuration.REDIS_HOST) as redis:
        bytesList = redis.lrange(Configuration.REDIS_PRODUCTS_LIST, 0, 0);
        if (len(bytesList) != 0):
            product = bytesList[0].decode("utf-8");
            return json.loads(product)["categories"];
        else:
            return "No products";

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5003 );