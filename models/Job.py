import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime

from models import Base


class Job(Base):

    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    jobinfo = Column(String, nullable=False)
    jobdetails = Column(String, nullable=True)
    updatetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())

    def __init__(self, info):
        self.jobinfo = info

class JobOutput(Base):

    __tablename__ = 'joboutput'

    id = Column(Integer, ForeignKey('job.id'), primary_key=True)
    output = Column(String, nullable=False)

    def __init__(self, id, output):
        self.id = id
        self.output = output

