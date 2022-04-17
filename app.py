from flask import Flask, render_template,request
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from openpyxl import load_workbook
import sqlite3
import utils
from nltk.tokenize import word_tokenize
import nltk
from statistics import mean

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
    f = request.files['file'] #File input
    structured=request.form.get('structure')
    if not f:
        return "No file attached"

    global filename
    filename=f.filename #changing global value of filename

    path='{}/{}'.format('static',filename)
    f.save(path)
    x=path.split('.')[-1]
    global filename_for_database
    filename_for_database='db/'+filename.replace(x,'db') #changing global value of filename_for_database

    #reading filedata start
    if x=='xlsx':
        new_wb = load_workbook(path)
        Dataframe = pd.read_excel(new_wb,engine='openpyxl',index_col=0,)
    elif x=='csv':
        Dataframe = pd.read_csv(path, encoding = "ISO-8859-1")
    else:
        return('Please upload the file in xlsx or csv only')
    #reading filedata end

    list_of_columns=list(Dataframe.columns) #getting columns from dataset
    
    #checking for data for insights
    data_report={'review':False,'order-status':False}

    # Data preprocessing and identifying columns in dataset START
    if 'product name' not in list_of_columns and 'Product Name' not in list_of_columns and 'name' not in list_of_columns and 'Name' not in list_of_columns:
        product_name=utils.check_product_name(list_of_columns=list_of_columns)
        Dataframe.rename(columns={product_name:'product_name'}, inplace=True)
    else:
        possible_values=['product name' , 'Product Name' ,'name', 'Name']
        for values in possible_values:
            Dataframe.rename(columns={values:'product_name'}, inplace=True)
    if 'product image' not in list_of_columns and 'Product Image' not in list_of_columns and 'image' not in list_of_columns and 'Image' not in list_of_columns:
        product_image=utils.check_product_image(list_of_columns=list_of_columns)
        Dataframe.rename(columns={product_image:'product_image'}, inplace=True)
    else:
        possible_values=['product image' , 'Product Image', 'image' , 'Image']
        for values in possible_values:
            Dataframe.rename(columns={values:'product_image'}, inplace=True)
    if 'review text' not in list_of_columns and 'Reviews' not in list_of_columns and 'Review Text' not in list_of_columns and 'reviews' not in list_of_columns and 'review.text' not in list_of_columns:
        review_text=utils.check_review_text(list_of_columns=list_of_columns)
        if review_text:
            Dataframe.rename(columns={review_text:'review_text'}, inplace=True)
            data_report['review']=True
    else:
        possible_values=['review text','Reviews','Review Text','reviews','review.text']
        for values in possible_values:
            Dataframe.rename(columns={values:'review_text'}, inplace=True)
        data_report['review']=True
    if 'shipping.date' not in list_of_columns and 'shipping date' not in list_of_columns and 'Shipping Date' not in list_of_columns:
        shipping_date=utils.check_shipping_date(list_of_columns=list_of_columns)
        if shipping_date:
            Dataframe.rename(columns={shipping_date:'shipping_date'}, inplace=True)
    else:
        possible_values=['shipping.date', 'shipping date', 'Shipping Date']
        for values in possible_values:
            Dataframe.rename(columns={values:'shipping_date'}, inplace=True)
    if 'Order Status' not in list_of_columns and 'order.status' not in list_of_columns and 'order status' not in list_of_columns:
        order_status=utils.check_order_status(list_of_columns=list_of_columns)
        if order_status:
            Dataframe.rename(columns={shipping_date:'order_status'}, inplace=True)
            data_report['order-status']=True
    else:
        possible_values=['Order Status','order.status','order status']
        for values in possible_values:
            Dataframe.rename(columns={values:'order_status'}, inplace=True)
        data_report['order-status']=True
    # Identifying columns in dataset END
    con=sqlite3.connect(filename_for_database) #connecting to the database
    cursor=con.cursor()

    for column in list_of_columns:
        final_name=column.lower().replace(" ","_")
        final_name=final_name.lower().replace("(","_")
        final_name=final_name.lower().replace(")","_")
        Dataframe.rename(columns={column:final_name}, inplace=True)
    #Data preprocessing END
    # Dataframe.to_sql(name='Dataset',con=con,if_exists='replace') # Dataset converted to RDBMS table

    # con.commit()
    
    cursor.execute('select "product_name" from Dataset;')
    result = cursor.fetchall()
    global products
    products=set(product[0] for product in result) # List of products fetched to be listed on page
    if structured=='structured':
        return render_template('check.html', products=list(products), final_report=data_report, db=filename_for_database, structured=True)
    else:
        return render_template('check.html', products=list(products), final_report=data_report, db=filename_for_database)

