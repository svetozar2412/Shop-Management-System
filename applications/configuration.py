from datetime import timedelta;
import os;

databaseUrl = os.environ["DATABASE_URL"];

class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/shop";
    REDIS_HOST = "redis";
    REDIS_PRODUCTS_LIST = "products";
    JWT_SECRET_KEY = "JWT_SECRET_KEY";
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);

