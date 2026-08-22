# prosody部署说明
本次部署于CentOS Stream 9 64位系统上  
部署参考[prosody官网](https://prosody.im/)
## 相关介绍
prosody是私有化聊天服务器，基于XMPP+OMEMO便可以实现端到端加密通信，加密理论安全性和Signal相当。  
个人认为wire的开源方案更好，但是部署wire需要更多的服务器资源，详见[官网](https://wire.com/)和[相关开源](https://github.com/wireapp/wire)
## 服务端prosody部署
需要开放的端口`5222、5280、5281`
### 1、安装prosody
prosody的命令安装已经非常完善  
对于Debian 和Ubuntu只需要`sudo apt install prosody`即可安装  
但是对于centos9（红帽类系统）则需要
```  
dnf install epel-release
crb enable
dnf install prosody
``` 
### 2、安装OMEMO 模块（端到端加密）
```
dnf install mercurial
hg clone https://hg.prosody.im/prosody-modules/ /usr/share/prosody/modules
```

### 3、配置prosody，参考[官方配置](https://prosody.im/doc/configure)
配置文件位于`etc/prosody/prosody.cfg.lua`  
文件内加入以下部分
```
-- 这里使用公网 IP 作为虚拟域名，适合没有域名的服务器
VirtualHost "your-server-ip"  -- 如 "123.45.67.89"
  ssl = {
    key = "/etc/pki/prosody/your-server-ip.key";
    certificate = "/etc/pki/prosody/your-server-ip.crt";
  }
-- 启用 OMEMO 支持
modules_enabled = {
  "omemo_store";
  "http_upload";  -- 文件传输支持
  "carbons";       -- 多设备同步
}
```
并检查如下模块是否开启（是否已取消注释）
```
"bosh";          -- 启用HTTP轮询连接
"websocket";     -- 启用WebSocket连接
"mam";           -- 消息归档
```
默认情况下客户端是不允许注册账户的，只允许服务端直接注册  
如有需要将`allow_registration` 设置成`true`即可
### 4、生成自签名证书（适合只有公网ip的服务器）
**默认证书存放在`/etc/pki/prosody/`下**  
将以下代码的`your-server-ip`替换为公网ip
```
openssl req -newkey rsa:4096 -x509 -days 365 -nodes \
    -out /etc/pki/prosody/your-server-ip.crt \
    -keyout /etc/pki/prosody/your-server-ip.key \
    -subj "/CN=your-server-ip" \
    -addext "subjectAltName = IP:your-server-ip"

```
tip:如果不加`addext`客户端会提示证书与网站预期身份不符  
**完成后添加证书权限**
```
chown -R prosody:prosody /etc/pki/prosody/
chmod 600 /etc/pki/prosody/*.key
```
### 5、启动prosody
执行`systemctl start prosody`  
之后便可以使用`prosodyctl`命令管理  
如`prosodyctl adduser xxx xxxxx`

## 客户端
windows客户端使用[Gajim](https://gajim.org/)，直接登录后在与他人的对话框中可以选择`OMEMO`加密


