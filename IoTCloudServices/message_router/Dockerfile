FROM python:3.11.1
COPY ./code /etc/usr/src/app
WORKDIR /etc/usr/src/app
RUN pip install -r requirements.txt
CMD ["python", "message_router.py"]