from flask import Flask, render_template,request
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from openpyxl import load_workbook
import sqlite3
import utils
from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
load_dotenv()

app = Flask(__name__)

filename=''
filename_for_database=''
products=set

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-dataset', methods=['GET','POST'])
def main():
    f = request.files['file']
    if not f:
        return "No file attached"

    global filename
    filename=f.filename #changing global value of filename

    path='{}/{}'.format('static/datasets',filename)
    f.save(path)
    x=path.split('.')[-1]
    print(path)
    global filename_for_database
    filename_for_database='db/'+filename.replace(x,'db') #changing global value of filename_for_database
    print(filename_for_database)
    if x=='xlsx':
        new_wb = load_workbook(path)
        Dataframe = pd.read_excel(new_wb,engine='openpyxl',index_col=0,)
    elif x=='csv':
        Dataframe = pd.read_csv(path, encoding = "ISO-8859-1")
    else:
        return('Please upload the file in xlsx or csv only')
    
    list_of_columns=list(Dataframe.columns)
    print(list_of_columns)
    data_report={'review':False,'order-status':False}

    if 'product name' not in list_of_columns and 'Product Name' not in list_of_columns and 'name' not in list_of_columns and 'Name' not in list_of_columns:
        product_name=utils.check_product_name(list_of_columns=list_of_columns)
        Dataframe.rename(columns={product_name:'product_name'}, inplace=True)
        print("Product name",product_name)
    else:
        possible_values=['product name' , 'Product Name' ,'name', 'Name']
        for values in possible_values:
            Dataframe.rename(columns={values:'product_name'}, inplace=True)
    if 'product image' not in list_of_columns and 'Product Image' not in list_of_columns and 'image' not in list_of_columns and 'Image' not in list_of_columns:
        product_image=utils.check_product_image(list_of_columns=list_of_columns)
        Dataframe.rename(columns={product_image:'product_image'}, inplace=True)
        print("Product image",product_image)
    else:
        possible_values=['product image' , 'Product Image', 'image' , 'Image']
        for values in possible_values:
            Dataframe.rename(columns={values:'product_image'}, inplace=True)
    if 'review text' not in list_of_columns and 'Reviews' not in list_of_columns and 'Review Text' not in list_of_columns and 'reviews' not in list_of_columns and 'review.text' not in list_of_columns:
        review_text=utils.check_review_text(list_of_columns=list_of_columns)
        if review_text:
            Dataframe.rename(columns={review_text:'review_text'}, inplace=True)
            data_report['review']=True
            print("Review Text",review_text)
    else:
        possible_values=['review text','Reviews','Review Text','reviews','review.text']
        for values in possible_values:
            Dataframe.rename(columns={values:'review_text'}, inplace=True)
        data_report['review']=True
    if 'shipping.date' not in list_of_columns and 'shipping date' not in list_of_columns and 'Shipping Date' not in list_of_columns:
        shipping_date=utils.check_shipping_date(list_of_columns=list_of_columns)
        if shipping_date:
            Dataframe.rename(columns={shipping_date:'shipping_date'}, inplace=True)
            print("Shipping Date",shipping_date)
    else:
        possible_values=['shipping.date', 'shipping date', 'Shipping Date']
        for values in possible_values:
            Dataframe.rename(columns={values:'shipping_date'}, inplace=True)
    if 'Order Status' not in list_of_columns and 'order.status' not in list_of_columns and 'order status' not in list_of_columns:
        order_status=utils.check_order_status(list_of_columns=list_of_columns)
        if order_status:
            Dataframe.rename(columns={shipping_date:'order_status'}, inplace=True)
            data_report['order-status']=True
            print("Order Status",order_status)
    else:
        possible_values=['Order Status','order.status','order status']
        for values in possible_values:
            Dataframe.rename(columns={values:'order_status'}, inplace=True)
        data_report['order-status']=True
    print(data_report)

    con=sqlite3.connect(filename_for_database) #connecting to the database
    cursor=con.cursor()

    for column in list_of_columns:
        final_name=column.lower().replace(" ","_")
        Dataframe.rename(columns={column:final_name}, inplace=True)

    # Dataframe.to_sql(name='Dataset',con=con,if_exists='replace')

    # con.commit()
    
    cursor.execute('select "product_name" from Dataset;')
    result = cursor.fetchall()
    global products
    products=set(product[0] for product in result)
    print(products)
    return render_template('check.html', products=list(products), final_report=data_report, db=filename_for_database)

