from src.main.python.net.i2cat.cnsmo.lib.message.base import Message


class NewService(Message):

    def __init__(self, service_type=None, service_id=None, service_status=None):
        """
        Most Basic Message exchanged between system state managers and clients.
        It actullay shows that a new service was launched

        :param service_type:
        :param service_id:
        :param service_status:
        :return:
        """
        self.__service_type = service_type
        self.__service_id = service_id
        self.__service_status = service_status

    def get_service_type(self):
        return self.__service_type

    def get_service_id(self):
        return self.__service_id

    def get_service_status(self):
        return self.__service_status


    def set_service_type(self, service_type):
        self.__service_type = service_type

    def set_service_id(self, service_id):
        self.__service_id = service_id

    def set_service_status(self, service_status):
        self.__service_status = service_status

