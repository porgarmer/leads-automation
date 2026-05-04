import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
#engine = sa.create_engine("postgresql://postgres:12345@localhost:5432/attitech")
#engine = sa.create_engine("mysql+mysqlconnector://root:12345@localhost:3306/leads", echo=False)
engine = sa.create_engine("mysql+mysqlconnector://kevin:Core%402002@192.168.68.200:3306/leads", echo=False, pool_pre_ping=True,
    pool_recycle=3600)
Session = sessionmaker(bind=engine)
Base = declarative_base()
        
