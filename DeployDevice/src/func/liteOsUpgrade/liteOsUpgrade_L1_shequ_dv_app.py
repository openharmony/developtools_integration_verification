#-*- coding:utf-8 -*-
import uuid
import sys
import subprocess
import os
import serial

from core.base import BaseApp, dec_stepmsg
from util.file_locker import FileLock
from util.log_info import logger
from util.time_info import get_now_time_str_info, get_now_time_info, Timeout, timeout
from aw.Telnet.TelnetClient import TelConnect
from aw.Common.Constant import CONSTANT
from aw.Download.Download import *
from aw.Common.Common import getHostIp, copyFile, copyDirectory
from aw.ExtractFile.ExtractFile import *
from aw.poweronoff.serial_power_on_off import usbPowerOnOff

lock_suffix = CONSTANT.File.LOCK_SUFFIX  #通过文件锁实现并发下载
suc_file = CONSTANT.File.SUC_FILE        #通过本文件是区分版本是否成功下载
failed_file = CONSTANT.File.FAILED_FILE  #通过本文件是标记文件下载失败
READ_MAXTIMEOUT = 120
READ_TIMEOUT = 30
READ_MINITIMEOUT = 5
uboot_finish = 'hisilicon #'
cmd_finish = ' #'

class liteOsUpgrade_L1_shequ_dv(BaseApp):
    '''
    @author: w00278233
    '''

    def __init__(self, param_file):
        super().__init__(param_file)
        self.param_List = ["deploy_com",
                        "usb_port",
                           "upgrade_upgradeLocation"]

    @dec_stepmsg("hongmeng L1 flash")
    def excute(self):
        '''
        #===================================================================================
        #   @Method:        excute(self)
        #   @Precondition:  none
        #   @Func:          升级执行入口
        #   @PostStatus:    none
        #   @eg:            excute()
        #   @return:        True or Flase
        #===================================================================================
        '''
        step_index = self.params_dict.get("step_list").index("liteOsUpgrade_L1_shequ_dv_app")
       
        # 执行下载
        try:
            if not self.download():
                CONSTANT.ENVERRMESSAGE = "image download fail"
                logger.printLog(CONSTANT.ENVERRMESSAGE)
                return False
        except Exception as e:
            raise e

        # 执行升级
        try:
            if not self.upgrade():
                CONSTANT.ENVERRMESSAGE = "board upgrade fail"
                logger.printLog(CONSTANT.ENVERRMESSAGE)
                return False
            return True
        except Exception as e:
            raise e

    @dec_stepmsg("download")
    @timeout(1800)
    def download(self):
        '''
        #===================================================================================
        #   @Method:        download(self)
        #   @Precondition:  none
        #   @Func:          构建下载到本地的路径，执行相应包的下载
        #   @PostStatus:    none
        #   @eg:            download()
        #   @return:        True or Flase
        #===================================================================================
        '''
        global version_savepath, version_name
        dir_path = CONSTANT.Path.getDirPath()
        if self.params_dict.get("pbiid"):
            version_path = self.params_dict.get("pbiid")
            version_name = str(uuid.uuid5(uuid.NAMESPACE_URL, str(self.params_dict.get("pbiid")) + "FASTBOOT"))
            version_savepath = os.path.join(dir_path, self.params_dict.get("flash_type"), version_name)
        else:
            version_path = self.params_dict.get("upgrade_upgradeLocation")
            version_name = str(uuid.uuid5(uuid.NAMESPACE_URL, (self.params_dict.get("upgrade_upgradeLocation"))))
            version_savepath = os.path.join(dir_path, version_name)

        if self.params_dict.get("isDownload") == "True":
            logger.printLog("不需要做下载，直接返回")
            return True

        #执行img下载
        import hashlib
        save_file_str = version_path.replace("/", "").replace("\\", "")
        save_file_name = hashlib.sha1(save_file_str.encode("utf-8")).hexdigest()
        logger.info("download hash string:%s, hash value:%s" % (save_file_str, save_file_name))
        save_path_file = os.path.join(dir_path, "record", "%s%s" % (save_file_name, ".txt"))
        if not self.excutedown(version_path, os.path.join(version_savepath, "img"), save_path_file, False):
            logger.error("download img fail")
            return False

        #保存本地版本路径给devicetest去版本路径下取用例
        saveVersion(save_path_file, os.path.join(version_savepath, "img"))
        
        #将本地版本push到远程tftp服务器
        tftp_ip = self.params_dict.get("Tftpserver_IP")
        if tftp_ip:
            box_ip = subprocess.getoutput("ipconfig")
            logger.info("current box ip is: %s" % box_ip)
            if not tftp_ip in box_ip:
                logger.info("start to send file")
                return self.pushFileToTftpServer(tftp_ip, os.path.join(version_savepath, "img"), version_name)
        return True

    def pushFileToTftpServer(self, tftp_ip, local_file_path, dis_path, username="root", passwd="devicetest@2012"):
        push_suc = os.path.join(local_file_path, "push_succ.txt")
        push_fail = os.path.join(local_file_path, "push_fail.txt")
        push_lock = os.path.join(local_file_path, "push.lock")
        if os.path.isfile(push_suc):
            logger.info("push file to tftpserver by other process.")
            return True
        elif os.path.isfile(push_fail):
            logger.info("%s exists. Other process has push package and failed. It will push by self" % push_fail)
            os.remove(push_fail)
        else:
            if os.path.isfile(push_lock):
                logger.info("wait for other process send succ")
                ret = waitotherdown(push_suc)
                return ret
        
        file_lock = FileLock()
        file_lock.lockFile(push_lock)
        
        try:
            import paramiko
            logger.info("ip: %s, source_path: %s" % (tftp_ip, local_file_path))
            #client = paramiko.Transport((tftp_ip,22), default_window_size=3072)
            client = paramiko.Transport((tftp_ip,22))
            client.connect(username=username,password=passwd)
            sftp = paramiko.SFTPClient.from_transport(client)
            #检查tftp服务器根目录，/data或/data/data
            ret = sftp.listdir(r"/data")
            server_base_dir = "/data/MobileUpgrade/local_img"
            if "data" in ret:
                server_base_dir = "/data/data/MobileUpgrade/local_img"
            logger.info("server base dir is : %s " % server_base_dir)
            #检查tftp服务器上有没有本次的版本目录，如果没有则创建文件夹
            ret = sftp.listdir(server_base_dir)
            server_des_path = "%s/%s" % (server_base_dir, dis_path)
            if not dis_path in ret:
                logger.info("mkdir in tftpserver: %s " % server_des_path)
                sftp.mkdir(server_des_path)
                server_img_path = "%s/%s/img" % (server_base_dir, dis_path)
                logger.info("mkdir in tftpserver: %s " % server_img_path)
                sftp.mkdir(server_img_path)
            remote_path = "%s/%s/img" % (server_base_dir, dis_path)
            logger.info("%s exists." % remote_path)
            ret = sftp.listdir(remote_path)
            #如果tftp服务器上有push_succ文件夹，则说明已经由其它进程或box把版本上传成功了。
            if "push_succ" in ret:
                logger.info("send file succ by other process")
                with open(push_suc, "a+") as fp:
                    fp.write("")
                return True
            #如果tftp服务器上有push.lock文件夹，则说明有其它进程在向tftp服务器发送版本，等待其它进程发送完毕。
            elif "push.lock" in ret:
                logger.info("wait for other process")
                i = 0
                while True:
                    time.sleep(10)
                    ret = sftp.listdir(remote_path)
                    if "push_succ" in ret:
                        logger.info("other process succ")
                        return True
                    if i > 6:
                        logger.info("wait 60s, other process failed")
                        break
                    i = i + 1
            #由本进程向tftp服务器发送版本，先创建push.lock占用上传资源
            logger.info("mkdir in tftpserver: %s/push.lock " % remote_path)
            sftp.mkdir("%s/push.lock" % remote_path)
            pushfilelist = ["OHOS_Image.bin", "rootfs.img", "userfs.img", "rootfs_vfat.img", "userfs_vfat.img", "rootfs_jffs2.img", "userfs_jffs2.img"]
            for filename in pushfilelist:
                if not os.path.exists(os.path.join(local_file_path, filename)):
                    continue
                logger.info("copy %s to %s" % (os.path.join(local_file_path, filename), "%s/%s" % (remote_path, filename)))
                try:
                    sftp.put(os.path.join(local_file_path, filename), "%s/%s" % (remote_path, filename))
                except Exception as e:
                    logger.info("retry, copy %s to %s" % (os.path.join(local_file_path, filename), "%s/%s" % (remote_path, filename)))
                    sftp.put(os.path.join(local_file_path, filename), "%s/%s" % (remote_path, filename))
            #创建上传成功标识
            logger.info("mkdir in tftpserver: %s/push_succ " % remote_path)
            sftp.mkdir("%s/push_succ" % remote_path)
            #删除占用标识
            logger.info("del %s/push.lock " % remote_path)
            sftp.rmdir("%s/push.lock" % remote_path)
            with open(push_suc, "a+") as fp:
                fp.write("")
            time.sleep(10)
            return True
        except (OSError, Exception) as exception:
            logger.error("copy to file to tftp server failed with error {}".format(exception))
            logger.info("del %s/%s " % (server_base_dir, dis_path))
            sftp.rmdir("%s/%s" % (server_base_dir, dis_path))
            client.close()
            with open(push_fail, "a+") as fp:
                fp.write("")
            return False
        finally:
            logger.info("close client")
            client.close()
    
    def excutedown(self, source_path, download_dir, suc_mark, is_file):
        '''
        #===================================================================================
        #   @Method:        excutedown(source_path, download_dir, is_file)
        #   @Precondition:  none
        #   @Func:          执行下载动作
        #   @PostStatus:    none
        #   @Param:         source_path：资源文件路径
        #                   download_dir:文件下载到本地的文件夹路径
        #                   is_file:是否是文件
        # 
        #   @eg:            excutedown("xxxx", "D:\\local\\image", Flase， os_method)
        #   @return:        True or Flase
        #===================================================================================
        '''
        failed_mark = os.path.join(download_dir, failed_file)
        lock_path = os.path.join(download_dir, lock_suffix)
        file_lock = FileLock()

        if isDownLoadSuccess(download_dir, suc_mark, failed_mark):
            return True
        try:
            nowtime = get_now_time_str_info()
            logger.printLog("%s Downloading, please wait" % nowtime)
            file_lock.lockFile(lock_path)
            ret = ""
            logger.info("Get lock. Start to ")
            if self.params_dict.get("bt_enable") and self.params_dict.get("bt_enable") == "True":
                ret = downloadByBitComet(source_path, download_dir, os_method)
            elif source_path.startswith('\\\\'):
                ret = downloadByCopy(source_path, download_dir, is_file)
            elif self.params_dict.get("pbiid"):
                ret = downlaodByDownloadTool(version_savepath, self.params_dict.get("version_type"), "FASTBOOT", self.params_dict.get("pbiid"))
            elif source_path.startswith("http"):
                ret = downloadFileFromDevCloud(source_path, "", "", download_dir)

            if source_path.endswith(".zip"):
                zip_name = os.path.basename(source_path)
                ret = extractZipFile(os.path.join(download_dir, zip_name), download_dir)
            if source_path.endswith(".tar.gz") or (source_path.startswith("http") and ("file_id=" in source_path)):
                if source_path.startswith("http") and ("file_id=" in source_path):
                    if source_path.endswith(".tar.gz"):
                        zip_name = source_path.split('=')[-1]
                    else:
                        zip_name = "out.tar.gz"
                else:
                    zip_name = os.path.basename(source_path)
                ret = unTarFile(os.path.join(download_dir, zip_name), download_dir)
            nowtime = get_now_time_str_info()
            logger.printLog("%s download to %s end" % (nowtime, download_dir))

            if not ret:
                with open(failed_mark, "a+") as fp:
                    fp.write("")
            return ret
        except Exception as e:
            logger.printLog(e)
            raise Exception(e)
        finally:
            file_lock.releaseFile()


    @dec_stepmsg("upgrade")
    #@timeout(900)
    def upgrade(self):
        '''
        #===================================================================================
        #   @Method:        upgrade(self)
        #   @Precondition:  none
        #   @Func:          升级相关业务逻辑
        #   @PostStatus:    none
        #   @eg:            upgrade()
        #   @return:        True or Flase
        #===================================================================================
        '''
        
        deploy_com = self.params_dict.get("deploy_com")
        usb_port = self.params_dict.get("usb_port")
        baudrate = self.params_dict.get("baudrate")
        tftp_ip = self.params_dict.get("Tftpserver_IP")
        device_ip = self.params_dict.get("Device_IP")
        device_Mac = self.params_dict.get("Device_MAC")
        device_netmask = self.params_dict.get("Device_Netmask")
        device_gatewayip = self.params_dict.get("Device_GatewayIP")
        #芯片类型,根据芯片类型获取对应的刷机命令
        flash_type = self.params_dict.get("flash_type")

        if not deploy_com:
            logger.error("deploy_com is NULL !!")
            return False
        if not baudrate:
            baudrate = 115200
        if not device_netmask:
            device_netmask = "255.255.252.0"
        if not device_Mac:
            device_Mac = "3a:82:d0:08:f4:99"
        local_image_path = "%s/%s" % (version_name, "img")
        scriptpath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))))
        scriptfile = os.path.join(scriptpath, "resource", "L1", "dv300_shequ", "update.txt")
        logger.info("upgrade scriptfile is: %s" % scriptfile)
        if not os.path.exists(scriptfile):
            logger.error("%s is not exit" % scriptfile)
            return False

        logger.info("open com")
        ser = serial.Serial(deploy_com, int(baudrate), timeout=1)
        try:
            logger.info("打开serial")
            if ser.is_open == False:
                ser.open()

            logger.info("获取单板状态")
            board_type = getBoardType(ser)
            if board_type != "uboot":
                sendResetCmd(ser, READ_TIMEOUT)
                board_type = getBoardType(ser)
                if board_type == "bootrom":
                    if not recoveryBoard(ser, usb_port):
                        logger.error("recovery board fail, please check board")
                        return False

            with open(scriptfile, "r") as fp:
                lines = fp.readlines()
                for line in lines:
                    #line = line.strip()
                    if not line:
                        logger.info("cmd is: %s " % line)
                        continue
                    if "%Tftpserver_IP%" in line:
                        line = line.replace("%Tftpserver_IP%", tftp_ip)
                    if "%Device_IP%" in line:
                        line = line.replace("%Device_IP%", device_ip)
                    if "%Device_MAC%" in line:
                        line = line.replace("%Device_MAC%", device_Mac)
                    if "%Device_Netmask%" in line:
                        line = line.replace("%Device_Netmask%", device_netmask)
                    if "%Device_GatewayIP%" in line:
                        line = line.replace("%Device_GatewayIP%", device_gatewayip)
                    if "userfs.img" in line:
                        if not os.path.exists(os.path.join(version_savepath, "img", "userfs.img")):
                            line = line.replace("userfs.img", "userfs_vfat.img")
                    if "rootfs.img" in line:
                        if not os.path.exists(os.path.join(version_savepath, "img", "rootfs.img")):
                            line = line.replace("rootfs.img", "rootfs_vfat.img")
                    if "tftp" in line:
                        packagefile_path = "/%s" % flash_type
                        new_packagefile_path = "/%s" % local_image_path
                        line = line.replace(packagefile_path, new_packagefile_path)
                        ret = sendCmd(ser, line, "hisilicon #", READ_MAXTIMEOUT)
                        if "retry count exceeded; starting again" in ret.lower():
                            logger.info("tftp cmd retry again!!")
                            ret = sendCmd(ser, line, "hisilicon #", READ_MAXTIMEOUT)
                        if "error:" in ret.lower():
                            logger.error("tftp fail")
                            return False
                        continue
                    if "reset" in line:
                        ret = sendCmd(ser, line, "OHOS #", READ_TIMEOUT)
                        continue
                    ret = sendCmd(ser, line, " #", READ_MINITIMEOUT)
            board_type = getBoardType(ser)
            if board_type == "OHOS":
                logger.info("upgrade success")
                init_cmd = "ifconfig eth0 %s netmask %s gateway %s \r" % (device_ip, device_netmask, device_gatewayip)
                sendCmd(ser, init_cmd, "OHOS #", READ_MINITIMEOUT)
                sendCmd(ser, 'ifconfig\r', "OHOS #", READ_MINITIMEOUT)
                return True
            else:
                logger.info("upgrade fail")
                return False
        except Exception as e:
            logger.printLog(e)
            return False
        finally:
            ser.close()
            logger.info("close serial")
                

