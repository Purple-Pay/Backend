FROM python:3.9-slim

RUN apt-get update && apt-get install -y libpq-dev gcc
RUN mkdir -p /usr/src/
RUN mkdir -p /var/log/purple_pay/
RUN chmod 777 /var/log/purple_pay/
WORKDIR /usr/src/

# Installing requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Adding remaining files
ADD . .

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/"
ENTRYPOINT ["/entrypoint.sh"]
#CMD ["python", "manage.py","runserver", "0.0.0.0:8000"]