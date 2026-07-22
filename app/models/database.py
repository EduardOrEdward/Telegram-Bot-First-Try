from sqlalchemy import String, Text, BigInteger, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from app.database.base import BaseClass


class OrderItem(BaseClass):
    """Repressent a specific product within an order"""
    
    __tablename__='order_items'
    
    order_item_id:Mapped[int]=mapped_column(primary_key=True)
    order_id:Mapped[int]=mapped_column(ForeignKey("orders.id",ondelete='CASCADE'))
    product_id:Mapped[int]=mapped_column(ForeignKey('products.id',ondelete='RESTRICT'))
    quanity:Mapped[int]=mapped_column(default=1)
    price_at_purchase:Mapped[float]=mapped_column(Numeric(10,2))
    
    order:Mapped["Order"]=relationship(back_populates="items")
    product:Mapped['Product']=relationship(back_populates="order_items")
    



class Order(BaseClass):
    """Repressent a user's order"""
    __tablename__='orders'
    
    orders_id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'))
    total_amount:Mapped[float]=mapped_column(Numeric(10,2),default=0.0)
    status:Mapped[str]=mapped_column(String(50),default='pending')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    
    
    user:Mapped["User"]=relationship(back_populates='orders')
    items:Mapped[List['OrderItem']]=relationship(back_populates='orders',lazy='selectin')



class User(BaseClass):
    '''Repressent a user of our telegram bot'''
    __tablename__="users"
    user_id:Mapped[int]=mapped_column(BigInteger,primary_key=True,autoincrement=False) #Telegram user ID
    username:Mapped[Optional[str]]=mapped_column(String(32),nullable=True) #Their username in Telegram
    first_name:Mapped[str]=mapped_column(String(255)) #Their first name(Displayed username)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()) #The date when account were created
    
    orders:Mapped[List['Order']]=relationship(back_populates='user',lazy='selectin')

class Category(BaseClass):
    '''Repressent a product category'''
    
    __tablename__='categories'
    
    category_id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(100),unique=True)
    description:Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    
    products:Mapped[List['Product']]=relationship(back_populates='categories',lazy='selectin')

class Product(BaseClass):
    '''Repressent a shop product'''
    __tablename__='products'
    
    product_id:Mapped[int]=mapped_column(primary_key=True)
    category_id:Mapped[int]=mapped_column(ForeignKey('categories.id',ondelete='CASCADE'))
    name:Mapped[str]=mapped_column(String(255))
    description:Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    price:Mapped[float]=mapped_column(Numeric(10,2))
    stock:Mapped[int]=mapped_column(default=0)
    
    category:Mapped['Category']=relationship(back_populates='products')
    order_time:Mapped[List['OrderItem']]=relationship(back_populates='product',lazy='selectin')