*** Settings ***
Documentation       Test Error logging.

Resource            ../lib/connection_client.robot
Resource            ../lib/openbmc_ffdc.robot
Resource            ../lib/utils.robot
Resource            ../lib/state_manager.robot
Resource            ../lib/ipmi_client.robot

Suite Setup         Run Keywords  Verify logging-test  AND
...                 Delete Error Logs
Test Setup          Open Connection And Log In
Test Teardown       Close All Connections
Suite Teardown      Delete Error Logs

*** Test Cases ***

Create Test Error And Verify
    [Documentation]  Create error logs and verify via REST.
    [Tags]  Create_Test_Error_And_Verify

    Create Test Error Log
    Verify Test Error Log


Test Error Persistency On Restart
    [Documentation]  Restart logging service and verify error logs don't exist.
    [Tags]  Test_Error_Persistency_On_Restart

    Create Test Error Log
    Verify Test Error Log
    Execute Command On BMC
    ...  systemctl restart xyz.openbmc_project.Logging.service
    Sleep  10s  reason=Wait for logging service to restart properly.
    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}${1}
    Should Be Equal As Strings  ${resp.status_code}  ${HTTP_NOT_FOUND}


Test Error Persistency On Reboot
    [Documentation]  Reboot BMC and verify error logs don't exist.
    [Tags]  Test_Error_Persistency_On_Reboot

    Create Test Error Log
    Verify Test Error Log
    Initiate BMC Reboot
    Wait Until Keyword Succeeds  10 min  10 sec
    ...  Is BMC Ready
    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}${1}
    Should Be Equal As Strings  ${resp.status_code}  ${HTTP_NOT_FOUND}


Create Test Error And Verify Resolved Field
    [Documentation]  Create error log and verify "Resolved"
    ...              field is 0.
    [Tags]  Create_Test_Error_And_Verify_Resolved_Field

    # Example Error log:
    #  "/xyz/openbmc_project/logging/entry/1": {
    #    "AdditionalData": [
    #        "STRING=FOO"
    #    ],
    #    "Id": 1,
    #    "Message": "example.xyz.openbmc_project.Example.Elog.AutoTestSimple",
    #    "Resolved": 0,
    #    "Severity": "xyz.openbmc_project.Logging.Entry.Level.Error",
    #    "Timestamp": 1490817164983,
    #    "associations": []
    # },

    # It's work in progress, but it's mnfg need. To mark an error as
    # resolved, without deleting the error, mfg will set this bool
    # property.
    # In this test context we are making sure "Resolved" field is "0"
    # by default.

    Delete Error Logs
    Create Test Error Log
    ${resolved}=  Read Attribute  ${BMC_LOGGING_ENTRY}${1}  Resolved
    Should Be True  ${resolved} == 0


Create Test Errors And Verify Time Stamp
    [Documentation]  Create error logs and verify time stamp.
    [Tags]  Create_Test_Error_And_Verify_Time_Stamp

    # Example Error logs:
    #  "/xyz/openbmc_project/logging/entry/1": {
    #    "AdditionalData": [
    #        "STRING=FOO"
    #    ],
    #    "Id": 1,
    #    "Message": "example.xyz.openbmc_project.Example.Elog.AutoTestSimple",
    #    "Resolved": 0,
    #    "Severity": "xyz.openbmc_project.Logging.Entry.Level.Error",
    #    "Timestamp": 1490818990051,  <--- Time stamp
    #    "associations": []
    #  },
    #  "/xyz/openbmc_project/logging/entry/2": {
    #    "AdditionalData": [
    #        "STRING=FOO"
    #    ],
    #    "Id": 2,
    #    "Message": "example.xyz.openbmc_project.Example.Elog.AutoTestSimple",
    #    "Resolved": 0,
    #    "Severity": "xyz.openbmc_project.Logging.Entry.Level.Error",
    #    "Timestamp": 1490818992116,   <---- Time stamp
    #    "associations": []
    # },

    Delete Error Logs
    Create Test Error Log
    Create Test Error Log
    # The error log generated is associated with the epoc time and unique
    # for every error and in increasing time stamp.
    ${time_stamp1}=  Read Attribute  ${BMC_LOGGING_ENTRY}${1}  Timestamp
    ${time_stamp2}=  Read Attribute  ${BMC_LOGGING_ENTRY}${2}  Timestamp
    Should Be True  ${time_stamp2} > ${time_stamp1}

