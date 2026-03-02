"""
Database models for Livelist
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


db = SQLAlchemy(model_class=Base)

# Import all models here to register them with SQLAlchemy
from .database import Band, Playlist, Song, PlaylistItem, Tag, song_tags
from .tags import TagManager

__all__ = [
    'db',
    'Band',
    'Playlist',
    'Song',
    'PlaylistItem',
    'Tag',
    'song_tags',
    'TagManager',
]
