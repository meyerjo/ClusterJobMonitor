import datetime

from sqlalchemy import DateTime, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.types import Text

from models import Base


class MonitoredFile(Base):

    __tablename__ = 'monitoredfile'

    id = Column(Integer, nullable=False, primary_key=True)
    complete_filepath = Column(String(1024), nullable=False)
    folder = Column(String(1024), nullable=False, default='/')
    filename = Column(String(1024), nullable=False)
    createtime = Column(DateTime, default=datetime.datetime.utcnow())

    def __init__(self, folder, filename, complete_filepath=None):
        if not folder.endswith('/'):
            folder = folder + '/'
        if complete_filepath is None:
            complete_filepath = folder + filename

        self.folder = folder
        self.filename = filename
        self.complete_filepath = complete_filepath

class MonitoredFileSource(Base):

    __tablename__ = 'monitoredfilesource'

    id = Column(Integer, ForeignKey('monitoredfile.id'), primary_key=True)
    source = Column(String(1024), nullable=False)
    auto_fix = Column(Boolean, nullable=False, default=False)
    createtime = Column(DateTime, default=datetime.datetime.utcnow())

    def __init__(self, id, src, auto_fix=False):
        self.id = id
        self.source = src
        self.auto_fix = auto_fix

class MonitoringError(Base):

    __tablename__ = 'monitoringerror'

    id = Column(Integer, primary_key=True)
    fileid = Column(Integer, ForeignKey('monitoredfile.id'))
    component = Column(String(1024), nullable=False)
    errormsg = Column(Text, nullable=False)
    createtime = Column(DateTime, default=datetime.datetime.utcnow())

    def __init__(self, fileid, component, errormsg):
        self.fileid = fileid
        self.component = component
        self.errormsg = errormsg
