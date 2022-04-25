from datetime import datetime

from discord.utils import snowflake_time
from tortoise import Model
from tortoise.fields import BigIntField, BooleanField, CharField, DatetimeField, ForeignKeyField, ForeignKeyRelation, \
    IntField, JSONField, ReverseRelation


class MangaEntry(Model):
    id = IntField(pk=True)
    guild_id = BigIntField(null=False)
    channel_id = BigIntField(null=False)
    creator_id = BigIntField(null=False)
    item_id = CharField(1024, null=False)
    source_id = CharField(20, null=False, index=True)
    extra_config = JSONField(null=True)
    message_channel_first = BooleanField(null=False, default=False)
    private_thread = BooleanField(null=False, default=False)
    deleted = DatetimeField(null=True)

    pings: ReverseRelation["Ping"]
    threads: ReverseRelation["ThreadData"]

    class Meta:
        indexes = (("guild_id", "channel_id"),)


class Ping(Model):
    id = IntField(pk=True)
    item: ForeignKeyRelation[MangaEntry] = ForeignKeyField("models.MangaEntry", related_name='pings',
                                                           on_delete="CASCADE", index=True)
    mention_id = BigIntField(null=False, index=True)
    is_role = BooleanField(null=False, default=False)


class Metadata(Model):
    key = CharField(256, pk=True, index=True)
    value = JSONField(null=False)


class ThreadData(Model):
    thread_id = BigIntField(pk=True)
    entry: ForeignKeyRelation[MangaEntry] = ForeignKeyField("models.MangaEntry", related_name='threads',
                                                            on_delete="CASCADE", index=True)

    @property
    def created_at(self) -> datetime:
        return snowflake_time(self.thread_id)
