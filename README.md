# voicevox-gpu-memory-monitor
VOICEVOX GPUメモリ監視プログラム

VOICEVOX Engine用のGPUメモリ使用量を監視するプログラムです。
GPUメモリ使用量が設定した閾値を超えたら、VOICEVOX Engineのrun.exeを再起動します。
プログラムはpythonで作ってます。

※nvidiaのGPU用です。
コマンド「nvidia-smi」が使える環境が前提です。
pandas、psutil、subprocess等のpythonライブラリが必要です。
