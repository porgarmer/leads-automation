from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import Date, DateTime, Float, String
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
    book_rating: Mapped[int]
    
    information_filled: Mapped[bool] = mapped_column(default=False)
    
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
    book_url: Mapped[str] 
    book_title: Mapped[str] 
    book_rating: Mapped[float] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )