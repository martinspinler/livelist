"""
Database models for Livelist
"""

import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import ForeignKey, Index, String, Text, Integer, Date, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


# Many-to-many relationship for song tags
song_tags = Table(
    'song_tags',
    Base.metadata,
    Column('song_id', Integer, ForeignKey('songs.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Band(Base):
    __tablename__ = "bands"

    id: Mapped[int] = mapped_column(primary_key=True)
    #uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    addr: Mapped[str] = mapped_column(String(255))  # subdomain identifier

    # Authentication tokens
    #view_token: Mapped[Optional[str]] = mapped_column(String(255))
    #edit_token: Mapped[Optional[str]] = mapped_column(String(255))

    # Active playlist (will be set by application, no foreign key to avoid circular dependency)
    active_playlist_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist",
        back_populates="band",
        order_by="Playlist.date.desc()",
        foreign_keys="[Playlist.band_id]"
    )

    songs: Mapped[List["Song"]] = relationship("Song", back_populates="band")


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    #uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date)

    # Band association
    band_id: Mapped[int] = mapped_column(ForeignKey("bands.id"))
    band: Mapped["Band"] = relationship(
        "Band",
        back_populates="playlists",
        foreign_keys=[band_id]
    )

    # CRDT sync fields
    version: Mapped[int] = mapped_column(default=0)
    #server_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Active item in this playlist (will be set by application, no foreign key to avoid circular dependency)
    active_item_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    items: Mapped[List["PlaylistItem"]] = relationship(
        "PlaylistItem",
        back_populates="playlist",
        order_by="PlaylistItem.position",
        cascade="all, delete-orphan",
        foreign_keys="[PlaylistItem.playlist_id]"
    )


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    #uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    # Band association
    band_id: Mapped[int] = mapped_column(ForeignKey("bands.id"))
    band: Mapped["Band"] = relationship("Band", back_populates="songs")

    # Song metadata
    filename: Mapped[Optional[str]] = mapped_column(String(512))
    store: Mapped[Optional[str]] = mapped_column(String(50))  # References config stores
    notes: Mapped[Optional[str]] = mapped_column(Text)
    bpm: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[str]] = mapped_column(String(255))  # Composer/arranger identifier
    meta: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for visual/other metadata

    # CRDT sync fields
    version: Mapped[int] = mapped_column(default=0)
    #server_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Tags for filtering
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=song_tags, back_populates="songs")

    # Relationship to playlist items
    playlist_items: Mapped[List["PlaylistItem"]] = relationship("PlaylistItem", back_populates="song")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color for UI display
    songs: Mapped[List["Song"]] = relationship("Song", secondary=song_tags, back_populates="tags")


class PlaylistItem(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    #uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True)

    # Foreign keys
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id"))
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="items")

    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"))
    song: Mapped["Song"] = relationship("Song", back_populates="playlist_items")

    position: Mapped[int] = mapped_column(Integer)
    meta: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for item-specific metadata

    # CRDT sync fields
    #version: Mapped[int] = mapped_column(default=0)
    #server_id: Mapped[Optional[str]] = mapped_column(String(255))
    #tombstone: Mapped[bool] = mapped_column(default=False)  # For soft delete in sync

    # Index for ordering
    __table_args__ = (
        Index('ix_playlist_items_playlist_position', 'playlist_id', 'position'),
    )
