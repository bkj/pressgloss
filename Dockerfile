FROM alpine:latest
RUN apk update

RUN apk add py-pip
RUN apk add --no-cache python3-dev
RUN pip install --upgrade pip
RUN apk add --no-cache mariadb-dev build-base

WORKDIR /app
COPY . /app
RUN pip --no-cache-dir install -r requirements.txt
EXPOSE 5000

ENTRYPOINT []

CMD ["python3", "-m", "pressgloss", "--operation", "app"]
