from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete,select,Column, String, Integer,DateTime,ForeignKey,Text,text,Numeric
from sqlalchemy.orm import relationship
from flask_login import UserMixin,LoginManager,current_user
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow

from .helper import get_image

bcrypt = Bcrypt()
db=SQLAlchemy()

login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

ma = Marshmallow()

class Users(db.Model,UserMixin):
    __tablename__ = "users"
    user_id =           Column("user_id", Integer,primary_key=True,autoincrement=True)
    first_name =        Column("fname",Text,default="none")
    last_name =         Column("lname",Text,default="none")
    email =             Column("email",Text,unique=True,nullable=False)
    phone =             Column("phone",Text,default="none")
    username =          Column("username",Text,unique=True,nullable=False)
    password =          Column("pwd",Text,nullable=False)
    created_on =        Column("created_on", DateTime(timezone=True),default=datetime.now())
    property =          relationship('Property', backref='users',cascade='all,delete',passive_deletes=True)

    def __init__(self, email, password,username):
        self.first_name = ""
        self.last_name = ""
        self.email = email
        self.phone = ""
        self.password = password
        self.username = username

    def pass_hash(password):
        hash_pwd = bcrypt.generate_password_hash(password)
        return hash_pwd.decode('utf-8')
    
    def get_id(self):
        return self.user_id

    def __repr__(self):
        return f"<USER ID: {self.user_id}>"
    
class Income(db.Model):
    __tablename__ =         "income"
    inc_id =                Column("inc_id",Integer, primary_key=True,autoincrement=True)
    prop_id =               Column("prop_id",Integer,ForeignKey('property.prop_id',ondelete='cascade'))
    name =                  Column("name",Text,default = "")
    amount =                Column("amount",Numeric(10,2),default=0)
    user_id =               Column(Integer,ForeignKey('users.user_id'))

    def __init__(self, prop_id, name,amount,user_id):
        self.prop_id = prop_id
        self.name = name
        self.amount = amount
        self.user_id = user_id

    def __repr__(self):
        return f"<INCOME: {self.name} AMOUNT: {self.amount}>"
    
class Expenses(db.Model):
    __tablename__ =         "expense"
    exp_id =                Column("inc_id",Integer, primary_key=True,autoincrement=True)
    prop_id =               Column("prop_id",Integer,ForeignKey('property.prop_id',ondelete='cascade'))
    name =                  Column("name",Text,default='none')
    amount =                Column("amount",Numeric(10,2),default=0)
    user_id =               Column(Integer,ForeignKey('users.user_id'))

    def __init__(self,prop_id,name,amount,user_id):
        self.prop_id = prop_id
        self.name =  name
        self.amount = amount
        self.user_id = user_id

    def __repr__(self):
        return f"<EXPENSE: {self.name} AMOUNT: {self.amount}>"

class Property(db.Model):
    __tablename__ =         "property"
    prop_id =               Column(Integer, primary_key=True,autoincrement=True)
    address =               Column(Text,nullable=False)
    purch_price =           Column(Numeric(10,2),nullable=False)
    est_rent =              Column(Numeric(10,2),nullable=False)
    _user_id =              Column(Integer,ForeignKey('users.user_id',ondelete='cascade'))
    image =                 Column(String, nullable=False)
    roi =                   Column(Numeric(5,2))
    income =                relationship('Income', backref='property', cascade='all,delete',passive_deletes=True)
    expenses =              relationship('Expenses', backref='property', cascade='all,delete',passive_deletes=True)
    
    def __init__(self,address,purch_price,est_rent,_user_id,image=""):
        self.address = address
        self.purch_price = purch_price
        self.est_rent = est_rent
        self._user_id = _user_id
        self.image = self.set_image(image,address)

    def set_image(self,image,address):
        if not image:
            image=get_image(address)
        return image
    
    def __repr__(self):
        return f"<ADDRESS: {self.address}>"
