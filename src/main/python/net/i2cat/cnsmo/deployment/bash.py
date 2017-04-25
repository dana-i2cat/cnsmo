import subprocess
import os
import shlex
import wget
import time
import signal


class BashDeployer:

    def __init__(self, bind_address):
        """
        Basic Bash deployer, given app requests, it creates an "environment" for the user, downloads resources from uris
        and install dependencies, after that it runs the command provided in the trigger field.

        Current implementation uses '/home/CNSMO/ENVS/' as the root directory for app environments.
        Notice it requires being run with privileges to be able to write to this directory.

        :param bind_address:
        :return:
        """
        self.__bind_address = bind_address

    def start(self):
        pass

    def stop(self):
        pass

    def launch_app(self, **kwargs):
        """
        Creates basic object that will manage the workflow of configuration and execution
        :param kwargs:
        :return:
        """
        instance = self.configure(kwargs.get("service_id"), kwargs.get("trigger"), kwargs.get("resources"), kwargs.get("dependencies"))
        process = self.spawn(instance.get_command(), instance.get_working_dir())
        instance.set_process(process)
        return instance

    def stop_app(self, instance):
        """
        Stops the app
        :param instance: Basic object that manages the workflow of configuration and execution of the app
        :return:
        """
        print("Stopping app...")
        if instance.get_process() is not None:
            print("Signalling for termination...")
            os.killpg(os.getpgid(instance.get_process().pid), signal.SIGTERM)
            time.sleep(2)
            instance.set_process(None)
        print("Stopped app")
        return instance

    def configure(self, app_id, trigger, resources, dependencies):
        """
        This method is meant to download the resources, resolve the dependencies, and prepare the app environment
        :param app_id:
        :param trigger:
        :param resources:
        :param dependencies:
        :return:
        """
        instance = self.get_instance()
        instance.set_id(app_id)
        instance.set_command(trigger)
        self.create_env(instance)
        self.get_resources(instance, resources)
        self.resolve_dependencies(dependencies)
        return instance

    #def start(self, instance):
    #    self.spawn(instance.get_command())
    #    return instance

    def create_env(self, instance):
        """
        The environment is a place were all the app data will be deployed and tracked. For simplicity
        right now is just a folder
        :param instance:
        :return:
        """
        path = "/home/CNSMO/ENVS/" + instance.get_id()
        if not os.path.exists(path):
            os.makedirs(path)
        instance.set_working_dir(path)

    def get_instance(self):
        return Instance()

    def spawn(self, command, working_dir):
        """
        Spawns the app trigger command. This method also wrapps the command with a CD to the app_env
        since all the resources are meant to be there
        :param command:
        :param working_dir:
        :return:
        """
        shell_command = "cd %s && " %working_dir +  command #self.wrap_command(command)
        process = subprocess.Popen(shell_command, shell=True, preexec_fn=os.setsid)
        return process

    def wrap_command(self, command, working_dir):
        """
        This method converts the command into a list that is required by subprocess
        :param command:
        :param working_dir:
        :return:
        """

        comand = command  #"sh -c" + command

        return shlex.split(command)

    def get_resources(self, instance, resources):
        """
        Wgets all the resources provided in the app request into the working dir
        :param instance:
        :param resources:
        :return:
        """

        [ self.download_file(resource, instance.get_working_dir()) for resource in resources ]

    def download_file(self, url, path):
        """
        logic that does all the work when downloading the resources
        :param url:
        :param path:
        :return:
        """

        file_name = url.split("/")[-1]
        file_location = path + "/" + file_name

        try:
            os.remove(file_location)
        except OSError:
            pass

        wget.download(url, out=file_location, bar=None)
        return file_location

    def resolve_dependencies(self, dependencies):
        """
        Spawns apt-get install -y for all the dependencies provided
        :param dependencies:
        :return:
        """
        [ self.spawn("apt-get install -y " + dependency) for dependency in dependencies]


class Instance(object):

    def __init__(self):
        """
        Basic DataModel used by the bashh deployer
        :return:
        """

        self.__id = None
        self.__command = None
        self.__working_dir = None

        self.__process = None

    def get_id(self):
        return self.__id

    def get_working_dir(self):
        return self.__working_dir

    def get_command(self):
        return self.__command

    def get_process(self):
        return self.__process

    def set_command(self, command):
        self.__command = command

    def set_id(self, instance_id):
        self.__id = instance_id

    def set_working_dir(self, working_dir):
        self.__working_dir = working_dir

    def set_process(self, process):
        self.__process = process
