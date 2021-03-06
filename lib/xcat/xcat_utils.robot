*** Settings ***

Resource    ../xcat/resource.txt
Resource    ../../lib/resource.txt

Library     SSHLibrary
Library     OperatingSystem
Library     String

*** Keywords  ***

Open Connection And Login To XCAT
    [Documentation]  Open connection and login to xCAT server.
    [Arguments]  ${xcat_host}=${XCAT_HOST}  ${xcat_port}=${XCAT_PORT}

    # Description of argument(s):
    # xcat_host  IP address of the XCAT server.
    # xcat_port  Network port on which XCAT server accepts ssh session.

    Open Connection  ${xcat_host}  port=${xcat_port}
    Login  ${XCAT_USERNAME}  ${XCAT_PASSWORD}

Get List Of BMC Nodes
    [Documentation]  Get list of BMC nodes.
    [Arguments]  ${node_cfg_file_path}=${NODE_CFG_FILE_PATH}

    # Get the list of BMC nodes to be added.
    # This keyword expects file having list of BMC nodes
    # as an input.
    # File should have IP addresses of BMC nodes.

    OperatingSystem.File Should Exist  ${node_cfg_file_path}  msg=cfg file missing.
    File Should Not Be Empty  ${node_cfg_file_path}  msg=Empty config file.

    ${bmc_list} =  OperatingSystem.Get File  ${node_cfg_file_path}
    [Return]  ${bmc_list}

Add Nodes To XCAT
    [Documentation]  Add nodes to XCAT configuration.
    [Arguments]  ${node}  ${username}=${OPENBMC_USERNAME}
    ...          ${password}=${OPENBMC_PASSWORD}

    # Description of the argument(s):
    # node  Name of the node to be added.

    ${cmd_buf}=  Catenate  ${XCAT_DIR_PATH}/mkdef ${node} bmc=${node}
    ...  bmcusername=${username} bmcpassword=${password} mgt=openbmc groups=all
    Execute Command  ${cmd_buf}

Validate Added Node
    [Documentation]  Validate added node.
    [Arguments]  ${node}

    # Description of the argument(s):
    # node  Name of the node.

    ${stdout}  ${stderr}=  Execute Command  ${XCAT_DIR_PATH}/nodels
    ...  return_stderr=True
    Should Be Empty  ${stderr}
    Should Contain  ${std_out}  ${node}  msg=Node is not added.

Power On Via XCAT
    [Documentation]  Power on via XCAT.
    [Arguments]  ${node}

    # Description of the argument(s):
    # node  Name of the node.

    ${stdout}  ${stderr}=  Execute Command  ${XCAT_DIR_PATH}/rpower ${node} on
    ...  return_stderr=True
    Should Be Empty  ${stderr}

Power Off Via XCAT
    [Documentation]  Power off via XCAT.
    [Arguments]  ${node}

    # Description of the argument(s):
    # node  Name of the node.

    ${stdout}  ${stderr}=  Execute Command  ${XCAT_DIR_PATH}/rpower ${node} off
    ...  return_stderr=True
    Should Be Empty  ${stderr}

Get Power Status
    [Documentation]  Get power status via XCAT.
    [Arguments]  ${node}

    # Description of the argument(s):
    # node  Name of the node.

    ${stdout}  ${stderr}=  Execute Command
    ...  ${XCAT_DIR_PATH}/rpower ${node} state  return_stderr=True
    Should Be Empty  ${stderr}

    [Return]  ${stdout}

Add Nodes To Group
    [Documentation]  Add BMC nodes to group.
    [Arguments]  ${node}  ${group}=${GROUP}

    # Description of argument(s):
    # node   Name of the node (e.g. "node1").
    # group  Name of the group (e.g. "openbmc").

    ${stdout}  ${stderr}=  Execute Command
    ...  ${XCAT_DIR_PATH}/chdef ${node} groups=${group}  return_stderr=True
    Should Be Empty  ${stderr}

Get List Of Nodes In Group
    [Documentation]  Get list of nodes in BMC.
    [Arguments]  ${group}=${GROUP}

    # Description of argument(s):
    # group  Name of the group (e.g. "openbmc").

    # Sample output of this keyword:
    # XXX.XXX.XXX.XXX
    # YYY.YYY.YYY.YYY
    # ZZZ.ZZZ.ZZZ.ZZZ

    ${stdout}  ${stderr}=  Execute Command
    ...  ${XCAT_DIR_PATH}/nodels ${group}  return_stderr=True
    Should Be Empty  ${stderr}

    [Return]  ${stdout}

Validate Node Added In Group
    [Documentation]  Validate whether node is added in group.
    [Arguments]  ${node}  ${group}

    # Description of argument(s):
    # node   Name of the node (e.g. "node1").
    # group  Name of the group (e.g. "openbmc").

    ${nodes_in_group}=  Get List Of Nodes In Group  ${group}
    Should Contain  ${nodes_in_group}  ${node}
    ...  msg=BMC node is not added in a group.

# TBD  openbmc/openbmc-test-automation/issues/647
