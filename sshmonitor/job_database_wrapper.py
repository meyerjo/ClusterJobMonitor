import logging
import re

import jsonpickle
import transaction

from models import DBSession
from models.ConfigurationModel import ArchiveUserConfiguration
from models.Job import Job, JobOutput


class JobDatabaseWrapper:


    @staticmethod
    def get_jobs(jobmanager, coltitles):
        """
        Returns the current jobs
        :param jobmanager: ssh or filebased job manager, which can retrieve the jobs from the server
        :param coltitles: list of the column titles which shall be returned, all the others get filtered
        :return:
        """
        jobs = jobmanager.get_all_jobs()
        log = logging.getLogger(__name__)
        try:
            JobDatabaseWrapper.write_jobs_to_database(jobs)
        except BaseException as e:
            log.error('{0} {1}'.format(jobs, str(e)))
        jobs = jobmanager.filter_from_dict(jobs, coltitles)
        jobs = jobmanager.convert_from_listdict_to_list(jobs, coltitles)
        jobs['joborder'] = ['eligible', 'active', 'blocked', 'completed']
        return jobs

    @staticmethod
    def write_jobs_to_database(jobs):
        """
        Writes the retrieved jobs to the database
        :param jobs: list of all jobs
        :return:
        """
        log = logging.getLogger(__name__)
        with transaction.manager:
            for (classname, classmembers) in jobs.items():
                if len(classmembers) == 0:
                    continue
                for element in classmembers:
                    if 'error' in element:
                        continue
                    if 'JobID' not in element:
                        log.debug('Row didn''t match specified criteria {0}'.format(element))
                        continue
                    if not re.search('[0-9]*', element['JobID']):
                        log.debug('Row didn''t match specified criteria {0}'.format(element))
                        continue
                    dbrow = DBSession.query(Job).filter(Job.id == element['JobID']).all()
                    json_str = jsonpickle.encode(element)
                    if len(dbrow) == 0:
                        j = Job(element['JobID'], json_str)
                        DBSession.add(j)
                    elif len(dbrow) == 1:
                        dbrow[0].jobinfo = json_str
                    else:
                        log.error('More than one entry for jobid: {0}'.format(json_str))
            DBSession.commit()

    @staticmethod
    def job_archive():
        """
        Returns the job archive from the database
        :return:
        """
        jobs_stmt = DBSession.query(Job).order_by(Job.updatetime.desc()).all()
        jobs_dict = []
        for jobs in jobs_stmt:
            job_outputs = DBSession.query(JobOutput).filter(JobOutput.jobid == jobs.id).all()
            jobs = jobs.__dict__

            if 'jobinfo' in jobs and jobs['jobinfo'] is not None:
                obj = jsonpickle.decode(jobs['jobinfo'])
                jobs.update(obj)

            if 'jobdetails' in jobs and jobs['jobdetails'] is not None:
                obj = jsonpickle.decode(jobs['jobdetails'])
                jobs.update(obj)

            jobs['number_of_joboutputs'] = len(job_outputs)
            jobs['joboutputs'] = []
            for outputs in job_outputs:
                jobs['joboutputs'].append(outputs.__dict__)
            jobs_dict.append(jobs)
        return jobs_dict

    @staticmethod
    def job_archive_config():
        """
        Retrieves the most recent job archive configuration
        :return:
        """
        jobconfig = DBSession.query(ArchiveUserConfiguration.configuration_id,
                                    ArchiveUserConfiguration.columns_json,
                                    ArchiveUserConfiguration.createtime).order_by(ArchiveUserConfiguration.configuration_id.desc()).first()
        return jobconfig

    @staticmethod
    def write_job_archive_config(configuration):
        """
        Writes a new job archive configuration to the database
        :param configuration:
        :return:
        """
        with transaction.manager:
            DBSession.add(ArchiveUserConfiguration(jsonpickle.encode(configuration)))
            DBSession.commit()