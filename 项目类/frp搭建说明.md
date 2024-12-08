# frp搭建说明
frp安装包下载地址：https://github.com/fatedier/frp/releases
## 一、安装和运行frp
1、压缩包分有windows版、linux版，不同系统需要安装对应的版本  
2、将 frpc 复制到内网服务所在的机器上，将 frps 复制到拥有公网 IP 地址的机器上，并将它们放在任意目录  
3、使用以下命令启动服务器：`./frps -c ./frps.toml`（可以挂载到systemd运行）
使用以下命令启动客户端：`./frpc -c ./frpc.toml`
## 二、配置toml文档
toml文档示例（端口映射-网页模式，所有流量都会中转服务器）  
此处服务端需放行7000和7001端口

服务端：
```
bindPort = 7000
vhostHTTPPort = 7001
auth.method="token"
auth.token="aaa123"
```

客户端：
```
serverAddr = "47.102.194.65"
serverPort = 7000

auth.method="token"
auth.token="aaa123"

[[proxies]]
name = "web"
type ="http"
localIp="10.11.183.198"
localPort = 8096
customDomains = ["47.102.194.65"]
```