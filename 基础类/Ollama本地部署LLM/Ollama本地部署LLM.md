# Ollama本地部署LLM
**参考[Ollama官方网站](https://ollama.com/)**
## 一、windows系统
去官网下载安装包，或使用已有的安装包，双击默认安装即可  
注意：正常完成安装会默认安装在c盘  

**可以通过以下步骤迁移：**  
### 1、文件移动
（1）将`C:\Users\XX\AppData\Local\Programs\Ollama`这个文件夹移动到其他盘（这就是Ollama的安装目录），例如改为`D:\Ollama`  
（2）将模型文件所在的目录`C:\Users\XX\.ollama`也移动到其他盘（建议修改系统变量后再下载模型，可以避免模型下载到c盘），例如改为`D:\Ollama\.ollama`  

### 2、修改环境变量，以便Ollama能够正确找到新的安装位置
（1）修改用户变量的PATH变量，将原来的`C:\Users\XX\AppData\Local\Programs\Ollama`路径更新为新的位置（win11中打开：编辑系统环境变量，点击“环境变量”，然后在用户变量中找到“Path”，编辑即可）。例如`D:\Ollama`  
（2）在环境变量或者用户变量中新建一个名为OLLAMA_MODELS的变量，设置其值为模型文件的新位置（同上找到用户变量，书写时注意：OLLAMA和MODELS之间有下划线）。例如`D:\Ollama\.ollama\models`

### 3、验证安装
打开cmd，通过输入`ollama -v`命令来打印Ollama的版本号，并使用`ollama list`来列出已下载的模型


## 二、linux系统
压缩包可直接下载或使用已有的
关于下载：`curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz`  
运行：`sudo tar -C /usr -xzf ollama-linux-amd64.tgz`  
进入解压后文件夹，启动ollama服务：`ollama serve `   
新开一个terminal即可使用：`ollama -v`  

## 三、其他事项
### 1、Ollama模型存放位置
模型本体文件位于`.ollama\models\blobs`  

在`.ollama\models\manifests`下还有多层文件夹嵌套,最后会有模型的识别文件
### 2、ChatBox连接到Ollama
![Ollma连接到ChatBox](chatbox连接到ollama.jpg)