import json
import time
import subprocess
import socket
import logging
import argparse
import re
import shutil


logging.basicConfig(level=logging.DEBUG)

AGENT_BUNDLE = "com.ohos.devicetest"
SETTINGS_API_MODULE = "com.ohos.devicetest.settingsApiHelper"


def get_hap_version(hdc, bundle_name):
    echo = hdc.shell(f"bm dump -n {bundle_name} |grep versionCode").strip()
    echo = echo.split("\n")[-1]
    result = re.search(r'versionCode.+: +(\d+)', echo)
    version_code = 0
    if result:
        version_code = result.groups()[0]
        if version_code.isdigit():
            version_code = int(version_code)
        else:
            version_code = 0
    return version_code


def get_unused_local_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    _, port = sock.getsockname()
    sock.close()
    return port


class RpcCall:

    def __init__(self, module) -> None:
        self.module = module
        self.client = ""
        self.method = ""
        self.params = {}

    def __getattr__(self, attr):
        def set_params(**kwargs):
            self.params = kwargs
            return self
        self.method = attr
        return set_params

    def to_str(self):
        if self.params is not None:
            param_str = "context", json.dumps(self.params, ensure_ascii=False,
                                              separators=(',', ':'))
        else:
            param_str = ["context"]

        call_dict = {
            "module": self.module,
            "method": self.method,
            "params": param_str,
            "request_id": str(int(time.time() * 1000)),
            "client": self.client
        }
        inter = json.dumps(call_dict, ensure_ascii=False, separators=(',', ':'))
        inter = json.loads(inter)
        return json.dumps(inter, ensure_ascii=False, separators=(',', ':'))


def shell(*args, **kwargs):
    logging.debug("run_command: %s" % args[0])
    return subprocess.check_output(*args, shell=True, **kwargs).decode(encoding="utf-8", errors="ignore")


class Hdc:

    def __init__(self, device_sn=None, remote_addr=None):
        self.device_sn = device_sn
        self.remote_addr = remote_addr
        self.connector_name = self._find_connector_command()
        if device_sn:
            self.hdc_cmd_head = [self.connector_name, "-t", self.device_sn]
        else:
            self.hdc_cmd_head = [self.connector_name]
        self.hdc_shell_head = self.hdc_cmd_head.copy()
        self.hdc_shell_head.append("shell")
        self._set_remote_addr(remote_addr)
        self.hdc_shell_head = " ".join(self.hdc_shell_head)
        self.hdc_cmd_head = " ".join(self.hdc_cmd_head)

    def _find_connector_command(self):
        if shutil.which("hdc_std"):
            return "hdc_std"
        elif shutil.which("hdc"):
            return "hdc"
        else:
            raise RuntimeError("No hdc connector")

    def _set_remote_addr(self, remote_addr):
        self.remote_addr = remote_addr
        if self.remote_addr:
            ip, port = self.remote_addr
            self.hdc_cmd_head.insert(1, "-s")
            self.hdc_cmd_head.insert(2, f"{ip}:{port}")
            self.hdc_shell_head = self.hdc_cmd_head.copy()
            self.hdc_shell_head.append("shell")

    def __call__(self, cmd: str):
        return shell(self.hdc_cmd_head + " " + cmd)

    def shell(self, cmd: str):
        return shell(self.hdc_shell_head + " " + '"%s"' % cmd)


class RpcClient:

    def __init__(self, hdc: Hdc, agent_hap_path="devicetest.hap") -> None:
        self.sk = None
        self.hdc = hdc
        self.agent_hap_path = agent_hap_path
        self.local_port = get_unused_local_port()
        self.addr = ("127.0.0.1", self.local_port)
        self.fport_item = ""

    def setup_agent(self):
        result = self.hdc.shell(f"bm dump -a|grep {AGENT_BUNDLE}")
        need_install = True
        if AGENT_BUNDLE in result:
            result = get_hap_version(self.hdc, AGENT_BUNDLE)
            if result >= 1020089:
                logging.info("Hap version is %s, don't need to install" % result)
                need_install = False

        if need_install:
            logging.info("start to install agent")
            result = self.hdc(f"install {self.agent_hap_path}")
            logging.info(result)
            time.sleep(5)
        result = self.hdc.shell(f"bm dump -a|grep {AGENT_BUNDLE}")
        if AGENT_BUNDLE not in result:
            logging.error(result)
            raise RuntimeError("Fail to install devicetest agent")

        result = self.hdc("fport ls")
        fport_item = "tcp:%s tcp:8011" % self.local_port
        self.fport_item = fport_item
        self.clear_fport()
        if fport_item in result:
            result = self.hdc("fport ls")
            if fport_item in result:
                raise RuntimeError("Fail to clear fport item" % fport_item)

        result = self.hdc("fport %s" % fport_item)
        logging.info(result)
        result = self.hdc("fport ls")
        if fport_item not in result:
            logging.error(result)
            raise RuntimeError("Fail to forward 8011 port to device")

        pid = self.hdc.shell(f"pidof {AGENT_BUNDLE}").strip()
        logging.debug(pid)
        if not pid.isdigit():
            logging.info("start agent")
            result = self.hdc.shell(f"aa start -a ServiceAbility -b {AGENT_BUNDLE}")
            if "error" in result.lower():
                result = self.hdc.shell(f"aa start -a EntryAbility -b {AGENT_BUNDLE}")
            if "error" in result.lower():
                logging.error(result)
                raise RuntimeError("Fail to start agent")
            time.sleep(2)

    def connect_to_agent(self):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        sk.connect(self.addr)
        logging.info("connect success")
        self.sk = sk

    def do_rpc_call(self, call: RpcCall):
        ip, port = self.sk.getsockname()
        call.client = ip
        rpc_str = call.to_str()
        logging.debug(rpc_str)
        self.sk.send(b'1' + rpc_str.encode(encoding="utf-8") + b'\n')
        result = self.sk.recv(1024)
        result = result.decode(encoding="utf-8", errors="ignore")
        logging.info("GetReply:" + result)
        return json.loads(result)

    def clear_fport(self):
        if self.fport_item:
            self.hdc("fport rm %s" % self.fport_item)

    def __del__(self):
        self.clear_fport()


