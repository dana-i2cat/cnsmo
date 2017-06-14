import time
import subprocess
import signal
import getopt
import sys
import os


class AppDeployer:
    process = None

    def __init__(self):
        self.process = None

    def start_app(self, command):
        if self.process is not None:
            return None

        print("Starting app " + command)
        shell_command = command
        self.process = subprocess.Popen(shell_command, shell=True, preexec_fn=os.setsid)
        print("Started app " + command + "with pid " + str(self.process.pid))
        return self.process

    def stop_app(self):
        if self.process is not None:
            print("Stopping app...")
            print("Signalling for termination...")
            print(self.process.pid)
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            time.sleep(2)
            print("Stopped app")


class SignalFlag:
    """
    A single-use flag for SIGINT and SIGTERM signals.
    """
    __signal_received = False

    def __init__(self):
        """
        Registers callback for SIGINT and SIGTERM
        """
        signal.signal(signal.SIGINT, self.flag_signal)
        signal.signal(signal.SIGTERM, self.flag_signal)

    def flag_signal(self, signum, frame):
        """
        Flags
        :param signum:
        :param frame:
        :return:
        """
        self.__signal_received = True

    def signal_received(self):
        return self.__signal_received

# A script that launches given command in a new process,
# waits 10 seconds
# and terminates the generated processes tree with SIGTERM.
# Serves as a demonstrator for the mechanism implemented in BashDeployer to launch and stop apps.
# Usage: python deployer.py -c 'COMMAND'
# e.g. python deployer.py -c 'python infiniteloop.py'
# Checking that python infiniteloop.py has been terminated can be checked with the command 'ps aux | grep python'
if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "c:")
    for opt, arg in opts:
        if opt == "-c":
            command = arg

    signal_flag = SignalFlag()
    deployer = AppDeployer()
    deployer.start_app(command)

    time.sleep(10)
    #print("Waiting for interruption or termination to stop app")
    #while not signal_flag.signal_received():
    #    time.sleep(0.5)
    print("Stopping app from deployer...")
    deployer.stop_app()

    # finish script with the second interruption
    #print("Waiting for interruption or termination to finish deployer")
    #signal_flag = SignalFlag()
    #while not signal_flag.signal_received():
    #    time.sleep(0.5)
