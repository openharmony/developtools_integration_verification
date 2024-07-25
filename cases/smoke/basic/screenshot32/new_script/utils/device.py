import json
import logging
import os.path
import re
import subprocess
import time
import threading


class Device:
    lock = threading.Lock()

    @classmethod
    def _execute_cmd(cls, cmd):
        with cls.lock:
            logging.info(f'[In]{cmd}')
            rst = subprocess.run(cmd, capture_output=True, shell=True, timeout=30, encoding='utf-8')
            out_put = rst.stdout or rst.stderr
            time.sleep(0.5)
            # 布局的回显太多了，不打印
            if not re.search(r'cat /data/local/tmp/\S+json', cmd):
                logging.info(f'[Out]{out_put}')
            return out_put

    def __init__(self, sn):
        self.sn = sn
        self.report_path = ''
        self.resource_path = ''
        self.width = 720
        self.height = 1280
        self.velocity_range = (200, 40000)
        self._element_list = []
        # self.get_render_size()

    def hdc_shell(self, cmd):
        out = ''
        for i in range(3):
            shell_cmd = f'hdc -l0 -t {self.sn} shell "{cmd}"'
            out = self._execute_cmd(shell_cmd)
            if '[Fail]Device not founded or connected' in out:
                self.restart_hdc_process()
                time.sleep(5)
            else:
                break
        return out

    def hdc(self, cmd):
        return self._execute_cmd(f'hdc -l0 -t {self.sn} {cmd}')

    def hdc_version(self):
        return self._execute_cmd('hdc -v')

    def hdc_list_targets(self):
        devices = self._execute_cmd('hdc list targets')
        if 'Empty' in devices:
            return []
        return devices.splitlines()

    def install_hap(self, hap_path, replace=True):
        """
        暗账应用
        :param hap_path: hap包的路径
        :param replace: 是否覆盖安装，true覆盖，否则不覆盖
        :return:
        """
        logging.info('install hap')
        if replace:
            cmd = f'app install -r {hap_path}'
        else:
            cmd = f'app install {hap_path}'
        return self.hdc(cmd)

    def install_multi_hap(self, hap_list: list):
        """
        安装更新, 多hap可以指定多个文件路径
        :param hap_list:
        :return:
        """
        logging.info('install hap')
        haps = ' '.join(hap_list)
        cmd = 'install {}'.format(haps)
        return self.hdc(cmd)

    def bm_install(self, hap_list: list):
        """
        bm工具安装更新多个hap
        :param hap_list:
        :return:
        """
        logging.info('install hap')
        haps = ' '.join(hap_list)
        cmd = 'bm install -p {}'.format(haps)
        return self.hdc_shell(cmd)

    def uninstall_hap(self, bundle_name):
        # 两个命令都可以
        logging.info(f'uninstall {bundle_name}')
        # cmd = 'hdc app uninstall {}'.format(bundle_name)
        return self.hdc(f'uninstall {bundle_name}')

    def bm_uninstall(self, bundle_name):
        logging.info(f'uninstall {bundle_name}')
        return self.hdc_shell(f'bm uninstall -n {bundle_name}')

    def hdc_file_send(self, local, remote):
        logging.info('send file to device')
        return self.hdc(f'file send "{local}" "{remote}"')

    def hdc_file_recv(self, remote, local=''):
        logging.info('recv file from device')
        local = local or self.report_path
        return self.hdc(f'file recv "{remote}" "{local}"')

    def hilog(self):
        logging.info('hilog')
        return self.hdc('hilog')

    def get_udid(self):
        logging.info('get udid')
        return self.hdc('bm get --udid')

    def kill_hdc_process(self):
        logging.info('kill hdc process')
        return self._execute_cmd('hdc kill')

    def restart_hdc_process(self):
        # logging.info('restart hdc process')
        return self._execute_cmd('hdc start -r')

    def reboot(self):
        # logging.info('reboot device')
        return self.hdc_shell('reboot')

    def start_ability(self, bundle_name, ability_name):
        # logging.info(f'start {bundle_name} application')
        rst = self.hdc_shell(f'aa start -b {bundle_name} -a {ability_name}')
        time.sleep(2)
        return rst

    def force_stop(self, bundle_name):
        # logging.info(f'停掉{bundle_name}应用')
        return self.hdc_shell(f'aa force-stop {bundle_name}')

    def clean_app_data(self, bundle_name):
        """
        清除应用缓存和数据， -c缓存， -d应用数据
        :param bundle_name:
        :return:
        """
        if not bundle_name:
            return
        # logging.info(f'清理{bundle_name}应用数据和缓存')
        return self.hdc_shell(f'bm clean -n {bundle_name} -c -d')

    def disable_app(self, bundle_name):
        """
        禁止应用，应用在桌面消失
        :param bundle_name:
        :return:
        """
        # logging.info(f'禁止{bundle_name}应用，应用在桌面消失')
        return self.hdc_shell(f'bm disable -n {bundle_name}')

    def enable_app(self, bundle_name):
        """
        允许应用，应用显示在桌面上
        :param bundle_name:
        :return:
        """
        # logging.info(f'允许{bundle_name}应用，应用显示在桌面上')
        return self.hdc_shell(f'bm enable -n {bundle_name}')

    def dump_hap_configuration(self, bundle_name):
        """
        查看应用配置信息
        :param bundle_name:
        :return:
        """
        # logging.info(f'查看{bundle_name}应用配置信息')
        return self.hdc_shell(f'bm dump -n {bundle_name}')

    def stop_permission(self):
        # self.click(504, 708)
        # logging.info(f'消掉权限请求的弹窗')
        focus_win = self.get_focus_window()
        if 'permissionDialog1' in focus_win:
            # logging.info(f'消掉权限请求的弹窗')
            self.refresh_layout()
            allow = self.get_element_by_condition(condition={'text': '允许', 'type': 'Button'})
            self.click_element(allow)
            time.sleep(2)
        else:
            logging.info(f'current window: {focus_win}')
        # return self.force_stop('com.ohos.permissionmanager')

    def click(self, x: int, y: int):
        """
        模拟触摸按下
        :param x:
        :param y:
        :return:
        """
        # logging.info(f'点击({x},{y})坐标')
        return self.hdc_shell(f'uinput -M -m {x} {y} -c 0')
        # return self.hdc_shell(f'uinput -T -c {x} {y}')
        # return self.hdc_shell(f'uitest uiInput click {x} {y}')

    def click_element(self, e):
        x, y = self.center_of_element(e)
        return self.click(x, y)

    def double_click(self, x, y):
        # logging.info(f'双击({x},{y})坐标')
        return self.hdc_shell(f'uitest uiInput doubleClick {x} {y}')

    def double_click_element(self, e):
        x, y = self.center_of_element(e)
        return self.double_click(x, y)

    def long_click(self, x, y):
        # logging.info(f'长按({x},{y})坐标')
        return self.hdc_shell(f'uitest uiInput longClick {x} {y}')

    def long_click_element(self, e):
        x, y = self.center_of_element(e)
        return self.long_click(x, y)

    def dirc_fling(self, direct=0):
        """
        模拟指定方向滑动
        :param direct:direction (可选参数,滑动方向,可选值: [0,1,2,3], 滑动方向: [左,右,上,下],默认值: 0)
        swipeVelocityPps_ (可选参数,滑动速度,取值范围: 200-40000, 默认值: 600, 单位: px/s)
        stepLength(可选参数,滑动步长,默认值:滑动距离/50, 单位: px)
        :return:
        """
        direct_map = {
            0: '左',
            1: '右',
            2: '上',
            3: '下',
        }
        if direct not in direct_map.keys():
            direct = 0
        # logging.info(f'向 {direct_map.get(direct)} 滑动')
        return self.hdc_shell(f'uitest uiInput dircFling {direct}')

    def swipe(self, from_x, from_y, to_x, to_y, velocity=600):
        """
        模拟慢滑操作
        :param from_x:(必选参数,滑动起点x坐标)
        :param from_y:(必选参数,滑动起点y坐标)
        :param to_x:(必选参数,滑动终点x坐标)
        :param to_y:(必选参数,滑动终点y坐标)
        :param velocity: (可选参数,滑动速度,取值范围: 200-40000, 默认值: 600, 单位: px/s)
        :return:
        """
        # 保证数据取值范围合理
        # logging.info(f'从({from_x},{from_y})滑动到({to_x},{to_y})，滑动速度：{velocity}px/s')
        return self.hdc_shell(f'uitest uiInput swipe {from_x} {from_y} {to_x} {to_y} {velocity}')

    def fling(self, from_x, from_y, to_x, to_y, velocity=600):
        """
        模拟快滑操作
        :param from_x:(必选参数,滑动起点x坐标)
        :param from_y:(必选参数,滑动起点y坐标)
        :param to_x:(必选参数,滑动终点x坐标)
        :param to_y:(必选参数,滑动终点y坐标)
        :param velocity: (可选参数,滑动速度,取值范围: 200-40000, 默认值: 600, 单位: px/s)
        :return:
        """
        # 保证数据取值范围合理
        # 保证数据取值范围合理
        # logging.info(f'从({from_x},{from_y})快速滑动到({to_x},{to_y})')
        return self.hdc_shell(f'uitest uiInput fling {from_x} {from_y} {to_x} {to_y}')

    def drag(self, from_x, from_y, to_x, to_y, velocity=600):
        """
        拖拽，从（x1, y1）拖拽到（x2, y2）
       :param from_x:(必选参数,滑动起点x坐标)
        :param from_y:(必选参数,滑动起点y坐标)
        :param to_x:(必选参数,滑动终点x坐标)
        :param to_y:(必选参数,滑动终点y坐标)
        :param velocity: (可选参数,滑动速度,取值范围: 200-40000, 默认值: 600, 单位: px/s)
        """
        # logging.info(f'从({from_x},{from_y})拖到({to_x},{to_y})，拖动速度：{velocity}px/s')
        return self.hdc_shell(f'uitest uiInput drag {from_x} {from_y} {to_x} {to_y} {velocity}')

    def key_event(self, key_code):
        # logging.info(f'按下{key_code}键')
        return self.hdc_shell(f'uitest uiInput keyEvent {key_code}')

    def go_home(self):
        return self.key_event('Home')

    def go_back(self):
        return self.key_event('Back')

    def press_power_key(self):
        return self.key_event('Power')

    def press_recent_key(self):
        return self.key_event('2078')

    def clear_recent_task(self):
        # logging.info('清理最近的任务')
        self.press_recent_key()
        time.sleep(0.5)
        self.press_clear_btn()

    def press_clear_btn(self):
        self.click(360, 1170)

    def input_text(self, x, y, text=''):
        # logging.info(f'向({x, y})坐标处输入“{text}”')
        return self.hdc_shell(f'uitest uiInput inputText {x} {y} {text}')

    def wakeup(self):
        # logging.info('点亮屏幕')
        return self.hdc_shell('power-shell wakeup')

    def suspend(self):
        # logging.info('熄灭屏幕')
        return self.hdc_shell('power-shell suspend')

    def set_power_mode(self, mode='602'):
        """
        设置电源模式
        :param mode:600 normal mode 正常模式
                    601 power save mode省电模式
                    602 performance mode性能模式,屏幕会常亮
                    603 extreme power save mode极端省电模式
        :return:
        """
        power_map = {
            '600': '正常模式',
            '601': '省电模式',
            '602': '性能模式',
            '603': '极端省电模式',
        }
        if mode not in power_map.keys():
            mode = '602'
        # logging.info(f'设置电源为{power_map.get(mode)}')
        return self.hdc_shell(f'power-shell setmode {mode}')

    def display_screen_state(self):
        # logging.info('获取屏幕点亮状态')
        return self.hdc_shell('hidumper -s 3308')

    def get_render_size(self):
        # logging.info('获取屏幕分辨率')
        rst = self.hdc_shell('hidumper -s RenderService -a screen')
        xy = re.findall(r'render size: (\d+)x(\d+)', rst)[0]
        self.width, self.height = [int(i) for i in xy]

    def dump_layout(self, file_name=''):
        # logging.info('获取当前页面布局')
        if file_name:
            file_path = '/data/local/tmp/' + file_name
            dump_rst = self.hdc_shell(f'uitest dumpLayout -p {file_path}')
        else:
            dump_rst = self.hdc_shell(f'uitest dumpLayout')
        layout_file = dump_rst.split(':')[1].strip()
        return layout_file

    def save_layout_to_local(self, file_name=''):
        layout_file = self.dump_layout(file_name)
        self.hdc_file_recv(layout_file)

    def refresh_layout(self, file_name=''):
        """
        :param file_name: 文件名不包含路径
        :return:
        """
        file_name = file_name or 'tmp_layout.json'
        tmp_file = self.dump_layout(file_name)
        json_data = json.loads(self.hdc_shell(f'cat {tmp_file}'))
        self._element_list = self._parse_attribute_nodes(json_data)
        # 将控件按从上到下，从左到右的顺序排列
        self._element_list.sort(key=lambda e: [self.center_of_element(e)[1], self.center_of_element(e)[0]])

    def snapshot_display(self, jpeg=''):
        """jpeg必须在/data/local/tmp目录"""
        # logging.info('获取当前页面截图')
        if jpeg:
            jpeg = '/data/local/tmp/' + jpeg
            shot_rst = self.hdc_shell(f'snapshot_display -f {jpeg}')
        else:
            shot_rst = self.hdc_shell('snapshot_display')
        if 'success' not in shot_rst:
            return ''
        return re.findall(r'write to(.*)as jpeg', shot_rst)[0].strip()

    def save_snapshot_to_local(self, file_name=''):
        tmp_file = self.snapshot_display(file_name)
        save_file = os.path.join(self.report_path, tmp_file.split('/')[-1])
        self.hdc_file_recv(tmp_file, self.report_path)
        return save_file

    def clear_local_tmp(self):
        self.hdc_shell('rm -rf /data/local/tmp/*')

    def set_screen_timeout(self, timeout=600):
        """
        设置屏幕超时时间
        :param timeout: 单位s
        :return:
        """
        # logging.info(f'设置屏幕{timeout}s无操作后休眠')
        return self.hdc_shell(f'power-shell timeout -o {timeout * 1000}')

    def rm_faultlog(self):
        # logging.info('删除fault log')
        self.hdc_shell('rm -f /data/log/faultlog/SERVICE_BLOCK*')
        self.hdc_shell('rm -f /data/log/faultlog/appfreeze*')
        self.hdc_shell('rm -f /data/log/faultlog/temp/cppcrash*')
        self.hdc_shell('rm -f /data/log/faultlog/faultlogger/jscrash*')
        self.hdc_shell('rm -f /data/log/faultlog/faultlogger/appfreeze*')
        self.hdc_shell('rm -f /data/log/faultlog/faultlogger/cppcrash*')

    def start_hilog(self):
        # logging.info('开启hilog')
        self.hdc_shell('hilog -w stop;hilog -w clear')
        self.hdc_shell('hilog -r;hilog -b INFO;hilog -w start -l 10M -n 1000')

    def stop_and_collect_hilog(self, local_dir=''):
        # logging.info('停止并收集hilog')
        self.hdc_shell('hilog -w stop')
        self.hdc_file_recv('/data/log/hilog/', local_dir)

    def unlock(self):
        """
        滑动解锁
        :return:
        """
        # logging.info('解锁屏幕')
        return self.dirc_fling(2)

    def assert_process_running(self, process):
        # logging.info(f'检查{process}进程是否存在')
        rst = self.hdc_shell(f'ps -ef | grep -w {process} | grep -v grep')
        assert process in rst, f'process {process} not exist'

    def get_pid(self, process):
        # logging.info(f'获取{process}进程PID')
        return self.hdc_shell(f'pidof {process}').strip()

    def get_wifi_status(self):
        # hidumper -ls查看所有hidumper服务
        # logging.info('获取wifi状态')
        status = self.hdc_shell('hidumper -s WifiDevice')
        active_state = re.findall(r'WiFi active state: (.*)', status)[0].strip()
        connection_status = re.findall(r'WiFi connection status: (.*)', status)[0].strip()

        scan_status = self.hdc_shell('hidumper -s WifiScan')
        is_scan_running = re.findall(r'Is scan service running: (.*)', scan_status)[0].strip()
        return {
            'active': active_state,
            'connected': connection_status,
            'scanning': is_scan_running
        }

    def dump_windows_manager_service(self):
        rst = self.hdc_shell("hidumper -s WindowManagerService -a '-a'")
        return rst

    def get_focus_window(self):
        time.sleep(1)
        text = self.dump_windows_manager_service()
        focus_win = re.findall(r'Focus window: (\d+)', text)[0].strip()
        win_id_index = 3
        focus_window_name = ''
        for line in text.splitlines():
            if line.startswith('Focus window'):
                break
            wms = re.match(r'\S*\s*(\d+\s+){' + str(win_id_index) + '}', line)
            if wms:
                data = wms.group().strip().split()
                if data[win_id_index] == focus_win:
                    focus_window_name = data[0]
                    break
        # logging.info('当前聚焦的窗口为：{}'.format(focus_window_name))
        return focus_window_name

    def get_win_id(self, window_name):
        text = self.dump_windows_manager_service()
        win = re.search(window_name + r'\s*(\d+\s+){3}', text)
        if not win:
            return
        win_id = win.group().split()[-1]
        return win_id

    def get_navigationb_winid(self):
        return self.get_win_id('SystemUi_NavigationB')

    def is_soft_keyboard_on(self):
        if self.soft_keyboard():
            return True
        return False

    def soft_keyboard(self):
        text = self.dump_windows_manager_service()
        keyboard = re.search(r'softKeyboard1\s*(\d+\s+){8}\[\s+(\d+\s+){4}]', text)
        if not keyboard:
            return ''
        return keyboard.group()

    def get_elements_by_text(self, text):
        ems = []
        for e in self._element_list:
            if e.get('text') == text:
                ems.append(e)
        return ems

    def get_element_by_text(self, text, index=0):
        ems = self.get_elements_by_text(text)
        if not ems:
            return
        return ems[index]

    def assert_text_exist(self, text):
        element = self.get_elements_by_text(text)
        rst = 'Yes' if element else 'No'
        logging.info('check [text]="{}" exist? [{}]'.format(text, rst))
        assert element

    def get_elements_by_type(self, _type):
        ems = []
        for e in self._element_list:
            if e.get('type') == _type:
                ems.append(e)
        return ems

    def get_element_by_type(self, _type, index=0):
        ems = self.get_elements_by_type(_type)
        if not ems:
            return
        return ems[index]

    def assert_type_exist(self, _type):
        element = self.get_elements_by_type(_type)
        rst = 'Yes' if element else 'No'
        logging.info('check [type]="{}"exist? [{}]'.format(_type, rst))
        assert element

    def get_elements_by_key(self, key):
        ems = []
        for e in self._element_list:
            if e.get('key') == key:
                ems.append(e)
        return ems

    def get_element_by_key(self, key, index=0):
        ems = self.get_elements_by_key(key)
        if not ems:
            return
        return ems[index]

    def assert_key_exist(self, key):
        element = self.get_elements_by_key(key)
        rst = 'Yes' if element else 'No'
        logging.info('check [key]="{}"exist? [{}]'.format(key, rst))
        assert element

    def get_elements_by_condition(self, condition: dict):
        ems = []
        for e in self._element_list:
            cs = set(condition.items())
            if cs.issubset(set(e.items())):
                ems.append(e)
        return ems

    def get_element_by_condition(self, condition, index=0):
        ems = self.get_elements_by_condition(condition)
        if not ems:
            return
        return ems[index]

    def set_brightness(self, value=102):
        return self.hdc_shell(f'power-shell display -s {value}')

    @staticmethod
    def center_of_element(e):
        assert e, 'element not exist'
        bounds = e.get('bounds')
        x1, y1, x2, y2 = [int(i) for i in re.findall(r'\d+', bounds)]
        x = (x1 + x2) // 2
        y = (y1 + y2) // 2
        return x, y

    def _parse_attribute_nodes(self, json_obj, attr_list=None):
        if attr_list is None:
            attr_list = []

        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                if key == 'attributes' and isinstance(value, dict):
                    attr_list.append(value)
                elif isinstance(value, (dict, list)):
                    self._parse_attribute_nodes(value, attr_list)
        elif isinstance(json_obj, list):
            for item in json_obj:
                self._parse_attribute_nodes(item, attr_list)
        return attr_list
