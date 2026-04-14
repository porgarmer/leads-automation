import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
engine = sa.create_engine("postgresql://postgres:12345@localhost:5432/book")
Session = sessionmaker(bind=engine)
Base = declarative_base()
        
