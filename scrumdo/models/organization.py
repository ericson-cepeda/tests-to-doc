__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

from models.item import Item
from models.project import Project
from scrumdo_to_testlink import check_throttle

class Organization(Item):

    def __init__(self, **kwargs):
        super(Organization,self).__init__(**kwargs)
        self.api_organization = self.api.organizations(self.slug)

    def set_sub_items(self, api_count):
        """ (int)

        Set the projects for the organization
        """
        # Get all of our projects in that organization and loop through them
        project_list = self.api_organization.projects.get()
        api_count = check_throttle(api_count)

        for project in project_list:

            # Print out the project name and slug
            #print Fore.BLUE + "\t%s\t%s" % (project['name'],project['slug'])
            new_project = Project(json = project, api = self.api_organization)
            new_project.set_sub_items(api_count)
            self.add_project(new_project)

    def add_project(self, project):
        """ (Project) -> boolean

        Adds a project to the organization
        """
        # check if project is new
        if not project.id == None:
            # create new iteration
            pass

        # add project to children
        self.sub_items.append(project)

    def export_project(self, slug):
        """ (str) -> str

        Return the project XML structured, if found

        <?xml version="1.0" encoding="UTF-8"?>
            <requirement-specification>
            </requirement-specification>
        """
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>'
        xml_string += "<requirement-specification>"
        for project in self.sub_items:
            if project.slug == slug:
                xml_string += project.to_xml()
        xml_string += "</requirement-specification>"
        return xml_string
