#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2019  Infobyte LLC (http://www.infobytesec.com/)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for `faraday_agent_dispatcher` package."""

import json
import os
import pytest
import sys

from pathlib import Path
from itsdangerous import TimestampSigner

from faraday_agent_dispatcher.dispatcher import Dispatcher
from faraday_agent_dispatcher.config import (
    reset_config,
    save_config,
    instance as configuration,
    Sections
)

from tests.utils.text_utils import fuzzy_string
from tests.utils.testing_faraday_server import FaradayTestConfig, test_config, tmp_custom_config, tmp_default_config, \
    test_logger_handler, test_logger_folder


@pytest.mark.parametrize('config_changes_dict',
                         [{"remove": {Sections.SERVER: ["host"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {Sections.SERVER: ["api_port"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.SERVER: {"api_port": "Not a port number"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.SERVER: {"api_port": "6000"}}},  # None error as parse int
                          {"remove": {Sections.SERVER: ["websocket_port"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.SERVER: {"websocket_port": "Not a port number"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.SERVER: {"websocket_port": "9001"}}},  # None error as parse int
                          {"remove": {Sections.SERVER: ["workspace"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {Sections.TOKENS: ["registration"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {"registration": "invalid_token"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {"registration": "   46aasdje446aasdje446aa"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {"registration": "QWE46aasdje446aasdje446aa"}}},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {"agent": "invalid_token"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {
                               "agent": "   46aasdje446aasdje446aa46aasdje446aasdje446aa46aasdje446aasdje"
                           }},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.TOKENS: {
                               "agent": "QWE46aasdje446aasdje446aaQWE46aasdje446aasdje446aaQWE46aasdje446"}}},
                          {"remove": {Sections.EXECUTOR_DATA.format("ex1"): ["cmd"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.EXECUTOR_DATA.format("ex1"): {"max_size": "ASDASD"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.EXECUTOR_PARAMS.format("ex1"): {"param1": "ASDASD"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.EXECUTOR_PARAMS.format("ex1"): {"param1": "5"}},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.EXECUTOR_PARAMS.format("ex1"): {"param1": "True"}}
                           },
                          {"remove": {Sections.AGENT: ["agent_name"]},
                           "replace": {},
                           "expected_exception": ValueError},
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": "ex1,ex1"}},
                           "expected_exception": ValueError
                           },
                          {"remove": {Sections.AGENT: ["section"]},
                           "replace": {},
                           "expected_exception": ValueError
                           },
                          {"remove": {Sections.TOKENS: ["section"]},
                           "replace": {},
                           "expected_exception": ValueError
                           },
                          {"remove": {Sections.SERVER: ["section"]},
                           "replace": {},
                           "expected_exception": ValueError
                           },
                          {"remove": {},
                           "replace": {},
                           "duplicate_exception": True,
                           "expected_exception": ValueError
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": "ex1, ex2"}},
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": "ex1,ex2 "}},
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": " ex1,ex2"}},
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": " ex1, ex2 , ex3"}},
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": "ex1,ex 1"}},
                           "expected_exception": ValueError
                           },
                          {"remove": {},
                           "replace": {Sections.AGENT: {"executors": "ex1,ex8"}},
                           "expected_exception": ValueError
                           },
                          {"remove": {},
                           "replace": {}}
                          ])
def test_basic_built(tmp_custom_config, config_changes_dict):
    for section in config_changes_dict["replace"]:
        for option in config_changes_dict["replace"][section]:
            if section not in configuration:
                configuration.add_section(section)
            configuration.set(section, option, config_changes_dict["replace"][section][option])
    for section in config_changes_dict["remove"]:
        if "section" in config_changes_dict["remove"][section]:
            configuration.remove_section(section)
        else:
            for option in config_changes_dict["remove"][section]:
                configuration.remove_option(section, option)
    tmp_custom_config.save()
    if "expected_exception" in config_changes_dict:
        if "duplicate_exception" in config_changes_dict and config_changes_dict["duplicate_exception"]:
            with open(tmp_custom_config.config_file_path, "r") as file:
                content = file.read()
            with open(tmp_custom_config.config_file_path, "w") as file:
                file.write(content)
                file.write(content)
        with pytest.raises(config_changes_dict["expected_exception"]):
            Dispatcher(None, tmp_custom_config.config_file_path)
    else:
        Dispatcher(None, tmp_custom_config.config_file_path)


async def test_start_and_register(test_config: FaradayTestConfig, tmp_default_config):
    # Config
    configuration.set(Sections.SERVER, "api_port", str(test_config.client.port))
    configuration.set(Sections.SERVER, "host", test_config.client.host)
    configuration.set(Sections.SERVER, "workspace", test_config.workspace)
    configuration.set(Sections.TOKENS, "registration", test_config.registration_token)
    configuration.set(Sections.EXECUTOR_DATA.format("ex1"), "cmd", 'exit 1')
    tmp_default_config.save()

    # Init and register it
    dispatcher = Dispatcher(test_config.client.session, tmp_default_config.config_file_path)
    await dispatcher.register()

    # Control tokens
    assert dispatcher.agent_token == test_config.agent_token

    signer = TimestampSigner(test_config.app_config['SECRET_KEY'], salt="websocket_agent")
    agent_id = int(signer.unsign(dispatcher.websocket_token).decode('utf-8'))
    assert test_config.agent_id == agent_id


async def test_start_with_bad_config(test_config: FaradayTestConfig, tmp_default_config):
    # Config
    configuration.set(Sections.SERVER, "api_port", str(test_config.client.port))
    configuration.set(Sections.SERVER, "host", test_config.client.host)
    configuration.set(Sections.SERVER, "workspace", test_config.workspace)
    configuration.set(Sections.TOKENS, "registration", "NotOk" * 5)
    configuration.set(Sections.EXECUTOR_DATA.format("ex1"), "cmd", 'exit 1')
    tmp_default_config.save()

    # Init and register it
    dispatcher = Dispatcher(test_config.client.session, tmp_default_config.config_file_path)

    with pytest.raises(AssertionError):
        await dispatcher.register()


@pytest.mark.parametrize('executor_options',
                         [
                             {  # 0
                                 "data": {"agent_id": 1},
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Data not contains action to do"},
                                 ],
                                 "ws_responses": [
                                     {"error": "'action' key is mandatory in this websocket connection"}
                                 ]
                             },
                             {  # 1
                                 "data": {"action": "CUT", "agent_id": 1},
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Unrecognized action"},
                                 ],
                                 "ws_responses": [
                                     {"CUT_RESPONSE": "Error: Unrecognized action"}
                                 ]
                             },
                             {  # 2
                                 "data": {"action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "json"}},
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 3
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "json", "count": "5"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR", "msg": "JSON Parsing error: Extra data"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 4
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "json", "count": "5", "spare": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "min_count": 5},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 5
                                 "data": {
                                     "action": "RUN",
                                     "agent_id": 1,
                                     "executor": "ex1",
                                     "args": {"out": "json", "spaced_before": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 6
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "json", "spaced_middle": "T", "count": "5", "spare": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "max_count": 1},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 7
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "bad_json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR",
                                      "msg": "Invalid data supplied by the executor to the bulk create endpoint. "
                                             "Server responded: "},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 8
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "str"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR", "msg": "JSON Parsing error: Expecting value"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 9
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "none", "err": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "DEBUG", "msg": "Print by stderr"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 10
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "none", "fails": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "WARNING", "msg": "Executor ex1 finished with exit code 1"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": False,
                                         "message": "Executor ex1 from unnamed_agent failed"
                                     }
                                 ]
                             },
                             {  # 11
                                 "data": {
                                     "action": "RUN",
                                     "agent_id": 1,
                                     "executor": "ex1",
                                     "args": {"out": "none", "err": "T", "fails": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "DEBUG", "msg": "Print by stderr"},
                                     {"levelname": "WARNING", "msg": "Executor ex1 finished with exit code 1"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": False,
                                         "message": "Executor ex1 from unnamed_agent failed"
                                     }
                                 ]
                             },
                             {  # 12
                                 "data": {
                                     "action": "RUN",
                                     "agent_id": 1,
                                     "executor": "ex1",
                                     "args": {"out": "json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "varenvs": {"DO_NOTHING": "True"},
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 13
                                 "data": {
                                     "action": "RUN",
                                     "agent_id": 1,
                                     "executor": "ex1",
                                     "args": {"err": "T", "fails": "T"},
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "ERROR", "msg": "Mandatory argument not passed"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": False,
                                         "message": "Mandatory argument(s) not passed to ex1 executor from "
                                                    "unnamed_agent agent"
                                     }
                                 ]
                             },
                             {  # 14
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1",
                                     "args": {"out": "json", "WTF": "T"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "ERROR", "msg": "Unexpected argument passed"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": False,
                                         "message": "Unexpected argument(s) passed to ex1 executor from unnamed_agent "
                                                    "agent"
                                     }
                                 ]
                             },
                             {  # 15
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR",
                                      "msg": "Invalid data supplied by the executor to the bulk create endpoint. "
                                             "Server responded: "},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "workspace": "error500",
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 16
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR",
                                      "msg": "Invalid data supplied by the executor to the bulk create endpoint. "
                                             "Server responded: "},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "workspace": "error429",
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 17
                                 "data": {"action": "RUN", "agent_id": 1, "executor": "ex1", "args": {"out": "json"}},
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor"},
                                     {"levelname": "ERROR", "msg": "ValueError raised processing stdout, try with "
                                                                   "bigger limiting size in config"},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully"}
                                 ],
                                 "max_size": "1",
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "running": True,
                                         "message": "Running ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "ex1",
                                         "successful": True,
                                         "message": "Executor ex1 from unnamed_agent finished successfully"
                                     }
                                 ]
                             },
                             {  # 18
                                 "data": {
                                     "action": "RUN", "agent_id": 1,
                                     "args": {"out": "json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "ERROR", "msg": "No executor selected"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "running": False,
                                         "message": "No executor selected to unnamed_agent agent"
                                     }
                                 ]
                             },
                             {  # 19
                                 "data": {
                                     "action": "RUN", "agent_id": 1, "executor": "NOT_4N_CORRECT_EXECUTOR",
                                     "args": {"out": "json"}
                                 },
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running ex1 executor", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "INFO", "msg": "Executor ex1 finished successfully", "max_count": 0,
                                      "min_count": 0},
                                     {"levelname": "ERROR", "msg": "The selected executor not exists"},
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "NOT_4N_CORRECT_EXECUTOR",
                                         "running": False,
                                         "message": "The selected executor NOT_4N_CORRECT_EXECUTOR not exists in "
                                                    "unnamed_agent agent"}
                                 ]
                             },
                             {  # 20
                                 "data": {"action": "RUN", "agent_id": 1, "executor": "add_ex1", "args": {"out": "json"}},
                                 "logs": [
                                     {"levelname": "INFO", "msg": "Running add_ex1 executor"},
                                     {"levelname": "INFO", "msg": "Data sent to bulk create"},
                                     {"levelname": "INFO", "msg": "Executor add_ex1 finished successfully"}
                                 ],
                                 "ws_responses": [
                                     {
                                         "action": "RUN_STATUS",
                                         "executor_name": "add_ex1",
                                         "running": True,
                                         "message": "Running add_ex1 executor from unnamed_agent agent"
                                     }, {
                                         "action": "RUN_STATUS",
                                         "executor_name": "add_ex1",
                                         "successful": True,
                                         "message": "Executor add_ex1 from unnamed_agent finished successfully"
                                     }
                                 ],
                                 "extra": ["add_ex1"]
                             },
                         ])
