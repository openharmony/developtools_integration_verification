#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2023-2024 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import json
import pprint


def _create_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(description='Collect init config information from xxxx/etc/init dir.')
    parser.add_argument('-i', '--input',
                        help='input init config files base directory example "out/rk3568/packages/phone/" ',
                        action='append', required=True)

    parser.add_argument('-o', '--output',
                        help='output init config information database directory', required=False)
    parser.add_argument('-b', '--bootevent',
                        help='input bootevent file from system ', required=False)
    return parser


class ItemParser(dict):
    def __init__(self, config):
        self._config_parser = config
        self["name"] = ""

    def create(self, json_node, parent=None, file_id=None):
        return

    def update(self, json_node, parent=None, file_id=None):
        return

    def get_name(self):
        return self["name"]

    def get(self, key):
        if self.__contains__(key):
            return self[key]
        return None

    # get value form json array
    def get_strings_value(self, json_str_array):
        if json_str_array == None or len(json_str_array) == 0:
            return ""

        string = json_str_array[0]
        for i in range(1, len(json_str_array)):
            string = "{}@{}".format(string, json_str_array[i])
        return string


class CmdParser(ItemParser):
    def __init__(self, config):
        ItemParser.__init__(self, config)
        self["content"] = ""
        self["fileId"] = -1

    def __str__(self):
        return "cmd \"%s\"  content \"%s\" " % (self["name"], self["content"])

    def create(self, json_node, parent=None, fileId=None):
        if not isinstance(json_node, str):
            raise Exception("json_node type error")
        if parent == None:
            raise Exception("parent ")
        info = json_node.partition(" ") # 取第一个空格分割
        self["name"] = info[0]
        self["jobId"] = parent.get("jobId")
        if fileId:
            self["fileId"] = fileId
        if len(info) > 2:
            self["content"] = info[2]
        return


class JobParser(ItemParser):
    def __init__(self, config):
        ItemParser.__init__(self, config)
        self["condition"] = ""
        self["serviceId"] = -1
        self["fileId"] = -1
        self["jobPriority"] = -1
        self["jobPriority"] = -1
        self["executionTime"] = 0

    def __str__(self):
        return "jobs '%s'  condition '%s' " % (self["name"], self["condition"])

    def create(self, json_node, parent=None, fileId=None):
        if not isinstance(json_node, dict):
            raise Exception("json_node type error")
        self["name"] = json_node["name"]
        self["jobId"] = self._config_parser.get_job_id()
        self["jobPriority"] = self._config_parser.get_job_priority(json_node["name"])

        if fileId and self["fileId"] is None:
            self["fileId"] = fileId
        if parent != None:
            self["serviceId"] = parent.get("serviceId")

        if json_node.__contains__("condition"):
            self["condition"] = json_node.get("condition")
        if json_node.__contains__("cmds"):
            self._add_cmds(json_node.get("cmds"), fileId)

        return

    def update(self, json_node, parent=None, fileId=None):
        if not isinstance(json_node, dict):
            raise Exception("json_node type error")
        if parent != None:
            self["serviceId"] = parent.get("serviceId")
        if fileId and self["fileId"] is None:
            self["fileId"] = fileId
        if json_node.__contains__("cmds"):
            self._add_cmds(json_node.get("cmds"), fileId)
        return

    def _add_cmds(self, cmd_list, file_id):
        for cmd in cmd_list:
            self._config_parser.add_cmd(cmd, self, file_id)


