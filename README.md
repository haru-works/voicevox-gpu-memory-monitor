# voicevox-gpu-memory-monitor
VOICEVOX GPUメモリ監視プログラム

VOICEVOX Engine用のGPUメモリ使用率を監視するプログラムです。
GPUメモリ使用率が設定した閾値を超えたら、VOICEVOX Engineのrun.exeを再起動します。
プログラムはpythonで作ってます。

※nvidiaのGPU用です。
コマンド「nvidia-smi」が使える環境が前提です。
pandas、psutil、subprocess等のpythonライブラリが必要です。
![キャプチャ](https://user-images.githubusercontent.com/89264182/218312485-49584abf-551a-4130-9fe6-8c74021ea02e.JPG)