@app.route('/get-insights', methods=['GET','POST'])
def insights():
    global filename_for_database
    
    
    product=str(request.form.get('products'))
    products=(product,)
    Reviews=request.form.get('review')
    order_status=request.form.get('order_status')
    if Reviews=='True':
        filename_for_database="Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products_May19.db"
        con=sqlite3.connect(filename_for_database) #connecting to the database
        cursor=con.cursor()
        cursor.execute('SELECT review_text FROM Dataset WHERE product_name = ?',products)
        data=cursor.fetchall()
        nltk.download('vader_lexicon')
        reviews={'neg':0,'pos':0}
        for review in data:
            sid=SentimentIntensityAnalyzer()
            sa=sid.polarity_scores(str(review))
            if sa['neg']>sa['pos']:
                reviews['neg']=reviews['neg']+1
            else:
                reviews['pos']=reviews['pos']+1
        return { 'review':reviews }

    if order_status=='True':
        filename_for_database="DataCoSupplyChainDataset.db"
        con=sqlite3.connect(filename_for_database) #connecting to the database
        cursor=con.cursor()
        cursor.execute('SELECT product_name, product_image, order_status FROM Dataset WHERE product_name = ?',products)
        data=cursor.fetchall()
        img=data[0][1]
        status={}
        for i in data:
            if i[2] in status.keys():
                status[i[2]]=status[i[2]]+1
            else:
                status[i[2]]=1
    return {'img':img, 'status':status}

@app.route('/get-query', methods=['GET','POST'])
def query_convert():
    statement=request.form.get('statement')
    Reviews=request.form.get('review')
    order_status=request.form.get('order_status')
    db=request.form.get("db")
    con=sqlite3.connect(db) #connecting to the database
    cursor=con.cursor()
    words_in_statement = word_tokenize(statement)
    pos=nltk.pos_tag(words_in_statement)
    print(pos)
    possible_columns=[]
    for i in pos:
        if i[1]=='NN' or i[1]=='NNP' or i[1]=='NNS':
            possible_columns.append(i[0])
    x=cursor.execute('SELECT * FROM Dataset')
    cursor.execute('SELECT product_name FROM Dataset')
    data=cursor.fetchall()
    similarity={}
    vals={}
    val=[]
    for i in possible_columns:
        vals={}
        for column in x.description:
            check=utils.similar(column[0], i)
            print(i,column[0],check)
            if check>=0.4:
                vals[column[0]]=check
        print(vals)
        if vals!={}:
            value_of_columns=list(vals.values())
            value=max(value_of_columns)
            position=value_of_columns.index(value)
            key=list(vals.keys())[position]
            similarity[i]=key
            val.append(value)
            resources={"column":True}
        pro={}
        removing_duplicates=[]
        similarity_products={}
        for product in data:
            if product[0] not in removing_duplicates:
                removing_duplicates.append(product[0])
                if i.lower() in product[0].lower():
                    pro[product[0]]=i
        if len(pro)>1:
            return {"products":pro}
        print(pro)
    print(pro,similarity_products)
    return{'check':True}



# def checked(jsondata):
#     statement=jsondata.get('statement')
#     print(statement)
#     sid=SentimentIntensityAnalyzer()
#     sa=sid.polarity_scores(str(statement))
#     for k in sa:
#             print(k,sa[k])
#     return sa

# if __name__ == '__main__':
#     app.run(debug=True)