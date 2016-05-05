import datetime

import jsonpickle
from sqlalchemy import DateTime, Column, Integer, String, ForeignKey, Boolean

from models import Base


class ArchiveUserConfiguration(Base):

    __tablename__ = 'archive_user_configuration'

    configuration_id = Column(Integer, primary_key=True)
    columns_json = Column(String, nullable=False)
    user = Column(Integer, nullable=True)
    createtime = Column(DateTime, default=datetime.datetime.utcnow(), nullable=True)

    def __init__(self, columns_json):
        if isinstance(columns_json, list):
            columns_json = jsonpickle.encode(columns_json)

        self.columns_json = columns_json
