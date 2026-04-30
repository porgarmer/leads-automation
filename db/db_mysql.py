import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

engine = sa.create_engine("mysql+mysqlconnector://root:12345@localhost:3306/leads", echo=False)
Session = sessionmaker(bind=engine)
