# yolo11环境配置
本次使用的是ubuntu24.04.1版本  
yolo官方文档：https://docs.ultralytics.com/  
## 一、Anaconda相关操作
### 1、安装Anaconda
去官网(https://www.anaconda.com/download/success)下载对应版本，这里下载的是完整版，并非mini版  
也可复制sh安装文件到ubuntu  
切换到sh文件目录下  
运行./a.sh(这里改名为a.sh，方便命令行操作)  
全程回车或者yes  
新打开一个命令窗口，输入conda -V检查是否安装完成  
### 2、虚拟环境操作
`conda create -n yolov11 python=3.12.7 `   创建虚拟环境，指定python版本  
`conda activate yolov11 `                  激活虚拟环境  
`conda activate       `                    恢复默认环境 
## 二、环境配置（以下均在yolov11虚拟环境进行）
### 1、切换下载源
```
pip install pip -U  
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple  
```
此处为清华源
### 2、安装pytorch
去官网(https://pytorch.org/)找到对应版本的下载命令下载即可
### 3、安装其余依赖包
```
pip install -r requirements.txt  
```
详见yolo_requirements.txt

## 三、使用yolo
python源码中加入`from ultralytics import YOLO`即可  
注意：运行py文件需在yolov11虚拟环境中