from app import db

class datasets(db.Model):
    __tablename__="datasets"
    id=db.Column(db.Integer,primary_key=True)
    dataset_name=db.Column(db.String,nullable=False)
    dataset_link=db.Column(db.String,nullable=False)
    
    def __init__(self,dataset_name,dataset_link):
        self.dataset_name=dataset_name
        self.dataset_link=dataset_link
