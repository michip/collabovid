import string
import random
from kubernetes import client, config, watch
import kubernetes.client
from kubernetes.client.rest import ApiException

from django.conf import settings


def cleanup_pods(delete_succeeded=True, delete_failed=True, namespace="default"):
    """
    Cleans up finished or failed pods.
    :param delete_succeeded:
    :param delete_failed:
    :param namespace:
    :return:
    """

    if not delete_failed and not delete_succeeded:
        return

    api_instance = kubernetes.client.CoreV1Api()

    try:
        if delete_succeeded:
            succeeded_pods = api_instance.list_namespaced_pod(namespace,  field_selector="status.phase==Succeeded")
            for pod in succeeded_pods.items:
                print("deleting succeeded pod", pod.metadata.name)
                api_instance.delete_namespaced_pod(pod.metadata.name, namespace)

        if delete_failed:
            failed_pods = api_instance.list_namespaced_pod(namespace, field_selector="status.phase==Failed")
            for pod in failed_pods.items:
                print("deleting failed pod", pod.metadata.name)
                api_instance.delete_namespaced_pod(pod.metadata.name, namespace)

    except ApiException as e:
        print("Exception when calling CoreV1Api from cleanup: %s\n" % e)


def create_job_object(name, container_image, command, args=None, namespace="default", container_name="jobcontainer",
                      env_vars=None, restart_policy='Never', ttl_finished=180, secret_names=None, backoff_limit=0,
                      volume_mappings=None):

    if settings.TASK_DELETE_SUCCESSFUL_PODS or settings.TASK_DELETE_FAILED_PODS:
        cleanup_pods(delete_succeeded=settings.TASK_DELETE_SUCCESSFUL_PODS,
                     delete_failed=settings.TASK_DELETE_FAILED_PODS,
                     namespace=namespace)

    if env_vars is None:
        env_vars = {}
    if secret_names is None:
        secret_names = []
    if args is None:
        args = []
    if volume_mappings is None:
        volume_mappings = []

    body = client.V1Job(api_version="batch/v1", kind="Job")
    # metadata and status are required
    body.metadata = client.V1ObjectMeta(namespace=namespace, name=name)
    body.status = client.V1JobStatus()

    template = client.V1PodTemplate()
    template.template = client.V1PodTemplateSpec()

    api_client = client.BatchV1Api()

    # Set env variables
    env_list = []
    for env_name, env_value in env_vars.items():
        env_list.append(client.V1EnvVar(name=env_name, value=env_value))

    env_from = []
    for secret_name in secret_names:
        env_from.append(client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=secret_name)))

    volumes = []
    volume_mounts = []
    for i, volume_mapping in enumerate(volume_mappings):
        volume = client.V1Volume(name=f'volume-{i}',
                                 host_path=client.V1HostPathVolumeSource(path=volume_mapping['host_path']))
        volumes.append(volume)
        volume_mounts.append(client.V1VolumeMount(name=f'volume-{i}', mount_path=volume_mapping['mount_path']))

    # set container options
    container = client.V1Container(name=container_name, image=container_image, env=env_list,
                                   command=command, args=args, env_from=env_from, volume_mounts=volume_mounts,
                                   image_pull_policy=settings.TASK_IMAGE_PULL_POLICY)

    # set pod options
    template.template.spec = client.V1PodSpec(containers=[container], restart_policy=restart_policy, volumes=volumes,
                                              service_account_name='collabovid-sa')

    body.spec = client.V1JobSpec(ttl_seconds_after_finished=ttl_finished, template=template.template,
                                 backoff_limit=backoff_limit)

    return body



def run_job(job_object: client.V1Job, block=False):
    config.load_incluster_config()
    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
    try:
        api_response = api_instance.create_namespaced_job("default", job_object, pretty=True)
        print(api_response, flush=True)

        if block:
            w = watch.Watch()
            for event in w.stream(api_instance.list_job_for_all_namespaces):
                o = event['object']
                if o.status.succeeded or o.status.failed:
                    break

    except ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e, flush=True)
    return


def get_deployment_version(service):
    config.load_incluster_config()
    v1 = client.AppsV1Api()
    ret = v1.list_namespaced_deployment(namespace='default', label_selector=f'app={service}')
    for i in ret.items:
        if len(i.spec.template.spec.containers) != 1:
            return None
        image = i.spec.template.spec.containers[0].image
        image = image.split('/')[-1]
        tokens = image.split(':')
        if len(tokens) != 2:
            return None
        service, tag = tokens
        return tag
    return None


def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
