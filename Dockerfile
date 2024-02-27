FROM python:3.12.2-slim
COPY . /app 
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app
CMD [ "python" "index.py" ]
