import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
#engine = sa.create_engine("postgresql://postgres:12345@localhost:5432/attitech")
#engine = sa.create_engine("mysql+mysqlconnector://root:12345@localhost:3306/leads", echo=False)
engine = sa.create_engine(settings.DB_URL, echo=False, pool_pre_ping=True,
    pool_recycle=3600)
Session = sessionmaker(bind=engine)
Base = declarative_base()
        
