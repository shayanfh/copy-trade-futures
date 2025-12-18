from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.migrate import *

import logging
import coloredlogs
logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG, logger=logger)

# db = SqliteDatabase("db")
db = SqliteQueueDatabase("db")


class BaseModel(Model):
    class Meta:
        database = db


class Signals(BaseModel):
    id_signal = TextField(unique=True)
    symbol = TextField()
    #long or short
    kind = TextField()
    entry = FloatField()
    # OPEN or CLOSE or CANCELED(for manual cancel)
    status = TextField(default="OPEN")
    targets_str = TextField()
    stop_limit = FloatField(default=0)
    id_stoploss = IntegerField(null=True)
    client_id_stoploss = TextField(null=True)

    def set_status(self, status):
        self.status = status
        self.save()

    def set_id_stoploss(self, id_stoploss):
        self.id_stoploss = id_stoploss
        self.save()

    def set_client_id_stoploss(self, client_id_stoploss):
        self.client_id_stoploss = client_id_stoploss
        self.save()


class Targets(BaseModel):
    owner = ForeignKeyField(Signals, backref='targets')
    number = IntegerField()
    id_target = TextField()
    # OPEN or CLOSE
    status = TextField(default="OPEN")

    def set_status(self, status):
        self.status = status
        self.save()


class Settings(BaseModel):
    limit_balance = FloatField(default=2000.0)

    def set_limit_balance(self, limit_balance):
        self.limit_balance = limit_balance
        self.save()

def create_db_tables():
    logger.info("Checking database...")
    # try:
    # with db:
    db.create_tables([Signals, Targets, Settings])
    logger.info("Tables created!")
    # except:
    #     pass

create_db_tables()

try:
    Settings.create(id=0)
except:
    pass
