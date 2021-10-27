FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/amqp_setup.py .
COPY src/app.py .
CMD ["python", "./app.py"]
