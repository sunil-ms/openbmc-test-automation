*** Settings ***

Documentation   This testsuite is for testing the Boot Device Functions

Resource        ../lib/rest_client.robot
Resource        ../lib/ipmi_client.robot
Resource        ../lib/openbmc_ffdc.robot
Resource        ../lib/utils.robot

Suite Setup     Test Suite Setup
Test Setup      Pre Test Case Execution
Test Teardown   Post Test Case Execution
Suite Teardown  Close All Connections

*** Variables ***

${HOST_SETTINGS}  ${SETTINGS_URI}host0

*** Test Cases ***

Set The Boot Device As Default Using REST API
    [Documentation]  This testcase is to set the boot device as default using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_Default_Using_REST_API

    ${bootDevice}=  Set Variable  Default
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Default
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  No override

Set The Boot Device As Default Using Ipmitool
    [Documentation]  This testcase is to set the boot device as default using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
    [Tags]  Set_The_Boot_Device_As_Default_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x00 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Default
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  No override

Set The Boot Device As Network Using REST API
    [Documentation]  This testcase is to set the boot device as Network using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_Network_Using_REST_API

    ${bootDevice}=  Set Variable  Network
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Network
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force PXE

Set The Boot Device As Network Using Ipmitool
    [Documentation]  This testcase is to set the boot device as Network using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
    [Tags]  Set_The_Boot_Device_As_Network_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x04 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Network
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force PXE

Set The Boot Device As Disk Using REST API
    [Documentation]  This testcase is to set the boot device as Disk using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_Disk_Using_REST_API

    ${bootDevice}=  Set Variable  Disk
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Disk
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot from default Hard-Drive

Set The Boot Device As Disk Using Ipmitool
    [Documentation]  This testcase is to set the boot device as Disk using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
    [Tags]  Set_The_Boot_Device_As_Disk_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x08 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Disk
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot from default Hard-Drive

Set The Boot Device As Safe Using REST API
    [Documentation]  This testcase is to set the boot device as Safe using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_Safe_Using_REST_API

    ${bootDevice}=  Set Variable  Safe
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Safe
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Safe-Mode

Set The Boot Device As Safe Using Ipmitool
    [Documentation]  This testcase is to set the boot device as Safe using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
    [Tags]  Set_The_Boot_Device_As_Safe_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x0C 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Safe
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Safe-Mode

Set The Boot Device As CDROM Using REST API
    [Documentation]  This testcase is to set the boot device as CDROM using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_CDROM_Using_REST_API

    ${bootDevice}=  Set Variable  CDROM
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  CDROM
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot from CD/DVD

Set The Boot Device As CDROM Using Ipmitool
    [Documentation]  This testcase is to set the boot device as CDROM using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
   [Tags]  Set_The_Boot_Device_As_CDROM_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x14 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  CDROM
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot from CD/DVD

Set The Boot Device As Setup Using REST API
    [Documentation]  This testcase is to set the boot device as Setup using REST
    ...              URI. The Boot device is read using REST API and ipmitool.
    [Tags]  Set_The_Boot_Device_As_Setup_Using_REST_API

    ${bootDevice}=  Set Variable  Setup
    ${valueDict}=  Create Dictionary  data=${bootDevice}
    Write Attribute  ${HOST_SETTINGS}  boot_flags  data=${valueDict}
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Setup
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot into BIOS Setup

Set The Boot Device As Setup Using Ipmitool
    [Documentation]  This testcase is to set the boot device as Setup using
    ...              ipmitool. The Boot device is read using REST API and
    ...              ipmitool.
    [Tags]  Set_The_Boot_Device_As_Setup_Using_Ipmitool

    Run IPMI command  0x0 0x8 0x05 0x80 0x18 0x00 0x00 0x00
    Read the Attribute  ${HOST_SETTINGS}  boot_flags
    Response Should Be Equal  Setup
    ${output}=  Run IPMI Standard Command  chassis bootparam get 5
    Should Contain  ${output}  Force Boot into BIOS Setup

*** Keywords ***

Response Should Be Equal
    [Arguments]  ${args}
    Should Be Equal  ${OUTPUT}  ${args}

Read the Attribute
    [Arguments]  ${uri}  ${parm}
    ${output}=  Read Attribute  ${uri}  ${parm}
    Set Test Variable  ${OUTPUT}  ${output}

Pre Test Case Execution
   [Documentation]  Do the pre test setup.

   Open Connection And Log In
   Initialize DBUS cmd  "boot_flags"

Post Test Case Execution
   [Documentation]  Do the post test teardown.

   FFDC On Test Case Fail
   Close All Connections

Test Suite Setup
    [Documentation]  Do the initial suite setup.
    ${current_state}=  Get Host State
    Run Keyword If  '${current_state}' == 'Off'
    ...  Initiate Host Boot

    Wait Until Keyword Succeeds
    ...  10 min  10 sec  Is OS Starting
