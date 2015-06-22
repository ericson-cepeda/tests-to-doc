__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

from models.item import *
from models.story import Story
from scrumdo_to_testlink import check_throttle

class Iteration(Item):

    def __init__(self, **kwargs):
        super(Iteration,self).__init__(**kwargs)
        self.completed_tasks = 0
        self.points = 0
        self.api_iteration = self.api.iterations(self.id)
        #print Fore.YELLOW + "\t\t%s %s to %s" % (iteration['name'], iteration['start_date'], iteration['end_date'])

    def set_sub_items(self, api_count):
        """ (int)

        Set the stories for the iteration
        """
        # Get all the stories in the iteration
        story_list = self.api_iteration.stories.get()
        api_count = check_throttle(api_count)

        # Compute some summary data for each iteration and print it out
        print Fore.YELLOW + "\t\t%s" % (self.url)
        for story in story_list:
            self.completed_tasks += story['completed_task_count']
            self.points += story['points_value']
            new_story = Story(json = story, api = self.api_iteration)
            self.add_story(new_story)
        print Fore.YELLOW + "\t\t\t%d Stories, %d Points, %d Completed tasks" % (len(story_list), self.points, self.completed_tasks)

    def add_story(self, story):
        """ (Story) -> boolean

        Add a story to the iteration
        """
        # check if story is new
        if not story.id == None:
            # create new iteration
            pass

        # add story to children
        self.sub_items.append(story)

    def to_xml(self,count):
        """ (int) -> json

        Export the stories to xml and count them
        """
        xml_string = ""
        for story in self.sub_items:
            xml_string += story.to_xml(count)
            count+=1
        return {'xml': xml_string, 'count': count}
