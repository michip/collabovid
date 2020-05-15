from tasks.launcher.kube_job_utils import create_job_object, run_job, id_generator, get_deployment_version
import os
from os.path import join
import subprocess
from django.conf import settings


class TaskLauncher:
    def launch_task(self, name, config, block=False):
        raise NotImplementedError

    @staticmethod
    def _generate_command(name, config, full_path=True):
        """
        Generates the python command for a given configuration.
        :param name:
        :param config:
        :param username:
        :param full_path:
        :return:
        """

        service = config['service']

        if full_path:
            script_path = join(settings.BASE_DIR, '..', service, 'run_task.py')
        else:
            script_path = 'run_task.py'

        parameter_values = []

        for parameter in config['parameters']:

            if parameter['type'] == 'bool':
                if parameter['value'] == '1':
                    parameter_values.append("--{}".format(parameter['name']))
            else:
                parameter_values.append("--{} {}".format(parameter['name'], parameter['value']))

        return "python {} -u {} {} {}".format(script_path, config['started_by'], name, " ".join(parameter_values))


secret_map = {
    'scrape': ['scrape-latest', 'shared-latest'],
    'web': ['web-latest', 'shared-latest'],
    'search': ['search-latest', 'shared-latest']
}

volume_map = {
    'scrape': [],
    'web': [],
    'search': [{
        'host_path': settings.SEARCH_MODELS_HOST_PATH,
        'mount_path': '/models'
    }]
}


class KubeTaskLauncher(TaskLauncher):
    def launch_task(self, name, config, block=False):
        service = config['service']
        registry = os.getenv('REGISTRY', 'localhost:32000')
        if len(registry) > 0:
            registry += '/'
        # we assume that the web deployment holds te newest version
        version = get_deployment_version('web')
        image = registry + service + ':' + version
        cmd = TaskLauncher._generate_command(name, config, full_path=False)

        job_object = create_job_object(name=name + '-' + id_generator(size=10), container_image=image,
                                       command=["bash", "-c"],
                                       args=["export PYTHONPATH=/app:$PYTHONPATH && " + cmd],
                                       secret_names=secret_map[service], volume_mappings=volume_map[service])
        run_job(job_object, block=block)


class LocalTaskLauncher(TaskLauncher):
    def launch_task(self, name, config, block=False):
        launch_env = os.environ.copy()
        launch_env.pop("DJANGO_SETTINGS_MODULE")

        cmd = TaskLauncher._generate_command(name, config)

        if block:
            subprocess.run(cmd, shell=True, env=launch_env)
        else:
            subprocess.Popen(cmd, shell=True, env=launch_env)


def get_task_launcher():
    """
    Returns the correct task launcher for the given environment.
    :return:
    """
    if settings.TASK_LAUNCHER_LOCAL:
        return LocalTaskLauncher()
    else:
        return KubeTaskLauncher()
