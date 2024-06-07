FROM python:3.12.3
WORKDIR /app
COPY . .
CMD ["bash", "start.sh"]
