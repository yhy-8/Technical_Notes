# 在CentOS Stream 9 64位上搭载MaiBot
**源自开源项目[MaiBot(麦麦qq机器人)](https://github.com/MaiM-with-u/MaiBot)**
## 一、搭建说明
### 1、**python环境**
该系统默认安装有适合的python环境。直接root用户的情况下，可以不使用venv创建虚拟环境，MaiBot-main(原项目文件夹)下执行`pip install -r requirements.txt`  

### 2、**安装并启动MongoDB**
参考[MongoDB官方文档](https://www.mongodb.com/zh-cn/docs/manual/tutorial/install-mongodb-on-red-hat/) 

执行命令:  `vim /etc/yum.repos.d/mongodb-org-8.0.repo`  

**mongodb-org-8.0.repo**中写入：  
```
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
```
完成后执行：`sudo yum install -y mongodb-org`  
刷新服务配置：`systemctl daemon-reload`  
启动MogoDB：`systemctl start mongod`  
查看MogoDB状态：`systemctl status mongod`  
至此，有关MogoDB的操作全部完成

### 3、**安装NapCat框架**
参考[NapCat官方文档](https://www.napcat.wiki/guide/boot/Shell#napcat-installer-linux%E4%B8%80%E9%94%AE%E4%BD%BF%E7%94%A8%E8%84%9A%E6%9C%AC-%E6%94%AF%E6%8C%81ubuntu-20-debian-10-centos9)

执行：`curl -o napcat.sh https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh && sudo bash napcat.sh --cli y`  

默认安装后配置文件位于：`/opt/QQ/resources/app/app_launcher/napcat/config`  
默认只存在**napcat.json**文件，在该文件夹下执行`vim onebot11.json`创建**onebot11.json**文件  

**napcat.json**内容为：
```
{
    "fileLog": false,
    "consoleLog": true,
    "fileLogLevel": "debug",
    "consoleLogLevel": "info",
    "packetBackend":"auto",
    "packetServer": "ws://127.0.0.1:8080/onebot/v11/ws",
    "o3HookMode": 1
}
```
**onebot11.json**内容为：
```
{
  "network": {
    "httpServers": [],
    "httpSseServers": [],
    "httpClients": [],
    "websocketServers": [],
    "websocketClients": [
      {
        "name": "WsClient",
        "enable": true,
        "url": "ws://127.0.0.1:8080/onebot/v11/ws",
        "messagePostFormat": "array",
        "reportSelfMessage": false,
        "reconnectInterval": 5000,
        "token": "",
        "debug": false,
        "heartInterval": 30000
      }
    ],
    "plugins": []
  },
  "musicSignUrl": "",
  "enableLocalFile2Url": false,
  "parseMultMsg": false
}
```

### 4、**配置MaiBot**  
创建两个文件.env.prod和bot_config.toml  
**.env.prod**位于MaiBot-main(原项目文件夹)下；**bot_config.toml**位于MaiBot-main/config下

**.env.prod**内容为：
```
# API配置
SILICONFLOW_KEY=your_key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1/
DEEP_SEEK_KEY=your_key
DEEP_SEEK_BASE_URL=https://api.deepseek.com/v1
CHAT_ANY_WHERE_KEY=your_key
CHAT_ANY_WHERE_BASE_URL=https://api.chatanywhere.tech/v1

# 服务配置
HOST=127.0.0.1  
PORT=8080       # 与反向端口相同

# 数据库配置
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017

DATABASE_NAME=MegBot

# 也可以使用URI连接数据库，取消注释填写在下面这行（URI的优先级比上面的高）
MONGODB_URI=mongodb://127.0.0.1:27017/MegBot

# 插件配置
PLUGINS=["src2.plugins.chat"]

```  
**bot_config.toml**内容为：
```
[inner]
version = "0.0.10"

#以下是给开发人员阅读的，一般用户不需要阅读
#如果你想要修改配置文件，请在修改后将version的值进行变更
#如果新增项目，请在BotConfig类下新增相应的变量
#1.如果你修改的是[]层级项目，例如你新增了 [memory],那么请在config.py的 load_config函数中的include_configs字典中新增"内容":{
#"func":memory,
#"support":">=0.0.0",  #新的版本号
#"necessary":False      #是否必须
#}
#2.如果你修改的是[]下的项目，例如你新增了[memory]下的 memory_ban_words ,那么请在config.py的 load_config函数中的 memory函数下新增版本判断:
            # if config.INNER_VERSION in SpecifierSet(">=0.0.2"):
            #     config.memory_ban_words = set(memory_config.get("memory_ban_words", []))

[bot]
qq = 123
nickname = "麦麦"
alias_names = ["麦叠", "牢麦"]

[personality]
prompt_personality = [
        "用一句话或几句话描述性格特点和其他特征",    
        "用一句话或几句话描述性格特点和其他特征",    
        "例如，是一个热爱国家热爱党的新时代好青年"    
    ]
personality_1_probability = 0.7 # 第一种人格出现概率
personality_2_probability = 0.2 # 第二种人格出现概率
personality_3_probability = 0.1 # 第三种人格出现概率，请确保三个概率相加等于1
prompt_schedule = "用一句话或几句话描述描述性格特点和其他特征"

[message]
min_text_length = 2 # 与麦麦聊天时麦麦只会回答文本大于等于此数的消息
max_context_size = 15 # 麦麦获得的上文数量
emoji_chance = 0.2 # 麦麦使用表情包的概率
thinking_timeout = 120 # 麦麦思考时间

response_willing_amplifier = 1 # 麦麦回复意愿放大系数，一般为1
response_interested_rate_amplifier = 1 # 麦麦回复兴趣度放大系数,听到记忆里的内容时放大系数
down_frequency_rate = 3 # 降低回复频率的群组回复意愿降低系数 除法
ban_words = [
    # "403","张三"
    ]

ban_msgs_regex = [
    # 需要过滤的消息（原始消息）匹配的正则表达式，匹配到的消息将被过滤（支持CQ码），若不了解正则表达式请勿修改
    #"https?://[^\\s]+", # 匹配https链接
    #"\\d{4}-\\d{2}-\\d{2}", # 匹配日期
    # "\\[CQ:at,qq=\\d+\\]" # 匹配@
]

[emoji]
check_interval = 300 # 检查表情包的时间间隔
register_interval = 20 # 注册表情包的时间间隔
auto_save = true  # 自动偷表情包
enable_check = false  # 是否启用表情包过滤
check_prompt = "符合公序良俗" # 表情包过滤要求

[cq_code]
enable_pic_translate = false

[response]
model_r1_probability = 0.8 # 麦麦回答时选择主要回复模型1 模型的概率
model_v3_probability = 0.1 # 麦麦回答时选择次要回复模型2 模型的概率
model_r1_distill_probability = 0.1 # 麦麦回答时选择次要回复模型3 模型的概率
max_response_length = 1024 # 麦麦回答的最大token数

[willing]
willing_mode = "classical"
# willing_mode = "dynamic"
# willing_mode = "custom"

[memory]
build_memory_interval = 2000 # 记忆构建间隔 单位秒   间隔越低，麦麦学习越多，但是冗余信息也会增多
memory_compress_rate = 0.1 # 记忆压缩率 控制记忆精简程度 建议保持默认,调高可以获得更多信息，但是冗余信息也会增多

forget_memory_interval = 1000 # 记忆遗忘间隔 单位秒   间隔越低，麦麦遗忘越频繁，记忆更精简，但更难学习
memory_forget_time = 24 #多长时间后的记忆会被遗忘 单位小时 
memory_forget_percentage = 0.01 # 记忆遗忘比例 控制记忆遗忘程度 越大遗忘越多 建议保持默认


memory_ban_words = [ #不希望记忆的词
    # "403","张三"
]

[mood]
mood_update_interval = 1.0 # 情绪更新间隔 单位秒
mood_decay_rate = 0.95 # 情绪衰减率
mood_intensity_factor = 1.0 # 情绪强度因子

[keywords_reaction] # 针对某个关键词作出反应
enable = true  # 关键词反应功能的总开关

[[keywords_reaction.rules]] # 如果想要新增多个关键词，直接复制本条，修改keywords和reaction即可
enable = true # 是否启用此条（为了人类在未来AI战争能更好地识别AI（bushi），默认开启）
keywords = ["人机", "bot", "机器", "入机", "robot", "机器人"] # 会触发反应的关键词
reaction = "有人说你是人机或者机器人，否定这一事实，攻击或反问他。注意，只有认为你是机器人才回复，否则不要否认" # 触发之后添加的提示词

[[keywords_reaction.rules]] # 就像这样复制
enable = false # 仅作示例，不会触发
keywords = ["测试关键词回复","test",""]
reaction = "回答“测试成功”"

[chinese_typo]
enable = true # 是否启用中文错别字生成器
error_rate=0.002 # 单字替换概率
min_freq=9 # 最小字频阈值
tone_error_rate=0.2 # 声调错误概率
word_replace_rate=0.006 # 整词替换概率

[others]
enable_advance_output = false # 是否启用高级输出
enable_kuuki_read = true # 是否启用读空气功能
enable_debug_output = false # 是否启用调试输出
enable_friend_chat = false # 是否启用好友聊天

[groups]
talk_allowed = [
    123,
    123,
]  #可以回复消息的群
talk_frequency_down = []  #降低回复频率的群
ban_user_id = []  #禁止回复消息的QQ号

[remote] #测试功能，发送统计信息，主要是看全球有多少只麦麦
enable = true


#下面的模型若使用硅基流动则不需要更改，使用ds官方则改成.env.prod自定义的宏，使用自定义模型则选择定位相似的模型自己填写
#推理模型：
[model.llm_reasoning] #回复模型1 主要回复模型
name = "Pro/deepseek-ai/DeepSeek-R1"
provider = "SILICONFLOW"
pri_in = 0 #模型的输入价格（非必填，可以记录消耗）
pri_out = 0 #模型的输出价格（非必填，可以记录消耗）

[model.llm_reasoning_minor] #回复模型3 次要回复模型
name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
provider = "SILICONFLOW"

#非推理模型

[model.llm_normal] #V3 回复模型2 次要回复模型
name = "Pro/deepseek-ai/DeepSeek-V3"
provider = "SILICONFLOW"

[model.llm_normal_minor] #V2.5
name = "deepseek-ai/DeepSeek-V2.5"
provider = "SILICONFLOW"

[model.llm_emotion_judge] #主题判断 0.7/m
name = "Qwen/Qwen2.5-14B-Instruct"
provider = "SILICONFLOW"

[model.llm_topic_judge] #主题判断：建议使用qwen2.5 7b
name = "Pro/Qwen/Qwen2.5-7B-Instruct"
provider = "SILICONFLOW"

[model.llm_summary_by_topic] #建议使用qwen2.5 32b 及以上
name = "Qwen/Qwen2.5-32B-Instruct"
provider = "SILICONFLOW"
pri_in = 0
pri_out = 0

[model.moderation] #内容审核 未启用
name = ""
provider = "SILICONFLOW"
pri_in = 0
pri_out = 0

# 识图模型

[model.vlm] #图像识别 0.35/m
name = "Pro/Qwen/Qwen2-VL-7B-Instruct"
provider = "SILICONFLOW"

#嵌入模型

[model.embedding] #嵌入
name = "BAAI/bge-m3"
provider = "SILICONFLOW"
```

### 5、**配置MaiBot后台服务**
后台服务配置文件存放位置：  
常规存放：`/usr/lib/systemd/system/`  
其他存放：`/etc/systemd/system/`  
在`/usr/lib/systemd/system/`中创建**MaiBot.service**   

**MaiBot.service**内容为
```
[Unit]
Description=MaiBot
After=network.target mongod.service

[Service]
User=root
Type=simple
WorkingDirectory=/home/MaiBot/MaiBot-main
ExecStart=python3 bot.py
ExecStop=/bin/kill -2 $MAINPID

[Install]
WantedBy=multi-user.target
```
其中WorkingDirectory为原项目存放位置

## 二、启动流程
### 1、确保8080和27017端口开放，且没被占用 

### 2、需要启动三个程序：MongoDB、NapCat、MaiBot。**MaiBot**留到最后启动    
**MongoDB**：服务名为`mongod`，启动服务即可  
**NapCat**:执行`napcat help`查看帮助。一般执行`napcat start {QQ}`后，使用`napcat log {QQ}`查看日志并扫码登录QQ  
**MaiBot**：若按上面配置MaiBot后台服务，则服务名为`MaiBot`，启动服务即可。也可以在MaiBot-main文件夹(原项目文件夹)下通过`python3 bot.py`运行，但不建议这样长期运行  


### 至此便完成所有部署启动流程

### 更详细请参考[原项目教程](MaiBot-main/docs/manual_deploy_linux.md)
