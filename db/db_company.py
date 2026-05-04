import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

engine = sa.create_engine("mysql+mysqlconnector://kevin:Core%402002@192.168.68.200:3306/leads", echo=False)
Session = sessionmaker(bind=engine)
