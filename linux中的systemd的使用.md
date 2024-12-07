# systemd的使用
查看 systemd 的状态及服务配置文件存放处：`systemctl status`（通常配置文件在：usr/lib/systemd/system）  
启动服务：`sudo systemctl start <服务名>`  
停止服务：`sudo systemctl stop <服务名>`  
重启服务：`sudo systemctl restart <服务名>`  
重新加载服务配置（不重启服务）：`sudo systemctl reload <服务名>`  
查看服务状态：`systemctl status <服务名>`  
启用服务（使服务在系统启动时自动启动）：`sudo systemctl enable <服务名>`  
禁用服务（使服务在系统启动时不自动启动）：`sudo systemctl disable <服务名>`  
列出所有服务及其状态：`systemctl list-units --type=service`  
列出所有服务（包括未启动的）：`systemctl list-unit-files --type=service`  
查看系统日志：`journalctl`  
查看某个服务的日志：`journalctl -u <服务名>`