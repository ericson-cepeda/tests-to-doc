__authors__ = ['Ericson Cepeda <ericson@picorb.com>']
__email__ = "ericson@picorb.com"
__copyright__ = 'Copyright'

from models.item import *

class Story(Item):

    def __init__(self, **kwargs):
        super(Story,self).__init__(**kwargs)
        #print Fore.RED +"\t\t"+ str(self)

    def to_xml(self, index):
        """ (int) -> str
        <requirement>
            <docid><![CDATA[ORQ-002]]></docid>
            <title><![CDATA[Requirement 0004]]></title>
            <node_order>0</node_order>
            <description></description>
            <status><![CDATA[V]]></status>
            <type><![CDATA[1]]></type>
            <expected_coverage><![CDATA[0]]></expected_coverage>
        </requirement>
        """
        xml_string = '<requirement>'
        xml_string += '<docid><![CDATA[#'+str(self.number)+']]></docid>'
        xml_string +=     '<title><![CDATA['+str(self.summary)+']]></title>'
        xml_string +=     '<node_order>'+str(10000-self.number)+'</node_order>'
        xml_string +=     '<description><![CDATA['+self.detail+']]></description>'
        xml_string +=     '<status><![CDATA[V]]></status>'
        xml_string +=     '<type><![CDATA[3]]></type>'
        xml_string +=     '<expected_coverage><![CDATA[1]]></expected_coverage>   '
        xml_string += '</requirement>'
        return xml_string

    def __str__(self):
        return "%s\t%s" % (self.id,self.summary)
