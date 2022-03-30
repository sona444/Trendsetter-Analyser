import base64
import io
import tempfile
from flask import Flask, render_template,request
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import numpy as np
from minio import Minio
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
import boto3
from minio.error import S3Error
from botocore.client import Config

load_dotenv()

LOCAL_FILE_PATH = os.environ.get('LOCAL_FILE_PATH')
ACCESS_KEY = os.environ.get('MINIO_ROOT_USER')
SECRET_KEY = os.environ.get('MINIO_ROOT_PASSWORD')
MINIO_API_HOST = "http://localhost:9000"
MINIO_CLIENT = Minio("localhost:9000", access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://sonakshi:sonakshi@localhost:5432/trendsetter' #postgresql://{username}:{password}@{hostname}:{port}/{dbname}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = '/trendsetter'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import datasets


def uploadFileToS3(filename,file,path):
    try:
        s3=boto3.resource('s3',
            endpoint_url=MINIO_API_HOST,
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin',
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        s3.Bucket('trendsetter').upload_file(path,filename)
        return "success"
    except S3Error as err:
        print(err)

def GetPath_from_S3(name):
    try:
        s3 = boto3.resource('s3',
        endpoint_url='http://127.0.0.1:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        config=Config(signature_version='s3v4'),
        region_name='us-east-1')
        path='{}/{}'.format(tempfile.gettempdir(),name)
        data = io.BytesIO()
        print(data)
        s3.Bucket('trendsetter').download_file(str(name),path)
        encoded_img_data = base64.b64encode(data.getvalue())
        return encoded_img_data.decode('utf-8')
    except S3Error as err:
        print("err")

nltk.download('vader_lexicon')
# two decorators, same function
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-dataset', methods=['GET','POST'])
def main():
    if request.method == 'POST':
        f = request.files['file']
        filename=f.filename
        path='{}/{}'.format(tempfile.gettempdir(),filename)
        f.save(path)
        s=uploadFileToS3(filename,f,path)
        breakpoint()
        df = pd.read_excel(
            "s3://trendsetter/"+filename,
            storage_options={
                "key": "minioadmin",
                "secret": "minioadmin",
                "client_kwargs": {"endpoint_url": 'http://127.0.0.1:9000'}
            }
        )
        breakpoint()
        print(df)
        # img_path=GetPath_from_S3(str(filename))
        # breakpoint()
        # dataset=datasets(dataset_name="recent",dataset_link=img_path)
        # db.session.add(dataset)
        # db.session.commit()
        return "success"



@app.route('/check-sentiment')
def check(jsondata):
    statement=jsondata.get('statement')
    print(statement)
    sid=SentimentIntensityAnalyzer()
    sa=sid.polarity_scores(str(statement))
    for k in sa:
            print(k,sa[k])
    return sa

if __name__ == '__main__':
    app.run(debug=True)