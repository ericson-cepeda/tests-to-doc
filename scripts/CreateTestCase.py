#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sys import stdout
from django.utils.html import escape
import json
import os
import re
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('TestToRally')


class TestToRally(object):
    """Tests documentation verifier"""

    def __init__(self, rally, config_file, regex_json):
        self.config_file = config_file
        handler = logging.FileHandler(self.config_file['RALLY_LOGGER'])
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        self.rally = rally
        self.errors = {}
        self.authors_to_inform = {}

        with open(regex_json) as regex_file:
            regex_expressions = json.load(regex_file)

        self.file_types = {}
        for file_type, regex in regex_expressions['file_types'].items():
            if file_type not in self.file_types:
                self.file_types[file_type] = {}
            self.file_types[file_type]['test_case'] = re.compile(
                r'{0}'.format(regex['test_case']), re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            self.file_types[file_type]['test_type'] = re.compile(
                r'{0}'.format(regex['test_type']), re.IGNORECASE | re.DOTALL
            )

        self.ignored_tags = regex_expressions['ignored_tags']

        self.re_story_module = re.compile(
            r'{0}'.format(regex_expressions['user_story_module']), re.IGNORECASE | re.DOTALL
        )
        self.re_story_name = re.compile(
            r'{0}'.format(regex_expressions['user_story_name']), re.IGNORECASE | re.DOTALL
        )
        self.re_test_case_name = re.compile(
            r'{0}'.format(regex_expressions['test_case_name']), re.IGNORECASE | re.DOTALL
        )
        self.re_test_folder = re.compile(
            r'{0}'.format(regex_expressions['test_folder']), re.IGNORECASE | re.DOTALL
        )
        self.re_test_contract = re.compile(
            r'{0}'.format(regex_expressions['test_contract']), re.IGNORECASE | re.DOTALL
        )
        self.re_author_id = re.compile(r'.*?([0-9]+)\.js', re.DOTALL)

        #Hipchat integration
        try:
            self.hipster = HypChat(self.config_file['HIPCHAT_TOKEN'])
            self.qe_room = self.hipster.get_user(self.config_file['QE_CHAT']) \
                if 'QE_CHAT_IS_USER' in self.config_file and self.config_file['QE_CHAT_IS_USER'] \
                else self.hipster.get_room(self.config_file['QE_CHAT'])

        except Exception, details:
            log.info('Connection to HipChat was disabled.')
            log.info('REASON: {0}'.format(details))

    def _create_test_cases(self, file_regex_expressions, test_folder_ref, data=''):
        """
            (TestToRally, list, str) -> NoneType

            create test cases on Rally
        """
        # find ocurrences with named groups
        test_cases = file_regex_expressions['test_case'].finditer(data)
        log.info("{0} case(s) found.".format(len(file_regex_expressions['test_case'].findall(data))))
        for test_case in test_cases:
            # retrieve related user story
            user_story = self.rally.get('UserStory', fetch=True, query='FormattedID = "{0}"'.format(test_case.group('story')))

            test_header = file_regex_expressions['test_type'].match(test_case.group('header'))
            test_contract = self.re_test_contract.match(test_case.group('contract'))
            try:
                test_type = test_contract.group('type').title()
            except (IndexError, AttributeError) as e:
                test_type = test_header.group('type').title()

            required_tags = ['QE', test_type]
            # extract module name from user story name
            for i, item in enumerate(user_story.content['QueryResult']['Results']):
                module = self.re_story_module.findall(item['Name'])
                required_tags += module
            for tag in required_tags:
                # create missing tags
                tags = self.rally.get('Tag', fetch=True, projectScopeUp=True, query='Name = "{0}"'.format(tag))
                if len(tags.content['QueryResult']['Results']) < 1:
                    new_tag = dict(
                        Name=escape(tag)
                    )
                    self.rally.put('Tag', new_tag)
            tags = self.rally.get('Tag', fetch=True, projectScopeUp=False, query=' OR '.join(['Name = "{0}"'.format(set_tag) for set_tag in required_tags]))

            for i, item in enumerate(user_story.content['QueryResult']['Results']):
                rally_test_cases = self.rally.get(
                    'TestCase',
                    fetch=True,
                    query='AutomationID = "{0}" AND WorkProduct = "{1}"'.format(test_case.group('header'), item['_ref'])
                )
                is_epic = self._verify_user_story(item)
                if item['FormattedID'] in self.errors or is_epic:
                    continue
                # create test case if missing
                try:
                    current_case = rally_test_cases.content['QueryResult']['Results'][0]
                    if not current_case['TestFolder']['_ref'] == str(test_folder_ref):
                        current_case['TestFolder']['_ref'] = str(test_folder_ref)
                        self.rally.post('TestCase', current_case)
                except IndexError:
                    test_case_name = self.re_story_name.match(item['Name']).group('objective').strip()
                    test_case_name = test_case_name[:1].upper()+test_case_name[1:]
                    new_test_case = dict(
                        Name=escape('{2}, {0}: {1}'.format(test_case_name, test_header.group('objective'), item['FormattedID'])),
                        Description="",
                        Type=test_type,
                        Method='Automated',
                        WorkProduct=item['_ref'],
                        AutomationID=test_case.group('header'),
                        Tags=tags.content['QueryResult']['Results'],
                        Priority='Important',
                        TestFolder=str(test_folder_ref),
                    )
                    try:
                        case_author = self.rally.get(
                            'User',
                            fetch=True,
                            query='UserName = "{0}"'.format(
                                self.config_file['COMPANY_DOMAIN'].format(test_contract.group('author'))
                            )
                        )
                        new_test_case['Owner'] = case_author.next()._ref
                    except:
                        new_test_case['Owner'] = item['Owner']['_ref']
                    self.rally.put('TestCase', new_test_case)

    def _define_test_folder(self, test_folder):
        """
            (TestToRally, str) -> str

            create or get a test folder on Rally based on a directory containing test files

            return test folder to be used on Rally
        """
        # verify test folder exists
        test_folder_items = self.rally.get('TestFolder', fetch=True, query='Name = "{0}"'.format(test_folder))
        if len(test_folder_items.content['QueryResult']['Results']) < 1:
            new_folder = dict(
                            Name=escape(test_folder)
                        )
            # Create test folder
            self.rally.put('TestFolder', new_folder)
            test_folder_items = self.rally.get('TestFolder', fetch=True, query='Name = "{0}"'.format(test_folder))
        return test_folder_items.next()._ref

    def _verify_user_story(self, user_story):
        """
            (TestToRally, dict) -> boolean

            verify the user story relevant attributes format

            return whether the user story is an epic
        """

        # verify name <module>: As a <persona>,I need <objective>, so that <achievement>.
        errors = {}
        if not self.re_story_module.match(user_story['Name']):
            errors['module'] = True
        if not self.re_story_name.match(user_story['Name']):
            errors['name'] = True

        if 'test_cases' in user_story and len(user_story['test_cases']) == 0:
            errors['test_cases'] = True

        # verify tags
        tag_names = [tag['_refObjectName'] for tag in user_story['Tags']]
        module = self.re_story_module.match(user_story['Name'])
        is_epic = set(self.ignored_tags).intersection(tag_names) or module and module.group('module') in self.ignored_tags
        # fill report
        if not is_epic and len(errors.keys()) > 0 and not user_story['FormattedID'] in self.errors:
            self.errors[user_story['FormattedID']] = errors
            # retrieve author
            if user_story['Owner']:
                author_id = self.re_author_id.search(user_story['Owner']['_ref']).group(1)
                if not author_id in self.authors_to_inform:
                    owner = self.rally.get('User', fetch=True, query="ObjectID = {0}".format(author_id)).next()
                    try:
                        owner_mention = self.hipster.get_user(owner.EmailAddress).mention_name
                    except Exception as e:
                        owner_mention = owner.EmailAddress
                    self.authors_to_inform[author_id] = {'mention_name': owner_mention, 'stories': {}}
                self.authors_to_inform[author_id]['stories'][user_story['FormattedID']] = self\
                    .config_file['INFORM_URL']\
                    .format(project=self.rally.getProject().ObjectID, story=user_story['ObjectID'])
        return is_epic

    def _verify_test_case(self, test_case):
        """
            (TestToRally, dict) -> NoneType

            verify the test case relevant attributes format
        """

        errors = {}
        # verify name <objective>: <automation_id>
        if not self.re_test_case_name.match(test_case['Name']):
            errors['name'] = True
        if not test_case['AutomationID']:
            errors['automation'] = True

        # TODO verify tags
        tag_names = [tag['_refObjectName'] for tag in test_case['Tags']]
        # fill report
        if len(errors.keys()) > 0 and not test_case['FormattedID'] in self.errors:
            self.errors[test_case['FormattedID']] = errors

    def _send_errors_message(self, kwargs):
        stories_message = "{task_name}, {project}: {by_name} stories with wrong format. "\
            "{by_module} stories do not state their module. "\
            "{by_cases} stories without test cases. "\
            "{by_automation} test cases without automation ID.".format(
                by_name=sum('name' in story for id, story in self.errors.items()),
                by_module=sum('module' in story for id, story in self.errors.items()),
                by_cases=sum('test_cases' in story for id, story in self.errors.items()),
                by_automation=sum('automation' in test_case for id, test_case in self.errors.items()),
                **kwargs
            )

        mention_message = '; '.join([
            '@{mention_name}: {stories} stories with issues: {links}'.format(
                mention_name=owner['mention_name'],
                stories=len(owner['stories']),
                links=', '.join(owner['stories'].values())
            ) for id, owner in self.authors_to_inform.items()
        ])
        try:
            self.qe_room.message(stories_message)
            if len(mention_message) > 0:
                self.qe_room.message(mention_message)
        except Exception:
            log.info(stories_message)
            log.info(mention_message)

    def files_to_test_cases(self, **kwargs):
        """
            (TestToRally) -> NoneType

            initialize Rally connection and test case creation script
        """
        hashes = '#' * 25
        start = 'START CreateTestCase LOG'
        end = 'END CreateTestCase LOG'
        log.info('%s %s %s\n' % (hashes, start, hashes))

        def explore_path(tests_path):
            for subdir, dirs, files in os.walk(tests_path):
                for file in files:
                    with open(subdir+'/'+file) as myfile:
                        data = myfile.read()

                        test_folder = os.path.basename(os.path.dirname(subdir+'/'+file))

                        test_folder_by_class = self.re_test_folder.search(data)
                        if test_folder_by_class:
                            test_folder = test_folder_by_class.group('test_folder')
                        elif 'test_folder' in kwargs and kwargs['test_folder']:
                            test_folder = kwargs['test_folder']

                        test_folder_ref = self._define_test_folder(test_folder)
                        file_type = file.split('.')[1]
                        if file_type in self.file_types:
                            log.info('Test folder: {0}'.format(test_folder))
                            log.info(subdir+'/'+file)
                            self._create_test_cases(self.file_types[file_type], test_folder_ref, data=data)

        try:
            self.rally.setWorkspace(self.config_file['RALLY_WORKSPACE'])
            # Make sure it is reading a directory
            if os.path.isdir(kwargs['tests_path']):
                explore_path(kwargs['tests_path'])
                self._send_errors_message(kwargs)
            else:
                log.error('You should pass a valid tests path.\n')
        except Exception, details:
            log.error('Error found executing the script: "%s"\n' % details)
        log.info('%s  %s  %s\n' % (hashes, end, hashes))

    def documentation_format_report(self, **kwargs):
        # retrieve project user stories
        user_stories = self.rally.get('UserStory', fetch=True, pagesize=200).content['QueryResult']
        while len(user_stories['Results']) < user_stories['TotalResultCount']:
            next_user_stories = self.rally.get('UserStory', fetch=True, pagesize=200, start=len(user_stories['Results'])+1).content['QueryResult']
            user_stories['Results'] += next_user_stories['Results']

        # retrieve test cases
        test_cases = self.rally.get('TestCase', fetch=True, pagesize=200).content['QueryResult']
        while len(test_cases['Results']) < test_cases['TotalResultCount']:
            next_test_cases = self.rally.get('TestCase', fetch=True, pagesize=200, start=len(test_cases['Results'])+1).content['QueryResult']
            test_cases['Results'] += next_test_cases['Results']

        # loop through test cases
        story_cases = {}
        for test_case in test_cases['Results']:
            # verify test case
            self._verify_test_case(test_case)
            if test_case['WorkProduct']:
                if not test_case['WorkProduct']['_ref'] in story_cases:
                    story_cases[test_case['WorkProduct']['_ref']] = list()
                story_cases[test_case['WorkProduct']['_ref']].append(test_case)

        # loop through user stories
        for user_story in user_stories['Results']:
            # verify individual story
            story_test_cases = story_cases[user_story['_ref']] if user_story['_ref'] in story_cases else []
            user_story['test_cases'] = story_test_cases
            self._verify_user_story(user_story)

        self._send_errors_message(kwargs)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('regex_json', help='Absolute path to REGEX file')
    parser.add_argument('config_file', help='Absolute path to config file')
    parser.add_argument('task_name', help='Task name')
    parser.add_argument('project', help='Project name')
    parser.add_argument('tests_path', help='Absolute Path to the tests folder')
    parser.add_argument('--test_folder', help='Rally test folder')
    args = parser.parse_args()
    if args.tests_path.strip() != '':
        from pyral import Rally
        from time import sleep
        #TODO Hipchat integration
        from hypchat import HypChat

        # Switch to know if the script got the connection to the Rally server
        connected = False
        # Try to reconnect to the server it the connection fails
        for retry in range(0, 4):
            try:
                with open(args.config_file) as config_file:
                    config = json.load(config_file)
                rally = Rally(config['RALLY_SERVER'], config['RALLY_USER'], config['RALLY_PASSWORD'], WORKSPACE=config['RALLY_WORKSPACE'])
                rally.enableLogging(config['RALLY_LOGGER'])
                rally.setProject(args.project)
                connected = True
                break
            except Exception, details:
                log.error('Cannot connect to the Rally Server.\n')
                log.error('DETAILS: %s' % details)
                log.info('Retrying (try #%d)...\n\n' % (retry+1))
                sleep(5)
        if not connected:
            log.error('The connection to the Rally server has failed.')
            exit(0)

        tests_path = args.tests_path
        teststorally = TestToRally(rally, config, args.regex_json)
        task_name = args.task_name
        if task_name in dir(teststorally):
            getattr(teststorally, task_name)(**vars(args))
    else:
        log.error("You should pass project and tests path\n")
        exit(0)  # Exit without errors, avoid mark the build as FAILURE
