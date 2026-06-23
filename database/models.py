import json
from typing import List
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    TIMESTAMP, BigInteger, Boolean, Text, UniqueConstraint, func, Integer, ForeignKey, DateTime
)


class BaseModel(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"


class Roles(BaseModel):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)

    users: Mapped[list["Users"]] = relationship(back_populates="role")


class Users(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    login: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=True)

    role: Mapped["Roles"] = relationship(back_populates="users")
    social_networks: Mapped[List["SocialNetworks"]] = relationship(back_populates="user")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Session(BaseModel):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(Text, unique=True, index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user: Mapped["Users"] = relationship(back_populates="sessions")


class SocialNetworks(BaseModel):
    __tablename__ = "social_networks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    username: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["Users"] = relationship(back_populates="social_networks")
    items: Mapped[list["NetworkItems"]] = relationship(back_populates="network")


class NetworkItems(BaseModel):
    __tablename__ = "network_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _network_id: Mapped[int] = mapped_column(ForeignKey("social_networks.id"))
    url: Mapped[str] = mapped_column(Text)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    network: Mapped["SocialNetworks"] = relationship(back_populates="items")
    _metadata: Mapped[list["ItemMetadata"]] = relationship(back_populates="item")
    comments: Mapped[list["ItemComments"]] = relationship(back_populates="item")

    __table_args__ = (
        UniqueConstraint("_network_id", "url", name="uq_network_item"),
    )


class ItemMetadata(BaseModel):
    __tablename__ = "item_metadata"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _item_id: Mapped[int] = mapped_column(ForeignKey("network_items.id"))
    likes: Mapped[int] = mapped_column(BigInteger)
    views_picture: Mapped[int] = mapped_column(BigInteger)
    views_video: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(Text)
    saves: Mapped[int] = mapped_column(BigInteger)
    reposts: Mapped[int] = mapped_column(BigInteger)
    comments_count: Mapped[int] = mapped_column(BigInteger)

    item: Mapped["NetworkItems"] = relationship(back_populates="_metadata")


class ItemComments(BaseModel):
    __tablename__ = "item_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    _item_id: Mapped[int] = mapped_column(ForeignKey("network_items.id"))
    comment: Mapped[dict] = mapped_column(JSONB)

    item: Mapped["NetworkItems"] = relationship(back_populates="comments")


class ScrapeAccounts(BaseModel):
    __tablename__ = "scrape_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    client_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # api_id - для телеграмма
    token_hash: Mapped[str | None] = mapped_column(Text, nullable=True)  # api_hash - для телеграмма
    type: Mapped[str | None] = mapped_column(Text, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)


class TelegramBots(BaseModel):
    __tablename__ = "telegram_bots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bot_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_hash: Mapped[str] = mapped_column(Text)
    status: Mapped[bool] = mapped_column(Boolean, default=True)


class Proxies(BaseModel):
    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    login: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    host: Mapped[str | None] = mapped_column(Text, nullable=True)
    port: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
