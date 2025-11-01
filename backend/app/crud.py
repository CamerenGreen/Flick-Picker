from sqlalchemy.orm import Session
import models
import json


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, name: str):
    user = models.User(name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_movie_by_tmdb(db: Session, tmdb_id: int):
    return db.query(models.Movie).filter(models.Movie.tmdb_id == tmdb_id).first()


def create_movie(db: Session, tmdb_id: int, title: str, data: dict):
    m = models.Movie(tmdb_id=tmdb_id, title=title, data=json.dumps(data))
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def ensure_movie(db: Session, tmdb_id: int, title: str, data: dict):
    m = get_movie_by_tmdb(db, tmdb_id)
    if m:
        return m
    return create_movie(db, tmdb_id, title, data)


def add_viewing(db: Session, user_id: int, movie_db_id: int):
    # movie_db_id is Movie.id
    try:
        vh = models.ViewingHistory(user_id=user_id, movie_id=movie_db_id)
        db.add(vh)
        db.commit()
        db.refresh(vh)
        return vh
    except Exception:
        db.rollback()
        # duplicate or other error -> return existing if exists
        return db.query(models.ViewingHistory).filter(models.ViewingHistory.user_id==user_id, models.ViewingHistory.movie_id==movie_db_id).first()


def get_user_history(db: Session, user_id: int):
    return db.query(models.ViewingHistory).filter(models.ViewingHistory.user_id == user_id).all()


def list_all_movies(db: Session):
    return db.query(models.Movie).all()
