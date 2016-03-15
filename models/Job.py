import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime

from models import Base


class Job(Base):

    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    jobinfo = Column(String, nullable=False)
    jobdetails = Column(String, nullable=True)
    updatetime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())

    def __init__(self, jobid, info):
        self.id = jobid
        self.jobinfo = info

class JobOutput(Base):

    __tablename__ = 'joboutput'

    id = Column(Integer, primary_key=True)
    jobid = Column(Integer, ForeignKey('job.id'))
    output = Column(String, nullable=False)
    createtime = Column(DateTime, nullable=False, default=datetime.datetime.utcnow())

    def __init__(self, id, output):
        self.jobid = id
        self.output = output

