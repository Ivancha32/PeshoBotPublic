from sqlalchemy import Table, Column, String, Integer, Boolean, ForeignKey, MetaData


metadata = MetaData()

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('discord_id', String, unique=True),
    Column('voice_channel_greeting', String),
    Column('is_bot_admin', Boolean),
    Column('play_music', Boolean, default=False),
    Column('add_to_commands', Boolean, default=False),
)

bot_permissions = Table('bot_permissions', metadata,
    Column('id', Integer, primary_key=True),
    Column('play_music', Boolean),
    Column('user_id', None, ForeignKey('users.id')),
)


pesho_tapni = Table('pesho_tapni', metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String),
    Column('active', Boolean, default=True),
)

vqrno = Table('vqrno', metadata,
    Column('id', Integer, primary_key=True),
    Column('text', String),
    Column('active', Boolean, default=True),
)