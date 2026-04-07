# claude接入与配置指南

**linux版**

安装claude code：`curl -fsSL https://claude.ai/install.sh | bash`

### 使用CC-Switch转换
源码地址：https://github.com/farion1231/cc-switch

下载对应.deb安装包   
运行：`sudo apt install ./<软件包.deb>`

直接填入第三方API和KEY，设置对应模型即可转换

### claude接入IDE

在ide内置终端里运行:`claude --ide`   

可能提示需要插件   
如PyCharm需要安装一个由**Anthropic**发布的**Claude Code Beta**插件