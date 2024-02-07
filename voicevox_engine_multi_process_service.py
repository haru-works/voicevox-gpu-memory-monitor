##################################################
# VOICEVOX Engine マルチプロセス 監視プログラム
##################################################
import os
import win32service
import win32serviceutil
import win32event
import logging
import servicemanager
import socket
import datetime
import time
import subprocess
from subprocess import PIPE
import time
from io import StringIO
import pandas as pd
import psutil

##################################################
# ログ設定
##################################################
today = datetime.date.today()
logging.basicConfig(
    # ログ出力先　※環境によって変更する
    filename = 'C:\\voicevox_engine\\voicevox-gpu-memory-monitor\\log\\{}-app.log'.format(today.strftime('%Y%m%d')),
    level = logging.DEBUG,
    format="%(asctime)s:LINE[%(lineno)s] %(levelname)s %(message)s"
)

##################################################
# PythonServiceクラス
##################################################
class PythonService(win32serviceutil.ServiceFramework):
    # サービス名
    _svc_name_ = 'VoiceVox Engine Multi Process Service'
    # 表示名(サービス画面にはこれを表示)
    _svc_display_name_ = 'VoiceVox Engine Multi Process Service'
    # サービスの説明
    _svc_description_ = '一定周期でVoiceVox Engineで使っているGPUメモリを監視する'
    # 実行コマンド ※環境によって変更する
    # _exe_path = "C:\\voicevox_engine\\0.14.7\\windows-directml\\run.exe --use_gpu --host 10.0.0.3"
    _exe_path = ["C:\\voicevox_engine\\voicevox-gpu-memory-monitor\\vv1_gpu.bat",
                 "C:\\voicevox_engine\\voicevox-gpu-memory-monitor\\vv2.bat",
                 "C:\\voicevox_engine\\voicevox-gpu-memory-monitor\\vv3.bat"]
    # VOICEVOX EXE名
    _exe_name_gpu = "run_gpu.exe"
    _exe_name_cpu = "run_cpu.exe"
    # メモリ仕使用率閾値　※環境によって変更する
    _threshold = 90
    # インターバル(秒)　※環境によって変更する
    _interval = 10.0
    # CSV に出力するカラム一覧
    _keys = ["timestamp","memory.total","memory.free","memory.used"]
    # GPUスペック出力カラム一覧
    _spec_keys = ["index","name","memory.total"]

    # 初期化
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.stop_event = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False


    # サービス停止
    def SvcStop(self):
        logging.info("execute service stop")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.stop_requested = True


    # サービス開始
    def SvcDoRun(self):
        logging.info("execute service start")
        servicemanager.LogMsg(
			servicemanager.EVENTLOG_INFORMATION_TYPE,
			servicemanager.PYS_SERVICE_STARTED,
			(self._svc_name_,'')
			)
        # メイン処理スタート
        self.main_loop() 


    # GPUスペック出力関数
    def get_gpu_specs(self):
        output = self.get_gpu_info(self._spec_keys)
        output = pd.read_csv(StringIO(output), names=self._spec_keys)
        return output


    # GPU情報出力関数
    def get_gpu_info(self,keys=_keys, no_units=True):
        queries = ",".join(keys)
        output_fmt = "csv,noheader"
        if no_units:
            output_fmt += ",nounits"

        cmd = f"nvidia-smi --query-gpu={queries} --format={output_fmt}"
        output = subprocess.check_output(cmd, shell=True).decode()
        # カンマの後の空白を削除する
        output = output.replace(", ", ",")
        return output


    # メイン処理
    def main_loop(self):       

        logging.info("service start successful")

        # GPU の一覧を取得
        gpu_specs = self.get_gpu_specs()

        # 初期画面表示
        logging.info("-----------------------------------------------------------------------------")
        logging.info("VOICEVOX GPU memory monitoring service")
        logging.info("--description--")
        logging.info(" GPU memory use rate" + str(self._threshold) + "%over VOICEVOX run.exe restart")
        logging.info(" GPU memory use rate" + str(self._interval) + "sec intarvel monitoring")
        logging.info("-----------------------------------------------------------------------------")
        logging.info("--GPU info--")
        logging.info(gpu_specs.head(1))
        logging.info("-----------------------------------------------------------------------------")
        logging.info("--exe path--")
        for exe_path in self._exe_path:
            logging.info(exe_path)
        logging.info("-----------------------------------------------------------------------------")

        while True: 
            if self.stop_requested:
                logging.info("service stopping")
                break            
            try:
                time.sleep(self._interval)
                # logging.info('service in progress')
                #プロセス存在フラグ初期化
                process_exist_flg = False
                #使用率初期化
                use_rate = 0
                # GPU の情報を取得
                output = self.get_gpu_info(self._keys)
                # データを分割＆改行削除
                gpu_info = output.replace('\r\n','').split(',')

                # プロセス取得
                for proc in psutil.process_iter():
                    try:
                        # プロセス情報取得
                        processName = proc.name()
                        processID = proc.pid
                        cmdLine = proc.cmdline()
                        cmd_line_str = ' '.join(cmdLine)

                        # 全プロセス存在チェック
                        if(processName == self._exe_name_cpu or processName == self._exe_name_gpu):
                            # どれか１つプロセスあればフラグ true
                            process_exist_flg = True

                        # GPUプロセスメモリチェック
                        if(processName == self._exe_name_gpu):
                            # メモリ使用率計算
                            # memory.used / memory.total * 100
                            use_rate = round(int(gpu_info[3]) / int(gpu_info[1]),2) * 100
                            # 画面表示用
                            logging.info(gpu_info[0] +
                                " - " + str(gpu_info[1]) + "MB" +
                                " - " + str(gpu_info[2]) + "MB" +
                                " - " + str(gpu_info[3]) + "MB" +
                                " - " + str(use_rate) + "%" +
                                " - " + str(processName) +
                                " -  " + str(processID) +
                                " -  " + cmd_line_str)

                            #もし、使用率が閾値を超えたらプロセス再起動
                            if(use_rate > self._threshold):
                                # プロセスIDからプロセス取得
                                p = psutil.Process(processID)

                                #子のterminate
                                pid_list=[pc.pid for pc in p.children(recursive=True)]
                                for pid in pid_list:
                                    psutil.Process(pid).terminate ()
                                    logging.info("terminate child process {}" .format(pid))

                                #親のterminate
                                p.terminate ()
                                logging.info("terminate parent process {}" .format(processID))

                                #GPU版を再起動
                                logging.info("gpu memory overflow ---> voicevox engine gpu restart " + self._exe_path[0])
                                res_vve = subprocess.Popen(exe_path)

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass

                #全プロセスが存在しなかったらすべて起動する
                if(process_exist_flg == False):
                    for exe_path in self._exe_path:
                        logging.info("voicevox engine process " + self._exe_name_gpu + "&"+ self._exe_name_cpu + " not found ---> start " + exe_path)
                        res_vve = subprocess.Popen(exe_path)

            except Exception as e:
                logging.error("Error occured.")
                logging.error(str(type(e)))
                logging.error(str(e.args))
                logging.error(str(e))

        logging.info("service stop successful")
        return

if __name__ == '__main__':
	win32serviceutil.HandleCommandLine(PythonService)