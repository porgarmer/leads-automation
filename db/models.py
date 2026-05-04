from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import Date, DateTime, Float, String, ARRAY
from datetime import date, datetime, timezone
from .db import Base

class Lead(Base):
    __tablename__ = "lead"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author: Mapped[str]
    author_email: Mapped[str] = mapped_column(nullable=True, default=None)
    author_contact_num: Mapped[str] = mapped_column(nullable=True, default=None)
    author_address: Mapped[str] = mapped_column(nullable=True, default=None)
    
    book_url: Mapped[str]
    book_title: Mapped[str] 
    book_rating: Mapped[float] = mapped_column(Float)
    
    information_filled: Mapped[bool] = mapped_column(default=False)
    
    exported: Mapped[bool] = mapped_column(default=False)
    
    exists_in_company_db: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[date] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    def to_dict(self):
        return {
            "author": self.author,
            "author_email": self.author_email,
            "author_contact_num": self.author_contact_num,
            "author_address": self.author_address,
            "id": self.id,
            "book_url": self.url,
            "book_title": self.title,
            "book_rating": self.book_rating
        }
    
    def __repr__(self):
        return f"""
            <Lead(
                id={self.id}, 
                author={self.author},
                author_email={self.author_email},
                author_contact_num={self.author_contact_num},
                author_address={self.author_address},
                book_url={self.url}, 
                book_title={self.title},
                book_rating={self.book_rating},
            )>
            """
            

class ScrapedAuthor(Base):
    __tablename__ = "scraped_author"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author: Mapped[str] = mapped_column(unique=True)
    about_author: Mapped[Optional[str]]
    author_birth_date: Mapped[Optional[date]] = mapped_column(Date)
    author_death_date: Mapped[Optional[date]] = mapped_column(Date)
    author_website: Mapped[Optional[str]] = mapped_column()
    author_age: Mapped[Optional[int]] = mapped_column()
    author_current_address: Mapped[Optional[str]] = mapped_column()
    author_candidate_address: Mapped[list[str]] = mapped_column(ARRAY(String))
    book_url: Mapped[str] 
    book_title: Mapped[str] 
    book_rating: Mapped[float] = mapped_column(Float)
    
    age_and_addr_filled: Mapped[bool] = mapped_column(default=False)
    
    to_delete: Mapped[bool] = mapped_column(default=False)
    
    exists_in_company_db: Mapped[bool] = mapped_column(default=False)
        
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "about_author": self.about_author,
            "author_birth_date": self.author_birth_date,
            "author_death_date": self.author_death_date,
            "author_website": self.author_website,
            "author_age": self.author_age,
            "author_current_address": self.author_current_address,
            "author_candidate_address": self.author_candidate_address,
            "book_url": self.book_url,
            "book_title": self.book_title,
            "book_rating": self.book_rating
        }
        
    



    