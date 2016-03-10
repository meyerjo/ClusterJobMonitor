import logging

import jsonpickle
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from models import initialize_sql
from sshmonitor.jobmanager import JobManager
from sshmonitor.ssh_connectionholder import SSHConnectionHolder
from sshmonitor.sshbasedjobmanager import SSHBasedJobManager


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(format=FORMAT)

    if 'ssh.connection_params' in settings:
        with open(settings['ssh.connection_params']) as f:
            ssh_param = jsonpickle.decode(f.read())
    else:
        raise BaseException('SSH Connection parameters file is not specified. See README')


    config = Configurator(settings=settings)
    config.scan('models') # the "important" line
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    config.include('pyramid_chameleon')
    config.registry.settings['ssh_holder'] = SSHConnectionHolder(ssh_param)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/home')
    config.add_route('jobs', '/')
    config.scan()
    return config.make_wsgi_app()
