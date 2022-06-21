from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
    
def common_member(a, b):
    a_set = set(a)
    b_set = set(b)
 
    if (a_set & b_set):
        return(a_set & b_set)
    else:
        return None

def check_product_name(list_of_columns):
    check={}
    for columns in list_of_columns:
        check[columns]=similar('Product Name',columns)
    print(check)
    fin_max = max(check, key=check.get)
    return fin_max

def check_product_image(list_of_columns):
    check={}
    for columns in list_of_columns:
        check[columns]=similar('Product Image',columns)
    print(check)
    fin_max = max(check, key=check.get)
    return fin_max    

def check_product_country(list_of_columns):
    check={}
    for columns in list_of_columns:
        check[columns]=similar('Order Country',columns)
    print(check)
    fin_max = max(check, key=check.get)
    return fin_max  

def check_product_city(list_of_columns):
    check={}
    for columns in list_of_columns:
        check[columns]=similar('Order City',columns)
    print(check)
    fin_max = max(check, key=check.get)
    return fin_max  

def check_review_text(list_of_columns):
    check={}
    for columns in list_of_columns:
        similarity=similar('Review Text',columns)
        if similarity>=0.5:
            check[columns]=similarity
    print(check)
    if check=={}:
        return None
    fin_max = max(check, key=check.get)
    return fin_max

def check_shipping_date(list_of_columns):
    check={}
    for columns in list_of_columns:
        similarity=similar('Shipping date',columns)
        if similarity>=0.5:
            check[columns]=similarity
    if check=={}:
        return None
    fin_max = max(check, key=check.get)
    return fin_max

def check_order_status(list_of_columns):
    check={}
    for columns in list_of_columns:
        similarity=similar('Order Status',columns)
        if similarity>=0.5:
            check[columns]=similarity
    if check=={}:
        return None
    fin_max = max(check, key=check.get)
    return fin_max