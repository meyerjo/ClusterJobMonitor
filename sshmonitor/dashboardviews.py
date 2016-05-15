import datetime
import logging
import re

from pyramid.view import view_config

from jobmanager.job_database_wrapper import JobDatabaseWrapper


class DashboardViews():

    def __init__(self, request):
        self._request = request
        self._projectname = 'Dashboard'
        self._jobarchive = JobDatabaseWrapper().job_archive()

    def get_statistics(self):
        permonth = dict()
        perhour = dict()
        perweekday = dict()
        for row in self._jobarchive:
            submissiontime = row['SubmissionTime']
            group = re.search('(\([^)]+\))', submissiontime)
            if group:
                submissiontime = group.group(1)[1:-1]
            dt = datetime.datetime.strptime(submissiontime, '%Y-%m-%d %H:%M:%S')
            year_month = str(dt.strftime('%Y-%m'))
            hour = str(dt.strftime('%H'))
            weekday = str(dt.strftime('%A'))

            perhour[hour] = 1 if hour not in perhour else perhour[hour] + 1
            permonth[year_month] = 1 if year_month not in permonth else permonth[year_month] + 1
            perweekday[weekday] = 1 if weekday not in perweekday else perweekday[weekday] + 1
        return permonth, perhour, perweekday


    @view_config(route_name='dashboard_statistics', renderer='json', match_param='fieldname=weekday')
    def weekday_statistics(self):
        permonth, perhour, perweekday = self.get_statistics()

        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        data = [dict(period=key, jobs=perweekday[key]) if key in perweekday else dict(period=key, jobs=0)
               for key in weekdays]
        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['period'],
            ykeys=['jobs'],
            labels=['Jobs'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')

    @view_config(route_name='dashboard_statistics',renderer='json', match_param='fieldname=jobs_per_hour')
    def jobs_per_hour_statistics(self):
        permonth, perhour, perweekday = self.get_statistics()
        data = []
        for i in range(0, 24):
            str_i = '{0:02d}'.format(i)
            if str_i in perhour:
                data.append(dict(period=str_i, jobs=perhour[str_i]))
            else:
                data.append(dict(period=str_i, jobs=0))

        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['period'],
            ykeys=['jobs'],
            labels=['Jobs'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')

    @view_config(route_name='dashboard_statistics', renderer='json', match_param='fieldname=jobs_per_month')
    def jobs_per_month(self):
        permonth, perhour, perweekday = self.get_statistics()
        data = []
        import datetime
        months = []
        for i in range(2015, datetime.datetime.now().year+1):
            for j in range(1, 13):
                if i == datetime.datetime.now().year and j > datetime.datetime.now().month:
                    continue
                months.append('{0}-{1:02d}'.format(i, j))
        for month in months:
            if month in permonth:
                data.append(dict(period=month, jobs=permonth[month]))
            else:
                data.append(dict(period=month, jobs=0))
        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['period'],
            ykeys=['jobs'],
            labels=['Jobs'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')

    @view_config(route_name='dashboard_statistics', match_param='fieldname=waitingtime_per_job', renderer='json')
    def waittime_per_job(self):
        jobs = JobDatabaseWrapper.job_archive()
        job_names = {}
        for job in jobs:
            if '_sa_instance_state' in job:
                del job['_sa_instance_state']
            if 'JobName' not in job:
                print('Jobnames not in {0}'.format(job))
                continue
            if ('StartTime' not in job) or \
                    ('CompletionTime' not in job) or \
                    ('SubmissionTime' not in job):
                continue
            if 'JobID' not in job:
                print('JobID not in job: {0}'.format(job))
                continue
            # make sure that they all have a common format
            timefields = ['StartTime', 'CompletionTime', 'SubmissionTime']
            for timefield in timefields:
                if timefield not in job:
                    continue
                m = re.search('^[0-9]+\s\(([^\)]+)\)', job[timefield])
                if m:
                    job[timefield] = m.group(1)

            if job['JobName'] in job_names:
                job_names[job['JobName']]['jobid'].append(job['JobID'])
                job_names[job['JobName']]['starttime'].append(job['StartTime'])
                job_names[job['JobName']]['completiontime'].append(job['CompletionTime'])
                job_names[job['JobName']]['submissiontime'].append(job['SubmissionTime'])
            else:
                tmp = dict(jobid=[job['JobID']],
                           starttime=[job['StartTime']],
                           completiontime=[job['CompletionTime']],
                           submissiontime=[job['SubmissionTime']])
                job_names[job['JobName']] = tmp

        # derive durations
        for (key, item) in job_names.items():
            if not isinstance(item, dict):
                continue
            waiting_time_str = []
            waiting_time = []
            for i, elem in enumerate(item['submissiontime']):
                diff = datetime.datetime.strptime(item['starttime'][i], '%Y-%m-%d %H:%M:%S') - \
                       datetime.datetime.strptime(elem, '%Y-%m-%d %H:%M:%S')
                waiting_time_str.append(str(diff))
                waiting_time.append(diff)
            duration_time = []
            duration_time_str = []
            for i, elem in enumerate(item['completiontime']):
                diff = datetime.datetime.strptime(elem, '%Y-%m-%d %H:%M:%S') - \
                       datetime.datetime.strptime(item['starttime'][i], '%Y-%m-%d %H:%M:%S')
                duration_time_str.append(str(diff))
                duration_time.append(diff)
            job_names[key]['waiting_time'] = waiting_time_str
            job_names[key]['duration'] = duration_time_str

            mean_duration = datetime.timedelta(0)
            for dur in duration_time:
                mean_duration += dur
            mean_duration  = mean_duration / len(duration_time)

            mean_waitingtime = datetime.timedelta(0)
            for wai in waiting_time:
                mean_waitingtime += wai
            mean_waitingtime = mean_waitingtime / len(waiting_time)

            job_names[key]['mean_duration'] = mean_duration.total_seconds()
            job_names[key]['mean_waiting'] = mean_waitingtime.total_seconds()

        data = []
        for (key, item) in job_names.items():
            data.append(dict(jobname=key, waitingtime=item['mean_waiting']))

        overall_data = dict(
            element=self._request.matchdict['fieldname'],
            data=data,
            xkey=['jobname'],
            ykeys=['waitingtime'],
            labels=['Waitingtime in sec'],
            hideHover='auto',
            resize=True
        )
        return dict(data=overall_data, charttype='bar')

    @view_config(route_name='dashboard_statistics', renderer='json')
    def dummy(self):
        """
        Dummy Request, which gets called, when none of the other view_config actions is matched
        :return:
        """
        log = logging.getLogger(__name__)
        try:
            print(self._request.params)
        except BaseException as e:
            print(e)
        log.error('Requested url didnt match any specified view. {0} {1}'
                  .format(self._request.matchdict, self._request.params))
        return self._request.matchdict

    @view_config(route_name='dashboard', renderer='templates/job_dashboard.pt')
    def dashboard(self):
        permonth, perhour, perweekday = self.get_statistics()
        
        return {'project': self._projectname, 'content': []}
