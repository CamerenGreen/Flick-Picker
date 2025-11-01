from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base
import datetime


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String)
    data = Column(String)  # JSON string of metadata


class ViewingHistory(Base):
    __tablename__ = 'viewing_history'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    watched_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User')
    movie = relationship('Movie')

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='uix_user_movie'),
    )
