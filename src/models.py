from tortoise import Model
from tortoise.fields import BigIntField, BooleanField, CharField, ForeignKeyField, ForeignKeyRelation, IntField, \
    JSONField, ReverseRelation


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

    pings: ReverseRelation["Ping"]

    class Meta:
        indexes = (("guild_id", "channel_id"))


class Ping(Model):
    id = IntField(pk=True)
    item: ForeignKeyRelation[MangaEntry] = ForeignKeyField("models.MangaEntry", related_name='pings',
                                                           on_delete="CASCADE", index=True)
    mention_id = BigIntField(null=False, index=True)
    is_role = BooleanField(null=False, default=False)


class Metadata(Model):
    key = CharField(256, pk=True, index=True)
    value = JSONField(null=False)
