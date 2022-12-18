FROM python:3

RUN mkdir -p /opt/src/products
WORKDIR /opt/src/products

COPY applications/migrate.py ./migrate.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]
