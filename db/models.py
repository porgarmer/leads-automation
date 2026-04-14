from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Book(Base):
    __tablename__ = "book"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str]
    title: Mapped[str] 
    author: Mapped[str]
    author_email: Mapped[str] = mapped_column(nullable=True, default=None)
    author_contact_num: Mapped[str] = mapped_column(nullable=True, default=None)
    author_address: Mapped[str] = mapped_column(nullable=True, default=None)
    information_filled: Mapped[bool] = mapped_column(default=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "author": self.author,
            "author_email": self.author_email,
            "author_contact_num": self.author_contact_num,
            "author_address": self.author_address,
            "information_filled": self.information_filled
        }
    
    def __repr__(self):
        return f"""
            <Book(
                id={self.id}, 
                url={self.url}, 
                title={self.title},
                author={self.author},
                author_email={self.author_email},
                author_contact_num={self.author_contact_num},
                author_address={self.author_address}
            )>
            """