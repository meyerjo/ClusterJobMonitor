import logging

from pyramid.config import Configurator

from sshmonitor.jobmanager import JobManager


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(format=FORMAT)

    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/home')
    config.add_route('jobs', '/')
    config.scan()
    return config.make_wsgi_app()
