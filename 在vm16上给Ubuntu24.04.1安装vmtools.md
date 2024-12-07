# 在vm16上给Ubuntu24.04.1安装vmtools
前提：安装系统的时候在虚拟机“设置”-“显示器”中关闭加速3d图像，不然会严重卡顿。之后最好都不要开启该选项  
说明：该操作主要针对解决低版本vm上运行高版本ubuntu的问题
## 一、切换源
1、在“软件与更新”中“Ubuntu软件”选项卡中“下载自”，选择其他，用mirrors.aliyun.com  
2、备份当前源：`sudo cp /etc/apt/sources.list.d/ubuntu.sources  /etc/apt/sources.list.d/ubuntu.sources.bak`  
3、运行：`sudo nano /etc/apt/sources.list.d/ubuntu.sources`（默认是没有安装vim的，只好使用nano）  
4、在原基础上更改为如下代码（实际只需要加上noble-security），并删除所有国外源，不然更新软件时一样会导致失败：
```
Types: deb
URIs: http://mirrors.aliyun.com/ubuntu/
Suites: noble noble-updates noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
```
## 二、安装vmtool：
更新软件：`sudo apt-get update`  
移除原有tools：`sudo apt-get autoremove open-vm-tools`  
安装tools：`sudo apt-get install open-vm-tools-desktop`  
重启：`sudo reboot`