class ServiceParser(ItemParser):
    def __init__(self, config):
        ItemParser.__init__(self, config)
        self["critical_enable"] = False
        self["limit_time"] = 20
        self["limit_count"] = 4
        self["importance"] = 0
        self["once"] = False
        self["console"] = False
        self["notify_state"] = True
        self["on_demand"] = False
        self["sandbox"] = False
        self["disabled"] = False
        self["start_mode"] = "normal"
        self["secon"] = ""
        self["boot_job"] = ""
        self["start_job"] = ""
        self["stop_job"] = ""
        self["restart_job"] = ""
        self["path"] = ""
        self["apl"] = ""
        self["d_caps"] = ""
        self["permission"] = ""
        self["permission_acls"] = ""
        self["fileId"] = -1

    def create(self, json_node, parent=None, fileId=None):
        if not isinstance(json_node, dict):
            raise Exception("json_node type error")
        self["name"] = json_node["name"]
        if not self.get("serviceId") :
            self["serviceId"] = self._config_parser.get_service_id()
        if fileId :
            self["fileId"] = fileId
        self._handle_string_filed(json_node)
        self._handle_bool_filed(json_node)
        self._handle_array_filed(json_node)
        self._handle_integer_filed(json_node)

        #for file
        if json_node.__contains__("file"):
            for item in json_node.get("file"):
                self._config_parser.add_service_file(item, self)

        #for socket
        if json_node.__contains__("socket"):
            for item in json_node.get("socket"):
                self._config_parser.add_service_socket(item, self)
        #for jobs
        if json_node.__contains__("jobs"):
            self._handle_scope_jobs(json_node.get("jobs"))

        #for critical
        if json_node.__contains__("critical"):
            critical = json_node.get("critical")
            if isinstance(critical, list):
                self["critical_enable"] = int(critical[0]) != 0
                self["limit_time"] = int(critical[0])
                self["limit_count"] = int(critical[0])
            else:
                self["critical_enable"] = int(critical) != 0
        return

    def update(self, json_node, parent=None, fileId=None):
        self.create(json_node, parent, fileId)
        return

    def _handle_string_filed(self, json_node):
        str_field_map = {
            "uid" : "uid", "caps":"caps", "start_mode":"start-mode", "secon":"secon", "apl":"apl"
        }
        for key, name in str_field_map.items():
            if json_node.__contains__(name):
                self[key] = json_node.get(name)

    def _handle_integer_filed(self, json_node):
        str_field_map = {
            "importance" : "importance"
        }
        for key, name in str_field_map.items():
            if json_node.__contains__(name):
                self[key] = json_node.get(name)

    def _handle_bool_filed(self, json_node):
        bool_field_map = {
            "once" : "once", "console" : "console", "notify_state" : "notify_state",
            "on_demand" : "ondemand", "sandbox" : "sandbox", "disabled" : "disabled",
            "critical_enable" : "critical_enable"
        }
        for key, name in bool_field_map.items():
            if json_node.__contains__(name):
                value = json_node.get(name)
                if isinstance(value, bool):
                    self[key] = value
                elif isinstance(value, int):
                    self[key] = value != 0

    def _handle_array_filed(self, json_node):
        array_field_map = {
            "path" : "path", "gid" : "gid", "cpu_core" : "cpucore", "caps":"caps", "write_pid":"writepid",
            "d_caps":"d-caps", "permission":"permission", "permission_acls":"permission_acls",
        }
        for key, name in array_field_map.items():
            if json_node.__contains__(name) :
                self[key] = self.get_strings_value(json_node.get(name))

    def _handle_scope_jobs(self, json_node):
        job_field_map = {
            "boot_job" : "on_boot", "start_job" : "on-start", "stop_job":"on-stop", "restart_job":"on-restart"
        }
        for key, name in job_field_map.items():
            if json_node.__contains__(name):
                self[key] = json_node.get(name)
                self._config_parser.add_job({"name" : json_node.get(name)}, self, self["fileId"])


class ServiceSocketParser(ItemParser):
    def __init__(self, config):
        ItemParser.__init__(self, config)
        self["family"] = ""
        self["type"] = ""
        self["protocol"] = ""
        self["permissions"] = ""
        self["uid"] = ""
        self["gid"] = ""
        self["serviceId"] = -1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "socket '%s' serviceid = %d family %s" % (self["name"], self["serviceId"], self["family"])

    def create(self, json_node, parent=None, file_id=None):
        if not isinstance(json_node, dict):
            raise Exception("json_node type error")
        self["name"] = json_node["name"]
        if parent != None:
            self["serviceId"] = parent.get("serviceId")
        fields = ["family", "type", "protocol", "permissions", "uid", "gid"]
        for field in fields:
            if json_node.get(field) :
                self[field] = json_node.get(field)
        if json_node.get("option") :
            self["option"] = self.get_strings_value(json_node.get("option"))


