# RustDesk搭建说明
服务端下载：https://github.com/rustdesk/rustdesk-server/releases  
客户端下载：https://github.com/rustdesk/rustdesk/releases
## 服务端：
1、解压服务端压缩包，进入文件夹  
2、使用systemd启动文件夹中的hbbr和hbbs  
3、记录id_xxxx.pub文件内的key  
4、开放TCP的21115到21119，开放UDP的21116

## 客户端：
设置里填入ID/中继服务器地址，以及key即可