def disable_startup_guide(client: RpcClient):
    result = client.do_rpc_call(RpcCall(SETTINGS_API_MODULE).setValue(setting_name="device_provisioned", value="1"))
    if result is not True:
        raise RuntimeError("Fail to set device_provisioned")

    result = client.do_rpc_call(RpcCall(SETTINGS_API_MODULE).setValueSync(setting_name="user_setup_complete", value="1",
                                                                                     domain_name="secure"))
    if result is not True:
        raise RuntimeError("Fail to set user_setup_complete")

    result = client.do_rpc_call(RpcCall(SETTINGS_API_MODULE).setValueSync(setting_name="is_ota_finished", value="1",
                                                                                              domain_name="secure"))
    if result is not True:
        raise RuntimeError("Fail to set is_ota_finished")

    client.do_rpc_call(RpcCall(SETTINGS_API_MODULE).getValueSync(setting_name="user_setup_complete", default_value="",
                                                                                    domain_name="secure"))

    client.do_rpc_call(RpcCall(SETTINGS_API_MODULE).getValueSync(setting_name="is_ota_finished", default_value="",
                                                                                domain_name="secure"))
    pid = client.hdc.shell("pidof com.ohos.startup_guide")
    pid = pid.strip()
    logging.debug(pid)
    result = re.search(r"\d+", pid)
    if not result:
        logging.info("startup guide is not running")
        return
    pid = result.group()
    time.sleep(1)
    result = client.hdc.shell("kill " + pid)
    logging.debug(result)
    result = client.hdc.shell("bm disable -n com.ohos.startup_guide")
    logging.debug(result)
    client.hdc.shell("uinput -K -d 1 -u 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="跳过开机向导工具")
    parser.add_argument("-m", "--module", help="模块名", default=SETTINGS_API_MODULE)
    parser.add_argument("-f", "--method", help="方法名称", default="setValue")
    parser.add_argument("-p", "--params", help="参数, 格式为\"name1=value1&name2=value2\"", default=None)
    parser.add_argument("-d", "--params_dict", help="参数, 格式为{\\\"name1:value1,name2:value2\\\"}", default=None)
    parser.add_argument("--sn", help="设备sn", default=None)
    parser.add_argument("--agent_hap_path", help="设备上未安装agent时使用的hap包路径(PC端)", default="devicetest.hap")
    parser.add_argument("--no_setup", action="store_true", help="不执行预置和启动操作")

    args = parser.parse_args()

    if args.params is not None:
        params = args.params.split("&")
        params_dict = {}
        for item in params:
            key, value = item.split("=")
            params_dict[key] = value
    else:
        params_dict = {}

    if args.params_dict is not None:
        params_dict = json.loads(args.params_dict)

    hdc = Hdc(args.sn)
    client = RpcClient(hdc, agent_hap_path=args.agent_hap_path)
    try:
        logging.info("setenforce 0")
        logging.debug(hdc.shell("setenforce 0"))
        logging.debug("start to setup agent")
        client.setup_agent()
        logging.debug("start to connect to agent")
        client.connect_to_agent()

        if args.method in ("disable_startup_guide", "disable_oobe"):
            disable_startup_guide(client)
        else:
            rpc_call = RpcCall(args.module)
            method = getattr(rpc_call, args.method)
            rpc_call = method(**params_dict)
            logging.debug("start to do call")
            client.do_rpc_call(rpc_call)
            logging.debug("finished")
    finally:
        logging.info("setenforce 1")
        try:
            logging.debug(hdc.shell("setenforce 1"))
        except Exception as err:
            logging.warning("restore setenforce 1 failed: %s", err)