from redis import Redis;
from flask import json,Flask;
from configuration import Configuration;
from models import database,Product,Category,ProductCategory,Order,ProductOrder;
from sqlalchemy import and_, func;

application = Flask(__name__);
application.config.from_object(Configuration);

if __name__ == "__main__":
    database.init_app(application);
    while True:
        with application.app_context():
            try:
                with Redis(host=Configuration.REDIS_HOST) as redis:
                    result = redis.blpop(Configuration.REDIS_PRODUCTS_LIST, 0);
                    product = result[1].decode("utf-8");
                    product = json.loads(product);
                    print(str(product), flush=True);

                    prod = Product.query.filter( Product.name == product["name"]).first();
                    print(f"Product before = {str(prod)}", flush=True)

                    if prod is None:
                        prod = Product(name=product["name"],price=product["deliveryPrice"],quantity=product["deliveryQuantity"]);
                        database.session.add(prod);
                        database.session.commit();

                        categories = product["categories"].split("|");
                        for category in categories:
                            cat = Category.query.filter(Category.name == category).first();
                            if cat is None:
                                cat = Category(name=category);
                                database.session.add(cat);
                                database.session.commit();

                            cat_prod = ProductCategory(productId=prod.id,categoryId=cat.id);
                            database.session.add(cat_prod);
                            database.session.commit();
                    else:
                        cats = product["categories"].split("|");

                        categories_in_db = [ category.name for category in prod.categories];

                        if len(cats) == len(categories_in_db):
                            valid = True;
                            for c in cats:
                                if c not in categories_in_db:
                                    valid = False;
                                    break;
                            if valid:

                                prod.price = (prod.quantity * prod.price + product["deliveryQuantity"] * product["deliveryPrice"])/(prod.quantity + product["deliveryQuantity"])
                                prod.quantity += product["deliveryQuantity"];
                                database.session.commit();
                                print(f"Product after = {str(prod)}",flush=True)
                            else:
                                continue;

                        orders = ProductOrder.query.filter( and_ (ProductOrder.productId == prod.id, ProductOrder.received < ProductOrder.requested) ).\
                            join(ProductOrder.order).order_by( Order.timestamp ).all();

                        for order in orders:
                            print(f"Order={str(order.order)}", flush=True);
                            if order.requested-order.received <= prod.quantity:
                                prod.quantity -= order.requested - order.received;
                                order.received = order.requested;
                                order_for_status = Order.query.filter( Order.id == order.orderId).first();
                                pending_requests_from_same_order = database.session.query(func.count(ProductOrder.id)).filter( and_ (ProductOrder.orderId == order.orderId, ProductOrder.received < ProductOrder.requested)).scalar();
                                print(f"\n STILL PENDING = {str(pending_requests_from_same_order)} \n", flush=True)
                                if int(pending_requests_from_same_order) == 0:
                                    order_for_status.status = "COMPLETE";
                                    database.session.commit();
                            else:
                                order.received += prod.quantity;
                                prod.quantity = 0;
                                database.session.commit();
                                break;
            except Exception as e:
                print(f"Error={str(e)}");