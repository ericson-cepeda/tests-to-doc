__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

from models.item import *
from models.iteration import Iteration
from scrumdo_to_testlink import check_throttle

class Project(Item):

    def __init__(self, **kwargs):
        # Initializes super class
        super(Project,self).__init__(**kwargs)
        self.api_project = self.api.projects(self.slug)
        # Print out the project name and slug
        print Fore.BLUE + "\t%s\t slug: %s" % (self.name,self.slug)

    def set_sub_items(self, api_count):
        """ (int)

        Set the iterations for the project
        """

        # Get all the iterations...
        iteration_list = self.api_project.iterations.get()
        api_count = check_throttle(api_count)

        for iteration in iteration_list:
            #print Fore.YELLOW + "\t\t%s %s to %s" % (iteration['name'], iteration['start_date'], iteration['end_date'])
            new_iteration = Iteration(json = iteration, api = self.api_project)
            new_iteration.set_sub_items(api_count)
            self.add_iteration(new_iteration)

    def add_iteration(self, iteration):
        """ (Iteration) -> boolean

        Adds an iteration to the project
        """
        # check if iteration is new
        if not iteration.id == None:
            # create new iteration
            pass

        # add iteration to children
        self.sub_items.append(iteration)

    def to_xml(self):
        """
        Export the project to XML

        <req_spec title="Oleg Spec - 001" doc_id="Oleg-SPEC-L1-001">
            <type><![CDATA[0]]></type>
            <node_order><![CDATA[0]]></node_order>
            <total_req><![CDATA[2]]></total_req>
            <scope>
                <![CDATA[Req. Spec LEVEL 1 - 001]]>
            </scope>
        </req_spec>
        """
        xml_string = '<req_spec title="Stories" doc_id="ScrumDo">'
        story_count = 0
        for iteration in self.sub_items:
            result = iteration.to_xml(story_count)
            xml_string += result['xml']
            story_count = result['count']
        xml_string += "</req_spec>"
        return xml_string

    def __str__(self):
        return "%s" % (self.name)
