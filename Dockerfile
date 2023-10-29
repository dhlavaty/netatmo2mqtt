FROM python:3.9.18-alpine

WORKDIR /usr/src/app

COPY netatmo2mqtt.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
 && echo "*/10 * * * * python /usr/src/app/netatmo2mqtt.py" >> /var/spool/cron/crontabs/root

CMD ["crond", "-f", "-l", "8"]

# docker build . --tag dhlavaty/netatmo2mqtt
#
# dockersh dhlavaty/netatmo2mqtt