Create Test Error Log And Delete
    [Documentation]  Create an error log and delete it.
    [Tags]  Create_Test_Error_Log_And_Delete

    Delete Error Logs And Verify
    Create Test Error Log
    Delete Error Logs And Verify

Create Multiple Test Error Logs And Delete All
    [Documentation]  Create multiple error logs and delete all.
    [Tags]  Create_Multiple_Test_Error_Logs_And_Delete_All

    Delete Error Logs And Verify
    Create Test Error Log
    Create Test Error Log
    Create Test Error Log
    Delete Error Logs And Verify

Create Two Test Error Logs And Delete One
    [Documentation]  Create two error logs and delete the first entry.
    [Tags]  Create_Two_Test_Error_Logs_And_Delete_One

    Delete Error Logs And Verify
    Create Test Error Log
    ${entry_id}=  Read Attribute  ${BMC_LOGGING_ENTRY}${1}  Id
    Create Test Error Log
    Delete Error log Entry  ${BMC_LOGGING_ENTRY}/${entry_id}
    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}/${entry_id}
    Should Be Equal As Strings  ${resp.status_code}  ${HTTP_NOT_FOUND}
    Delete Error Logs And Verify


Verify IPMI SEL Version
    [Documentation]  Verify IPMI SEL's version info.
    [Tags]  Verify_IPMI_SEL_Version

    ${version_info}=  Get IPMI SEL Setting  Version
    ${setting_status}=  Fetch From Left  ${version_info}  (
    ${setting_status}=  Evaluate  $setting_status.replace(' ','')

    Should Be True  ${setting_status} >= 1.5
    Should Contain  ${version_info}  v2compliant  case_insensitive=True


*** Keywords ***

Get IPMI SEL Setting
    [Documentation]  Returns status for given IPMI SEL setting.
    [Arguments]  ${setting}
    # Description of argument(s):
    # setting  SEL setting which needs to be read(e.g. "Last Add Time").

    ${resp}=  Run IPMI Standard Command  sel info

    ${setting_line}=  Get Lines Containing String  ${resp}  ${setting}
    ...  case-insensitive
    ${setting_status}=  Fetch From Right  ${setting_line}  :
    ${setting_status}=  Evaluate  $setting_status.replace(' ','')

    [Return]  ${setting_status}


Verify logging-test
    [Documentation]  Verify existence of prerequisite logging-test.

    Open Connection And Log In
    ${out}  ${stderr}=  Execute Command  which logging-test  return_stderr=True
    Should Be Empty  ${stderr}
    Should Contain  ${out}  logging-test

Clear Existing Error Logs
    [Documentation]  If error log isn't empty, reboot the BMC to clear the log.

    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}${1}
    Return From Keyword If  ${resp.status_code} == ${HTTP_NOT_FOUND}
    Initiate BMC Reboot
    Wait Until Keyword Succeeds  10 min  10 sec
    ...  Is BMC Ready
    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}${1}
    Should Be Equal As Strings  ${resp.status_code}  ${HTTP_NOT_FOUND}

Create Test Error Log
    [Documentation]  Generate test error log.

    # Test error log entry example:
    # "/xyz/openbmc_project/logging/entry/1":  {
    #     "AdditionalData": [
    #         "STRING=FOO"
    #     ],
    #     "Id": 1,
    #     "Message": "example.xyz.openbmc_project.Example.Elog.AutoTestSimple",
    #     "Severity": "xyz.openbmc_project.Logging.Entry.Level.Error",
    #     "Timestamp": 1487743963328,
    #     "associations": []
    # }

    Execute Command On BMC  logging-test -c AutoTestSimple

Verify Test Error Log
    [Documentation]  Verify test error log entries.
    ${entry_id}=  Read Attribute  ${BMC_LOGGING_ENTRY}${1}  Message
    Should Be Equal  ${entry_id}
    ...  example.xyz.openbmc_project.Example.Elog.AutoTestSimple
    ${entry_id}=  Read Attribute  ${BMC_LOGGING_ENTRY}${1}  Severity
    Should Be Equal  ${entry_id}
    ...  xyz.openbmc_project.Logging.Entry.Level.Error

Delete Error Logs And Verify
    [Documentation]  Delete all error logs and verify.

    Delete Error Logs
    ${resp}=  OpenBMC Get Request  ${BMC_LOGGING_ENTRY}/list
    Should Be Equal As Strings  ${resp.status_code}  ${HTTP_NOT_FOUND}
