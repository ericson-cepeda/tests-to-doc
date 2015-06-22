__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

from colorama import Fore

class Item(object):
    """
    Provide general instance variables
    """
    api = None

    def __init__(self, **kwargs):
        self.slug = None
        self.id = None
        self.sub_items = []

        self.api = kwargs.get("api")

        # Set self attributes
        json = kwargs.get("json", {})

        self.id = json['id']

        # Attributes for organizations and projects
        if "slug" in json:
            self.slug = json['slug']
        if "name" in json:
            self.name = json['name']
        # Attributes for iterations
        if "url" in json:
            self.url = json['url']
        # Attributes for stories
        if "summary" in json:
            self.summary = json['summary']
        if "detail" in json:
            self.detail = json['detail']
        if "number" in json:
            self.number = json['number']
