from flask import Flask, request, Response, json;
from flask_jwt_extended import JWTManager;
from sqlalchemy import func,desc;

from roleDecorator import roleCheck
from configuration import Configuration
from models import database,Product,ProductOrder,Category;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

jwt = JWTManager ( application );

@application.route("/productStatistics", methods=["GET"])
@roleCheck(role="admin")
def productStatistics():
    if request.headers.get('Authorization') == None:
        return Response(json.dumps({"msg": "Missing Authorization Header"}), status=401);

    statistics = database.session.query(
        Product.name, func.sum(ProductOrder.requested), func.sum(ProductOrder.requested-ProductOrder.received)
    ).join(Product.product_orders).group_by(Product.id).all(); #isouter=True je za LEFT JOIN,u slucaju da je potrebno

    statistics = [{"name":product[0],"sold":int(product[1]) if product[1]!=None else 0,"waiting":int(product[2]) if product[2]!=None else 0} for product in statistics]

    print(f"Product statistics = {str(statistics)}", flush=True);

    return Response(json.dumps({"statistics": statistics }), status=200);

@application.route("/categoryStatistics", methods=["GET"])
@roleCheck(role="admin")
def categoryStatistics():
    if request.headers.get('Authorization') == None:
        return Response(json.dumps({"msg": "Missing Authorization Header"}), status=401);

    statistics = database.session.query(
        Category.name, func.sum(ProductOrder.requested).label("requested")
    ).join(Category.products, isouter=True).join(Product.product_orders, isouter=True).group_by(Category.id).order_by ( desc ( "requested" ), Category.name ).all();
    # isouter=True ide u oba join-a ako je potreban LEFT JOIN

    stats = [{"name":category[0],"sold":int(category[1]) if category[1]!=None else 0 } for category in statistics]
    statistics = [ category[0] for category in statistics];
    print(f"Category statistics = {str(stats)}", flush=True);

    return Response(json.dumps({"statistics": statistics }), status=200);


if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5005 );