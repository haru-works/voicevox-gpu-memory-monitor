##################################################
# VOICEVOX　GPUメモリ監視プログラム
##################################################
import subprocess
from subprocess import PIPE
import time
from io import StringIO
import pandas as pd
import psutil

##################################################
# 設定
##################################################
# 実行コマンド ※環境によって変更する
exe_path = "C:\\voicevox_engine\\0.14.3\\engine\\windows-directml\\run.exe --use_gpu"
# メモリ仕使用率閾値　※環境によって変更する
threshold = 80
# インターバル(秒)　※環境によって変更する
interval = 10.0
# VOICEVOX EXE名
exe_name = "run.exe"
# CSV に出力するカラム一覧
keys = ["timestamp","memory.total","memory.free","memory.used"]

##################################################
# GPUスペック出力関数
##################################################
def get_gpu_specs():
    spec_keys = ["index","name","memory.total"]
    output = get_gpu_info(spec_keys)
    output = pd.read_csv(StringIO(output), names=spec_keys)
    return output

##################################################
# GPU情報出力関数
##################################################
def get_gpu_info(keys=keys, no_units=True):
    queries = ",".join(keys)
    output_fmt = "csv,noheader"
    if no_units:
        output_fmt += ",nounits"

    cmd = f"nvidia-smi --query-gpu={queries} --format={output_fmt}"
    output = subprocess.check_output(cmd, shell=True).decode()
    # カンマの後の空白を削除する
    output = output.replace(", ", ",")

    return output



# GPU の一覧を取得
gpu_specs = get_gpu_specs()

# 初期画面表示
print("-----------------------------------------------------------------------------")
print("VOICEVOX GPUメモリ監視プログラム")
print("--説明--")
print(" GPUメモリ使用率が" + str(threshold) + "%を超えたら VOICEVOX run.exe再起動")
print(" GPUメモリ使用率を" + str(interval) + "秒間隔で監視")
print("-----------------------------------------------------------------------------")
print("--GPU情報--")
print(gpu_specs.head(1))
print("-----------------------------------------------------------------------------")
print("--実行コマンド--")
print(exe_path)
print("-----------------------------------------------------------------------------")

# ここから監視処理
while True:

    #プロセス存在フラグ初期化
    process_exist_flg = False
    #使用率初期化
    use_rate = 0
    # GPU の情報を取得
    output = get_gpu_info(keys)
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

            # プロセス名チェック
            if(processName == exe_name):
                # プロセスあればフラグTrrue
                process_exist_flg = True
                # メモリ使用率計算
                # memory.used / memory.total * 100
                use_rate = round(int(gpu_info[3]) / int(gpu_info[1]),2) * 100
                # 画面表示用
                print(gpu_info[0] +
                      " - " + str(gpu_info[1]) + "MB" +
                      " - " + str(gpu_info[2]) + "MB" +
                      " - " + str(gpu_info[3]) + "MB" +
                      " - " + str(use_rate) + "%" +
                      " - " + str(processName) +
                      " -  " + str(processID) +
                      " -  " + cmd_line_str)

                #もし、使用率が閾値を超えたらプロセス再起動
                if(use_rate > threshold):
                    # プロセスIDからプロセス取得
                    p = psutil.Process(processID)

                    #子のterminate
                    pid_list=[pc.pid for pc in p.children(recursive=True)]
                    for pid in pid_list:
                        psutil.Process(pid).terminate ()
                        print("terminate child process {}" .format(pid))

                    #親のterminate
                    p.terminate ()
                    print("terminate parent process {}" .format(processID))

                    #再起動
                    print("voicevox process memory overflow ---> restart " + exe_path)
                    res_vve = subprocess.Popen(exe_path)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    #プロセスが存在しなかったら起動する
    if(process_exist_flg == False):
        print("voicevox process  not found ---> start " + exe_path)
        res_vve = subprocess.Popen(exe_path)

    #スリープ
    time.sleep(interval)
