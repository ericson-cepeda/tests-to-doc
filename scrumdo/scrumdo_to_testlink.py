import slumber
from colorama import init, Fore, Back, Style
from time import sleep
import local_settings as settings
import string
import re
from models import *
import xml.etree.ElementTree as ET
import os
import argparse

organizations = {}

def main():
    init()
    base_url = "%s/api/v2/" % settings.scrumdo_host
    api = slumber.API(base_url, auth=(settings.scrumdo_username, settings.scrumdo_password))

    read(api)

# Don't go over the throttle limit.
def check_throttle(requests):
    requests += 1
    if requests >= 49:
        sleep(5) # Add in a delay when we get close the our max # of requests per 5 seconds.
        return 0
    return requests

def read(api):
    """
    Get all the organizations information
    """
    # Get all of our organizations and loop through them
    organization_list = api.organizations.get()
    api_count = check_throttle(1)

    for organization in organization_list:

        # Print out the name & slug of each organization (Fore.GREEN colors it...)
        print Fore.GREEN + "%s\t%s" % (organization["name"], organization["slug"])
        new_org = Organization(json = organization, api = api)
        new_org.set_sub_items(api_count)
        organizations[organization["slug"]] = new_org

def export_project(**kwargs):
    """ (str) -> NoneType

    Export a ScrumDo project to a valid XML
    """
    tree = None
    # Search for the required project
    for organization_slug in organizations:
        try:
            tree = ET.fromstring(organizations[organization_slug].export_project(kwargs['project']).encode('utf8').decode("ascii","ignore"))
        except Exception as e:
            print str(e)
            continue
    # Prompt to save a XML file if a correct format was created
    if not tree is None:
        if  kwargs["utestlink"] == True:
            testlink_interaction(ET.tostring(tree), **kwargs)
        elif len(kwargs['ofile']) > 0:
            filename = kwargs['ofile']
            valid_chars = r"[^-_\.\(\)\s%s%s/]+" % (string.ascii_letters, string.digits)

            filename = re.sub(valid_chars, "", filename)
            if os.path.isfile(filename):
                os.remove(filename)
            ET.ElementTree(tree).write(filename,encoding="UTF-8",xml_declaration=True)

def testlink_interaction(project_xml, **kwargs):
    # substitute your Dev Key Here
    client = TestLink(settings.test_link_key,settings.SERVER_URL)
    # get info about the server
    test = open("log.txt", "w")
    test.write(str(client.upload_requirement_specification(project_xml, **kwargs)))
    # Substitute for tcid and tpid that apply to your project
    #result = client.reportTCResult(1132, 56646, "p")
    # Typically you'd want to validate the result here and probably do something more useful with it
    #print "reportTCResult result was: %s" %(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--project', default='', type=str, help='Project to export.')
    parser.add_argument('-o','--ofile', default='', type=str, help='File to save the project.')
    parser.add_argument('-u','--utestlink', action="store_true", default=False, help='Should it be uploaded to TestLink?')
    parser.add_argument('-t','--testproject', default='', type=str, help='TestLink project name.')
    args = parser.parse_args()
    main()
    export_project(**vars(args))
