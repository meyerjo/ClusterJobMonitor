import datetime

import jsonpickle
from sqlalchemy import DateTime, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.types import Text

from models import Base


class ArchiveUserConfiguration(Base):

    __tablename__ = 'archive_user_configuration'

    configuration_id = Column(Integer, primary_key=True)
    columns_json = Column(Text, nullable=False)
    user = Column(Integer, nullable=True)
    createtime = Column(DateTime, default=datetime.datetime.utcnow(), nullable=True)

    def __init__(self, columns_json):
        if isinstance(columns_json, list):
            columns_json = jsonpickle.encode(columns_json)

        self.columns_json = columns_json


class JobConfiguration(Base):

    __tablename__ = 'job_configuration'

    configuration_id = Column(Integer, primary_key=True)
    configuration_name = Column(String, nullable=False)
    job_name = Column(String(255), nullable=False)
    job_path = Column(Text, nullable=False)
    variable_set = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)
    create_time = Column(DateTime, default=datetime.datetime.utcnow(), nullable=True)

    def __init__(self, conf_name, job_name, job_path, variable_set, user_id=None):
        self.configuration_name = conf_name
        self.job_name = job_name
        self.job_path = job_path
        self.variable_set = variable_set
        if user_id is not None:
            self.user_id = user_id