class ServiceFileParser(ItemParser):
    def __init__(self, config):
        ItemParser.__init__(self, config)
        self["name"] = ""
        self["content"] = ""
        self["serviceId"] = -1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "file '%s' serviceid = %d content '%s'" % (self["name"], self["serviceId"], self["content"])

    def create(self, json_node, parent=None, file_id=None):
        if not isinstance(json_node, str):
            raise Exception("json_node type error")
        if parent != None:
            self["serviceId"] = parent.get("serviceId")
        info = json_node.partition(" ")
        self["name"] = info[0]
        if len(info) > 2:
            self["content"] = info[2]
        return


class ConfigParser():
    def __init__(self, path):
        self._path = path
        self._jobs = {}
        self._files = {}
        self._cmds = []
        self._services = {}
        self._service_sockets = {}
        self._service_files = {}
        self._job_id = 0
        self._file_id = 0
        self._service_id = 0
        self._selinux = ""
        self._plug_in = []

    def load_config(self, file_name):
        path = self._path + file_name
        if not os.path.exists(path):
            print("Warning, invalid config file %s" % path)
            return
        with open(path, encoding='utf-8') as content:
            try:
                root = json.load(content)
                file_id = self.add_file(file_name)
                if not isinstance(root, dict):
                    raise Exception("root type error")
                if (root.__contains__("services")):
                    self._load_services(root["services"], file_id)
                if (root.__contains__("jobs")):
                    self._load_jobs(root["jobs"], file_id)
                if (root.__contains__("import")):
                    self._load_import(root["import"])
                    pass
            except:
                pass

    def add_file(self, file_name):
        if self._files.get(file_name):
            return self._files.get(file_name).get("fileId")
        self._file_id = self._file_id + 1
        self._files[file_name] = {
            "fileId" : self._file_id,
            "file_name" : file_name
        }
        return self._files[file_name].get("fileId")

    def add_job(self, item, service, file_id):
        if self._jobs.get(item.get("name")):
            self._jobs.get(item.get("name")).update(item, service, file_id)
            return
        parser = JobParser(self)
        parser.create(item, service, file_id)
        self._jobs[parser.get_name()] = parser

    def add_cmd(self, item, job, file_id):
        parser = CmdParser(self)
        parser.create(item, job, file_id)
        self._cmds.append(parser)

    def add_service(self, item, file_id):
        if self._services.get(item.get("name")):
            self._services.get(item.get("name")).update(item)
            return
        parser = ServiceParser(self)
        parser.create(item, None, file_id)
        self._services[parser.get("name")] = parser

    def add_service_socket(self, item, service):
        parser = ServiceSocketParser(self)
        parser.create(item, service)
        self._service_sockets[parser.get_name()] = parser

    def add_service_file(self, item, service):
        parser = ServiceFileParser(self)
        parser.create(item, service)
        self._service_files[parser.get_name()] = parser

    def get_job_id(self):
        self._job_id = self._job_id + 1
        return self._job_id

    def get_service_id(self):
        self._service_id = self._service_id + 1
        return self._service_id

    def dump_config(self):
        pp = pprint.PrettyPrinter(indent=0, compact=True)
        pp.pprint(self._jobs)
        pass

    def scan_library(self, target_cpu):
        if target_cpu == "arm64":
            config_paths = [
                "system/lib64/init",
                "chip_prod/lib64/init",
                "sys_prod/lib64/init",
                "vendor/lib64/init",
            ]
        else:
            config_paths = [
                "system/lib/init",
                "chip_prod/lib/init",
                "sys_prod/lib/init",
                "vendor/lib/init",
            ]
        for file_name in config_paths:
            dir_config_file = os.path.join(self._path, file_name)
            self._scan_share_library_file(dir_config_file)

    def scan_config(self):
        config_paths = [
            "system/etc/init",
            "chip_prod/etc/init",
            "sys_prod/etc/init",
            "vendor/etc/init",
        ]
        for file_name in config_paths:
            self._scan_config_file(file_name)

    def get_job_priority(self, job_name):
        job_priority = {
            "pre-init" : 0,
            "init" : 1,
            "post-init" : 2,
            "early-fs" : 3,
            "fs" : 4,
            "post-fs" : 5,
            "late-fs" : 6,
            "post-fs-data" : 7,
            "firmware_mounts_complete" : 8,
            "early-boot" : 9,
            "boot" : 10
        }

        if (job_priority.__contains__(job_name)):
            return job_priority.get(job_name)
        return 100

    def load_boot_event_file(self, boot_event_file):
        if not os.path.exists(boot_event_file):
            print("Warning, invalid config file %s" % boot_event_file)
            return
        with open(boot_event_file, encoding='utf-8') as content:
            try:
                root = json.load(content)
                for item in root:
                    self._load_boot_event(item)
            except:
                pass
        pass

    def load_selinux_config(self, file_name):
        path = os.path.join(self._path, file_name)
        if not os.path.exists(path):
            print("Error, invalid selinux config path %s" % path)
            return
        try:
            with open(path, encoding='utf-8') as fp:
                line = fp.readline()
                while line :
                    if line.startswith("#") or len(line) < 3:
                        line = fp.readline()
                        continue
                    param_info = line.partition("=")
                    if len(param_info) != 3:
                        line = fp.readline()
                        continue
                    if param_info[0].strip() == "SELINUX":
                        self._selinux = param_info[2].strip()
                    line = fp.readline()
        except:
            print("Error, invalid parameter file ", file_name)
            pass

    def _load_services(self, json_node, file_id):
        if not isinstance(json_node, list):
            raise Exception("json_node type error")
        for item in json_node:
            self.add_service(item, file_id)
        return

    def _load_jobs(self, json_node, file_id):
        if not isinstance(json_node, list):
            raise Exception("json_node type error")
        for item in json_node:
            self.add_job(item, None, file_id)
        return

    def _load_import(self, import_node):
        if not isinstance(import_node, list):
            raise Exception("import_node type error")
        start_with = ["/system", "/chip_prod", "/sys_prod", "/vendor"]
        for file in import_node:
            found = False
            for start in start_with:
                if file.startswith(start):
                    found = True
                    break
            if found :
                self.load_config(self._path + file)
            else:
                for start in start_with:
                    self.load_config(self._path + start + file, file)

    def _is_valid_file(self, file, valid_file_ext):
        if not file.is_file():
            return False
        for ext in valid_file_ext:
            if file.name.endswith(ext):
                return True
        return False

    def _scan_config_file(self, file_name):
        dir_config_file = os.path.join(self._path, file_name)
        if not os.path.exists(dir_config_file):
            return
        try:
            with os.scandir(dir_config_file) as files:
                for file in files:
                    if self._is_valid_file(file, ".cfg"):
                        name = file.path[len(self._path) :]
                        self.load_config(name)
        except:
            pass

    def _scan_share_library_file(self, file_name):
        if not os.path.exists(file_name):
            return
        try:
            for item in os.scandir(file_name):
                file_path = os.path.join(file_name, item.name)
                if item.is_file():
                    if self._is_valid_file(item, ".so"):
                        self._plug_in.append(file_path)
                        continue
                else:
                    dir_config_file = os.path.join(file_name, item.name)
                    self._scan_share_library_file(item)
        except:
            pass

    def _load_boot_event(self, event):
        if self._jobs.__contains__(event.get("name")):
            print("loadBootEvent_ %s %f" % (event.get("name"), event.get("dur")))
            self._jobs.get(event.get("name"))["executionTime"] = event.get("dur")


def startup_config_collect(base_path, target_cpu):
    parser = ConfigParser(os.path.join(base_path, "packages/phone"))
    parser.load_config("/system/etc/init.cfg")
    parser.scan_library(target_cpu)
    parser.scan_config()
    parser.load_selinux_config("system/etc/selinux/config")
    return parser

if __name__ == '__main__':
    args_parser = _create_arg_parser()
    options = args_parser.parse_args()
    startup_config_collect(options.input)
