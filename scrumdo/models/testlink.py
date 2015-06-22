__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

import xmlrpclib
import base64

class TestLink():

    def __init__(self, devKey, server_url):
        self.server = xmlrpclib.Server(server_url)
        self.devKey = devKey

    def report_TC_result(self, tcid, tpid, status):
        data = {"devKey":self.devKey, "tcid":tcid, "tpid":tpid, "status":status}
        return self.server.tl.reportTCResult(data)

    def get_info(self):
        return self.server.tl.about()

    def upload_requirement_specification(self, project_xml, **kwargs):
        """ (str) -> str

        Upload the XML specification
        """
        print "Uploading xml file to Testlink"
        test_project = self.get_test_project_by_name(kwargs["testproject"])
        try:
            argsAPI = {'devKey' : self.devKey, 'testprojectid': test_project[0]["id"], 'xmlfile': base64.b64encode(project_xml)}
            return self.server.tl.uploadRequirementXML(argsAPI)
        except Exception as e:
            return test_project

    def get_test_project_by_name(self, test_link_project_name):
        """

        """
        argsAPI = {'devKey' : self.devKey, 'testprojectname':str(test_link_project_name)}
        return self.server.tl.getTestProjectByName(argsAPI)
