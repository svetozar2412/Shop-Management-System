FROM python:3

RUN mkdir -p /opt/src/products
WORKDIR /opt/src/products

COPY applications/daemon.py ./daemon.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt
COPY applications/roleDecorator.py ./roleDecorator.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/products"

ENTRYPOINT ["python", "./daemon.py"]