@app.route('/get-insights', methods=['GET','POST'])
def insights():
    #called for insights of products
    global filename_for_database
    product=str(request.form.get('products'))
    products=(product,)
    Reviews=request.form.get('review')
    order_status=request.form.get('order_status')
    #For unstructured dataset Reviews are listed based on the result of sentiment analysis
    if Reviews=='True':
        filename_for_database="db/Datafiniti_Amazon_Consumer_Reviews_of_Amazon_Products_May19.db"
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

    #For structured dataset OrderStatuses are listed:
    if order_status=='True':
        filename_for_database="db/DataCoSupplyChainDataset.db"
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
    db=request.form.get("db")
    con=sqlite3.connect(db) #connecting to the database
    cursor=con.cursor()
    words_in_statement = word_tokenize(statement)
    pos=nltk.pos_tag(words_in_statement)
    possible_columns=[]
    time=[]
    verb_possibility='no'
    for i in pos:
        if i[1]=='VB'or i[1]=='VBD' or i[1]=='VBG' or i[1]=='VBN' or i[1]=='VBP' or i[1]=='VBZ':
            verb_possibility=i[0]
        if i[1]=='NN' or i[1]=='NNP' or i[1]=='NNS':
            if verb_possibility!='no':
                possible_columns.append(verb_possibility)
            verb_possibility='no'
            possible_columns.append(i[0])
        if i[1]=='CD':
            verb_possibility='no'
            time.append(int(i[0]))
        if i[1]=='IN' or i[1]=='PRP':
            verb_possibility='no'
    date_column=[]
    x=cursor.execute('SELECT * FROM Dataset')
    columns=[]
    for column in x.description:
            columns.append(column[0])
    cursor.execute('SELECT DISTINCT product_name FROM Dataset')
    data=cursor.fetchall()
    pro={}
    vals={}
    for i in possible_columns:
        if len(i)>1:
            vals[i]=[]
            pro[i]=[]
            for column in columns:
                if i.lower() in column.lower():
                    vals[i].append(column)
            if vals[i]==[]:
                del vals[i]
        
            for product in data:
                if i.lower() in product[0].lower():
                    pro[i].append(product[0])
            if pro[i]==[]:
                del pro[i]
            val=list(pro.values())
    product=[]
    common_find=None
    if len(pro)>1:
        for i in range(len(pro)-1):
            common_find=utils.common_member(val[i], val[i+1])

        if common_find==None:
            for i in range(len(pro)):
                product.append(val[i])
        else:
            common_find=list(common_find)

    for i in columns:
        if 'date' in i.lower():
            date_column.append(i)

    date_columns=str(date_column[0])
    if vals and common_find:
        for i in vals.values():
            v=i[0]
            print (i,v)
        final_details={}
        data_chart=[]
        if time!=[]:
            for i in range(min(time),max(time)+1):
                    if i not in time:
                        time.append(i)
        rows=[]
        
        for pros in common_find:
            chart_rows=[]
            
            cursor.execute('SELECT '+v+', '+date_columns+' FROM Dataset WHERE product_name= ? ',(pros,))
            data=list(cursor.fetchall())
            year_wise={}
            for details in data:
                date=pd.to_datetime(details[1])
                if time != []:
                    if date.year not in time:
                        data.remove(details)

                        continue
            
                if date.year in year_wise:
                    year_wise[date.year].append(details[0])
                else:
                    year_wise[date.year]=[details[0]]
            for i in year_wise.keys():
                year_under_consideration=year_wise[i]
                finall=sum(year_under_consideration) / len(year_under_consideration)
                year_wise[i]=finall
            chart_rows.append(pros)
            no_time=False
            if time!=[]:
                for i in time:
                    if i not in list(year_wise.keys()):
                        year_wise[i]=0
                print(year_wise)
            else:
                no_time=True
            year_wise_sorted={}
            while year_wise!={}:
                year_wise_sorted[min(year_wise.keys())]=year_wise[min(year_wise.keys())]
                year_wise.pop(min(year_wise.keys()))
            print(year_wise_sorted)
            for i in year_wise_sorted.keys():
                chart_rows.append(year_wise_sorted[i])
                if no_time==True:
                    time.append(i)
            
            final_details[pros]=year_wise
            rows.append(chart_rows)
        print(time)
        time_sort=sorted(time)
        return {'columns':vals,'products':final_details,'time':time_sort,'rows':rows}

    elif vals and not common_find and pro:
        for i in vals.values():
            v=i[0]
        final_details={}
        if time!=[]:
            for i in range(min(time),max(time)+1):
                    if i not in time:
                        time.append(i)
        rows=[]
        for pros in pro.values():
            chart_rows=[]
            cursor.execute('SELECT '+v+', '+date_columns+' FROM Dataset WHERE product_name= ? ',(pros[0],))
            data=list(cursor.fetchall())
            
            year_wise={}
            for details in data:
                date=pd.to_datetime(details[1])
                if time!=[]:
                    if date.year not in time:
                        data.remove(details)
                        continue
            
                if date.year in year_wise:
                    year_wise[date.year].append(details[0])
                else:
                    year_wise[date.year]=[details[0]]
                        
            for i in year_wise.keys():
                year_under_consideration=year_wise[i]
                finall=sum(year_under_consideration) / len(year_under_consideration)
                year_wise[i]=finall
            no_time=False
            if time!=[]:
                for i in time:
                    if i not in list(year_wise.keys()):
                        year_wise[i]=0
                print(year_wise)
            else:
                no_time=True
            year_wise_sorted={}
            while year_wise!={}:
                year_wise_sorted[min(year_wise.keys())]=year_wise[min(year_wise.keys())]
                year_wise.pop(min(year_wise.keys()))
            print(year_wise_sorted)
            chart_rows.append(pros[0])
                
            for i in year_wise_sorted.keys():
                chart_rows.append(year_wise_sorted[i])
                if no_time==True:
                    time.append(i)
            
            final_details[pros[0]]=year_wise
            rows.append(chart_rows)
        print(time)
        time_sort=sorted(time)
        return {'columns':vals,'products':final_details,'time':time_sort,'rows':rows}
    else:
        return {'columns':None,'products':None,'time':None,'rows':None}


if __name__ == '__main__':
    app.run(debug=True)