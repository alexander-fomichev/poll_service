# pull official base image
FROM python:3.9-alpine
# set work directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN apk update \
    && apk add postgresql-dev gcc musl-dev python3-dev libffi-dev openssl-dev cargo
COPY ./requirements.txt .
RUN pip install -r requirements.txt
# copy project
COPY . .

# copy entrypoint.sh
COPY ./entrypoint.sh .

# RUN chmod +x /usr/src/app/entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

#EXPOSE 8000
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
