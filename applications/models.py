from flask_sqlalchemy import SQLAlchemy;
from sqlalchemy.sql import func;

database = SQLAlchemy ( );

class ProductCategory ( database.Model ):
    __tablename__ = "productcategory";
    id = database.Column ( database.Integer, primary_key = True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "products.id" ), nullable = False );
    categoryId = database.Column ( database.Integer, database.ForeignKey ( "categories.id" ), nullable = False );

class ProductOrder ( database.Model ):
    __tablename__ = "productorder";
    id = database.Column ( database.Integer, primary_key = True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "products.id" ), nullable = False );
    orderId = database.Column ( database.Integer, database.ForeignKey ( "orders.id" ), nullable = False );

    product = database.relationship ( "Product", back_populates="product_orders");
    order = database.relationship ( "Order", back_populates="product_orders");

    requested = database.Column(database.Integer, nullable=False);
    received = database.Column(database.Integer, nullable=False);
    presentPrice = database.Column(database.Float, nullable=False);


class Product ( database.Model ):
    __tablename__ = "products";
    id = database.Column ( database.Integer, primary_key = True );
    name = database.Column ( database.String ( 256 ), nullable = False );
    price = database.Column(database.Float, nullable=False);
    quantity = database.Column(database.Integer, nullable=False);

    categories = database.relationship ( "Category", secondary = ProductCategory.__table__, back_populates = "products" );
    orders = database.relationship( "Order", secondary=ProductOrder.__table__, back_populates="products");

    product_orders = database.relationship("ProductOrder", back_populates="product");

    def __repr__ ( self ):
        return "({}, {}, {}, {}, {})".format ( self.id, self.name, self.price, self.quantity, self.categories );


class Category ( database.Model ):
    __tablename__ = "categories";
    id = database.Column ( database.Integer, primary_key = True );
    name = database.Column ( database.String ( 256 ), nullable = False );

    products = database.relationship ( "Product", secondary = ProductCategory.__table__, back_populates = "categories" );

    def __repr__ ( self ):
        return "({}, {})".format ( self.id, self.name );

class Order ( database.Model ):
    __tablename__ = "orders";
    id = database.Column(database.Integer, primary_key=True);

    customer = database.Column ( database.String(256), nullable = False );
    price = database.Column ( database.Float, nullable = False );
    status = database.Column ( database.String ( 256 ), nullable = False );
    timestamp = database.Column ( database.DateTime(timezone=True), default=func.now() );

    products = database.relationship("Product", secondary=ProductOrder.__table__, back_populates="orders");
    product_orders = database.relationship( "ProductOrder", back_populates="order");

    def __repr__ ( self ):
        return "({}, {}, {}, {}, {}, {})".format ( self.id, self.customer, self.price, self.status, self.timestamp, str(self.products));