async def test_run_once(test_config: FaradayTestConfig, tmp_default_config, test_logger_handler,
                        test_logger_folder, executor_options):
    # Config
    workspace = test_config.workspace if "workspace" not in executor_options else executor_options["workspace"]
    configuration.set(Sections.SERVER, "api_port", str(test_config.client.port))
    configuration.set(Sections.SERVER, "host", test_config.client.host)
    configuration.set(Sections.SERVER, "workspace", workspace)
    configuration.set(Sections.TOKENS, "registration", test_config.registration_token)
    configuration.set(Sections.TOKENS, "agent", test_config.agent_token)
    path_to_basic_executor = (
            Path(__file__).parent.parent /
            'data' / 'basic_executor.py'
    )
    executor_names = ["ex1"] + ([] if "extra" not in executor_options else executor_options["extra"])
    configuration.set(Sections.AGENT, "executors", ",".join(executor_names))
    for executor_name in executor_names:
        executor_section = Sections.EXECUTOR_DATA.format(executor_name)
        params_section = Sections.EXECUTOR_PARAMS.format(executor_name)
        varenvs_section = Sections.EXECUTOR_VARENVS.format(executor_name)
        for section in [executor_section, params_section, varenvs_section]:
            if section not in configuration:
                configuration.add_section(section)

        configuration.set(executor_section, "cmd", "python {}".format(path_to_basic_executor))
        configuration.set(params_section, "out", "True")
        [configuration.set(params_section, param, "False") for param in [
            "count", "spare", "spaced_before", "spaced_middle", "err", "fails"]]
        if "varenvs" in executor_options:
            for varenv in executor_options["varenvs"]:
                configuration.set(varenvs_section, varenv, executor_options["varenvs"][varenv])

        max_size = str(64 * 1024) if "max_size" not in executor_options else executor_options["max_size"]
        configuration.set(executor_section, "max_size", max_size)

    tmp_default_config.save()

    async def ws_messages_checker(msg):
        msg_ = json.loads(msg)
        assert msg_ in executor_options["ws_responses"]
        executor_options["ws_responses"].remove(msg_)

    # Init and register it
    dispatcher = Dispatcher(test_config.client.session, tmp_default_config.config_file_path)
    await dispatcher.run_once(json.dumps(executor_options["data"]), ws_messages_checker)
    history = test_logger_handler.history
    assert len(executor_options["ws_responses"]) == 0
    for l in executor_options["logs"]:
        min_count = 1 if "min_count" not in l else l["min_count"]
        max_count = sys.maxsize if "max_count" not in l else l["max_count"]
        assert max_count >= \
            len(list(filter(lambda x: x.levelname == l["levelname"] and l["msg"] in x.message, history))) >= \
            min_count, l["msg"]


