import json


class Message(object):
    """
    Base class for messages.
    Messages are the data exchanged between the system State Manager and its clients,
    it does not define any specific class attribute. It just provide helper
    """

    def dictionarize(self):
        """
        Composes a dictionary containing the plane name of all the attributes that
        have getter functions and its value.
        :return: dictionary
        """
        return { method[4:]:getattr(self, method)() for method in dir(self) if method.startswith("get_") }

    def jsonify(self):
        """
        Wraps objectify function to return JSON output
        :return:
        """
        return json.dumps(self.dictionarize())

    def objectify(self, **params_dict):
        """
        For every param in the input dictionary , tries to call the correct setter function
        and adds its value

        :param params_dict:
        :return:
        """
        [ getattr(self, "set_" + param_name)(param_value) for param_name, param_value in params_dict.iteritems() ]

    def objectify_from_json(self, json_stream):
        """
        Wraps Objectify to parse a JSON stream
        :param json_stream:
        :return:
        """
        if json_stream:
            self.objectify(**json.loads(json_stream))