def boardPowerOn(usb_port):
    logger.info("board power on start")
    
    #对端口下电
    if not usbPowerOnOff('127.0.0.1', '7788', usb_port, "off"):
        logger.error("board power off failed")
        return False
    
    #对端口上电
    if not usbPowerOnOff('127.0.0.1', '7788', usb_port, "on"):
        logger.error("board power on failed")
        return False
    logger.info("board power on end")


def getBoardType(ser):
    ret = sendCmd(ser, '\r', " #", READ_MINITIMEOUT)
    if 'HMOS' in ret or 'OHOS' in ret:
        ostype = 'OHOS'
    elif 'hisilicon' in ret:
        ostype = 'uboot'
    elif ' #' in ret:
        ostype = 'linux'
    else:
        ostype = 'bootrom'
    logger.info("board type is: %s" % ostype)
    return ostype

def sendCmd(ser, cmd, endtag, timeout):
    ser.reset_input_buffer()
    logger.info("cmd is: %s " % cmd)
    ser.write((cmd + '\n').encode())
    time.sleep(0.5)
    i = 0
    ret = ''
    while True:
        out = ser.read(ser.inWaiting())
        ret = ret + out.decode(encoding="utf-8", errors="ignore")
        if endtag in ret:
            logger.info("cmd end")
            break
        time.sleep(1)
        i = i + 1
        if i > timeout:
            logger.info("cmd timeout")
            break
    logger.info("result is: %s " % ret)
    return ret