async def test_connect(test_config: FaradayTestConfig, tmp_default_config, test_logger_handler,
                       test_logger_folder):
    configuration.set(Sections.SERVER, "api_port", str(test_config.client.port))
    configuration.set(Sections.SERVER, "host", test_config.client.host)
    configuration.set(Sections.SERVER, "workspace", test_config.workspace)
    configuration.set(Sections.TOKENS, "registration", test_config.registration_token)
    configuration.set(Sections.TOKENS, "agent", test_config.agent_token)
    path_to_basic_executor = (
            Path(__file__).parent.parent /
            'data' / 'basic_executor.py'
    )
    configuration.set(Sections.AGENT, "executors", "ex1,ex2,ex3")

    for executor_name in ["ex1","ex2","ex3"]:
        executor_section = Sections.EXECUTOR_DATA.format(executor_name)
        params_section = Sections.EXECUTOR_PARAMS.format(executor_name)
        for section in [executor_section, params_section]:
            if section not in configuration:
                configuration.add_section(section)
        configuration.set(executor_section, "cmd", "python {}".format(path_to_basic_executor))

    configuration.set(Sections.EXECUTOR_PARAMS.format("ex1"), "param1", "True")
    configuration.set(Sections.EXECUTOR_PARAMS.format("ex1"), "param2", "False")
    configuration.set(Sections.EXECUTOR_PARAMS.format("ex2"), "param3", "False")
    configuration.set(Sections.EXECUTOR_PARAMS.format("ex2"), "param4", "False")
    tmp_default_config.save()
    dispatcher = Dispatcher(test_config.client.session, tmp_default_config.config_file_path)

    ws_responses = [{
                    'action': 'JOIN_AGENT',
                    'workspace': test_config.workspace,
                    'token': None,
                    'executors': [
                        {
                            "executor_name": "ex1",
                            "args": {
                                "param1": True,
                                "param2": False
                            }
                        },
                        {
                            "executor_name": "ex2",
                            "args": {
                                "param3": False,
                                "param4": False
                            }
                        },
                        {
                            "executor_name": "ex3",
                            "args": {}
                        }
                    ]
                }]

    async def ws_messages_checker(msg):
        msg_ = json.loads(msg)
        assert msg_ in ws_responses
        ws_responses.remove(msg_)

    await dispatcher.connect(ws_messages_checker)

    assert len(ws_responses) == 0
