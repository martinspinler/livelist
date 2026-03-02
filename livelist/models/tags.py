"""
Tag management system for songs
"""

from typing import List, Optional
from . import db
from .database import Song, Tag


class TagManager:
    """Manager for song tags"""

    @staticmethod
    def get_or_create_tag(name: str, color: Optional[str] = None) -> Tag:
        """Get existing tag or create a new one"""
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, color=color)
            db.session.add(tag)
            db.session.commit()
        return tag

    @staticmethod
    def add_tag_to_song(song_id: int, tag_name: str, color: Optional[str] = None) -> bool:
        """Add a tag to a song"""
        song = Song.query.get(song_id)
        if not song:
            return False

        tag = TagManager.get_or_create_tag(tag_name, color)

        if tag not in song.tags:
            song.tags.append(tag)
            db.session.commit()

        return True

    @staticmethod
    def remove_tag_from_song(song_id: int, tag_name: str) -> bool:
        """Remove a tag from a song"""
        song = Song.query.get(song_id)
        tag = Tag.query.filter_by(name=tag_name).first()

        if not song or not tag:
            return False

        if tag in song.tags:
            song.tags.remove(tag)
            db.session.commit()

            # If tag is no longer used, delete it
            if not tag.songs:
                db.session.delete(tag)
                db.session.commit()

        return True

    @staticmethod
    def get_songs_by_tag(tag_name: str, band_id: Optional[int] = None) -> List[Song]:
        """Get all songs with a specific tag, optionally filtered by band"""
        query = Song.query.join(Song.tags).filter(Tag.name == tag_name)

        if band_id is not None:
            query = query.filter(Song.band_id == band_id)

        return query.all()

    @staticmethod
    def get_all_tags(band_id: Optional[int] = None) -> List[Tag]:
        """Get all tags, optionally filtered by band"""
        if band_id is None:
            return Tag.query.all()

        # Get tags only for songs in the specified band
        return Tag.query.join(Tag.songs).filter(Song.band_id == band_id).distinct().all()

    @staticmethod
    def update_tag_color(tag_name: str, color: str) -> bool:
        """Update the color of a tag"""
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            return False

        tag.color = color
        db.session.commit()
        return True

    @staticmethod
    def merge_tags(old_tag_name: str, new_tag_name: str) -> bool:
        """Merge two tags, moving all songs from old tag to new tag"""
        old_tag = Tag.query.filter_by(name=old_tag_name).first()
        new_tag = TagManager.get_or_create_tag(new_tag_name)

        if not old_tag:
            return False

        # Move songs from old tag to new tag
        for song in old_tag.songs:
            if new_tag not in song.tags:
                song.tags.append(new_tag)
            song.tags.remove(old_tag)

        db.session.delete(old_tag)
        db.session.commit()

        return True
