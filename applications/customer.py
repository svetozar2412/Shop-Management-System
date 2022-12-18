from flask import Flask, request, Response, json;
from flask_jwt_extended import JWTManager, get_jwt_identity;
from roleDecorator import roleCheck;
from configuration import Configuration;
from models import database, Category, ProductCategory, Product, Order, ProductOrder;
from sqlalchemy import and_,func,desc;

application = Flask(__name__);
application.config.from_object(Configuration);

jwt = JWTManager(application);

@application.route("/search", methods=["GET"])
@roleCheck(role="customer")
def search():
    if request.headers.get('Authorization') == None:
        return Response(json.dumps({"msg": "Missing Authorization Header"}), status=401);

    name = request.args.get("name");
    if name == None:
        name = ""
    category = request.args.get("category");
    if category == None:
        category = ""

    categories = database.session.query(Category.name).filter(and_(
        Category.name.like(f"%{category}%"),
        Category.id == ProductCategory.categoryId,
        ProductCategory.productId == Product.id,
        Product.name.like(f"%{name}%")
    )).distinct().all();
    categories = [category1.name for category1 in categories];

    products = Product.query.join(Product.categories).filter(
        and_(Category.name.like(f"%{category}%"), Product.name.like(f"%{name}%"))).all();
    products = [
        {"categories": [category.name for category in product.categories], "id": product.id, "name": product.name,
         "price": product.price, "quantity": product.quantity} for product in products]

    print(f"Search = {str(products)}",flush=True)

    return Response(json.dumps({"categories": categories, "products": products}), status=200);

@application.route("/order", methods=["POST"])
@roleCheck(role="customer")
def order():
    if request.headers.get('Authorization') == None:
        return Response(json.dumps({"msg": "Missing Authorization Header"}), status=401);

    requests = request.json.get("requests", None);

    if requests == None:
        return Response(json.dumps({"message": "Field requests is missing."}), status=400);

    print(f"Before={requests}",flush=True)

    index = 0;
    products = [];
    for req in requests:
        print(f"Request={req}", flush=True)

        if "id" not in req:
            return Response(json.dumps({"message": f"Product id is missing for request number {index}."}), status=400);

        if "quantity" not in req:
            return Response(json.dumps({"message": f"Product quantity is missing for request number {index}."}),
                            status=400);
        id = req["id"];
        quantity = req["quantity"];

        try:
            if int(id) <= 0:
                return Response(json.dumps({"message": f"Invalid product id for request number {index}."}), status=400);
        except ValueError:
            return Response(json.dumps({"message": f"Invalid product id for request number {index}."}), status=400);

        try:
            if int(quantity) <= 0:
                return Response(json.dumps({"message": f"Invalid product quantity for request number {index}."}),
                                status=400);
        except ValueError:
            return Response(json.dumps({"message": f"Invalid product quantity for request number {index}."}),
                            status=400);

        product = Product.query.filter(Product.id == id).first();

        if (not product):
            return Response(json.dumps({"message": f"Invalid product for request number {index}."}), status=400);

        products.append({"product": product, "requested": quantity});

        index += 1;

    identity = get_jwt_identity();
    order = Order(customer=identity, price=0, status="COMPLETE");
    database.session.add(order);
    database.session.commit();

    sum = 0;
    pending = False;
    for product in products:
        #PROBLEM JE AKO POSTOJI VISE NARUDZBINA ISTOG PROIZVODA
        product_order = ProductOrder(orderId=order.id, productId=product["product"].id, requested=product["requested"],
                                     received=product["requested"] if product["requested"] <= product[
                                         "product"].quantity else product["product"].quantity,
                                     presentPrice=product["product"].price);
        sum += product["requested"] * product["product"].price;
        if (not pending) and product["requested"] > product["product"].quantity:
            print(f"requested = {product['requested']}, quantity = {product['product'].quantity}", flush=True);
            pending = True;

        product["product"].quantity = product["product"].quantity-product["requested"] if product["requested"] <= product[
                                         "product"].quantity else 0;
        print(f"Product after update = {str(product['product'])}",flush=True)
        database.session.add(product_order);
        database.session.commit();


    order.price = sum;
    if not pending:
        print("order.status = COMPLETE", flush=True);
        order.status = "COMPLETE";
    else:
        print("order.status = PENDING", flush=True);
        order.status = "PENDING";

    database.session.commit();

    return Response(json.dumps({"id": order.id}), status=200);

@application.route("/status", methods=["GET"])
@roleCheck(role="customer")
def status():
    if request.headers.get('Authorization') == None:
        return Response(json.dumps({"msg": "Missing Authorization Header"}), status=401);

    orders = Order.query.filter(
        Order.customer == get_jwt_identity()).all();
    orders = [
        {"products": [
            {"categories": [category.name for category in product_order.product.categories], "name": product_order.product.name,
             "price": product_order.presentPrice, "received": product_order.received, "requested": product_order.requested } for product_order in order.product_orders],
         "price": order.price, "status": order.status, "timestamp": order.timestamp.isoformat() } for order in orders]

    print(f"Products={json.dumps({'orders': orders })}",flush=True);
    return Response(json.dumps({"orders": orders }), status=200);


if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5004);