def sendResetCmd(ser, timeout):
    logger.info("send reset")
    ser.reset_input_buffer()
    ser.write(b"reset \r\n")
    ret = ser.read(ser.inWaiting())
    time.sleep(3)
    #logger.info("result is: %s " % ret)
    ser.write(b"\r\n")
    ret = ser.read(ser.inWaiting())
    logger.info("result is: %s " % ret)
    ser.write(b"\r\n")
    ret = ser.read(ser.inWaiting())
    logger.info("result is: %s " % ret)
    ser.write(b"\r\n")
    ret = ser.read(ser.inWaiting())
    logger.info("result is: %s " % ret)
    return ret


def recoveryBoard(ser, usb_port):
    logger.info("start recovery board")
    boardPowerOn(usb_port)
    #再发送回车
    ser.write(b"\r\n")
    time.sleep(0.5)
    ret = ser.read(ser.inWaiting())
    logger.info("result is: %s " % ret)
    ser.write(b"\r\n")
    time.sleep(0.5)
    ret = ser.read(ser.inWaiting())
    logger.info("result is: %s " % ret)
    board_type = getBoardType(ser)
    if board_type == "bootrom":
        logger.error("recovery board failed")
        return False
    logger.info("recovery board succ")
    return True


if __name__ == "__main__":
    param_file = sys.argv[1]
    if not param_file:
        logger.printLog("Missing params file")
        sys.exit(-1)
    try:
        uphandle = liteOsUpgrade_L1(param_file)
        uphandle._excuteApp()
    except Exception as e:
        logger.printLog(e)
        sys.exit(-1)