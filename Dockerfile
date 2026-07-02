
FROM python:3.9-slim  

WORKDIR /app  

COPY . /app  

RUN pip install -r requirements.txt  

RUN python create_db.py

EXPOSE 5000  


CMD ["python", "app.py"]