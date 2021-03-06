#!/usr/bin/python

###
# Copyright (2016) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from ansible.module_utils.basic import *
try:
    from hpOneView.oneview_client import OneViewClient
    from hpOneView.common import transform_list_to_dict

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_ethernet_network_facts
short_description: Retrieve the facts about one or more of the OneView Ethernet Networks.
description:
    - Retrieve the facts about one or more of the Ethernet Networks from OneView.
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 2.0.1"
author:
    - "Camila Balestrin (@balestrinc)"
    - "Mariana Kreisig (@marikrg)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
      required: true
    name:
      description:
        - Ethernet Network name.
      required: false
    options:
      description:
        - "List with options to gather additional facts about an Ethernet Network and related resources.
          Options allowed: associatedProfiles and associatedUplinkGroups."
      required: false
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
'''

EXAMPLES = '''
- name: Gather facts about all Ethernet Networks
  oneview_ethernet_network_facts:
    config: "{{ config_file_path }}"

- debug: var=ethernet_networks

- name: Gather facts about an Ethernet Network by name
  oneview_ethernet_network_facts:
    config: "{{ config_file_path }}"
    name: Ethernet network name

- debug: var=ethernet_networks

- name: Gather facts about an Ethernet Network by name with options
  oneview_ethernet_network_facts:
    config: "{{ config }}"
    name: "{{ name }}"
    options:
      - associatedProfiles
      - associatedUplinkGroups
  delegate_to: localhost

- debug: var=enet_associated_profiles
- debug: var=enet_associated_uplink_groups
'''

RETURN = '''
ethernet_networks:
    description: Has all the OneView facts about the Ethernet Networks.
    returned: Always, but can be null.
    type: complex

enet_associated_profiles:
    description: Has all the OneView facts about the profiles which are using the Ethernet network.
    returned: When requested, but can be null.
    type: complex

enet_associated_uplink_groups:
    description: Has all the OneView facts about the uplink sets which are using the Ethernet network.
    returned: When requested, but can be null.
    type: complex
'''
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class EthernetNetworkFactsModule(object):
    argument_spec = dict(
        config=dict(required=True, type='str'),
        name=dict(required=False, type='str'),
        options=dict(required=False, type='list')
    )

    def __init__(self):
        self.module = AnsibleModule(argument_spec=self.argument_spec,
                                    supports_check_mode=False)
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)
        self.oneview_client = OneViewClient.from_json_file(self.module.params['config'])

    def run(self):
        try:
            ansible_facts = {}
            if self.module.params['name']:
                ethernet_networks = self.__get_by_name(self.module.params['name'])

                if self.module.params.get('options') and ethernet_networks:
                    ansible_facts = self.__gather_optional_facts(self.module.params['options'], ethernet_networks[0])
            else:
                ethernet_networks = self.__get_all()

            ansible_facts['ethernet_networks'] = ethernet_networks

            self.module.exit_json(changed=False, ansible_facts=ansible_facts)

        except Exception as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def __gather_optional_facts(self, options, ethernet_network):
        options = transform_list_to_dict(options)

        ansible_facts = {}

        if options.get('associatedProfiles'):
            ansible_facts['enet_associated_profiles'] = self.__get_associated_profiles(ethernet_network)
        if options.get('associatedUplinkGroups'):
            ansible_facts['enet_associated_uplink_groups'] = self.__get_associated_uplink_groups(ethernet_network)

        return ansible_facts

    def __get_associated_profiles(self, ethernet_network):
        associated_profiles = self.oneview_client.ethernet_networks.get_associated_profiles(ethernet_network['uri'])
        return [self.__get_server_profile_by_uri(x) for x in associated_profiles]

    def __get_associated_uplink_groups(self, ethernet_network):
        uplink_groups = self.oneview_client.ethernet_networks.get_associated_uplink_groups(ethernet_network['uri'])
        return [self.__get_uplink_set_by_uri(x) for x in uplink_groups]

    def __get_uplink_set_by_uri(self, uplink_set_uri):
        return self.oneview_client.uplink_sets.get(uplink_set_uri)

    def __get_server_profile_by_uri(self, server_profile_uri):
        return self.oneview_client.server_profiles.get(server_profile_uri)

    def __get_by_name(self, name):
        return self.oneview_client.ethernet_networks.get_by('name', name)

    def __get_all(self):
        return self.oneview_client.ethernet_networks.get_all()


def main():
    EthernetNetworkFactsModule().run()


if __name__ == '__main__':
    main()
