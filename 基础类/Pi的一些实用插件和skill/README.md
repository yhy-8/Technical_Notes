# Pi的一些实用插件、skill、细节
这里说的是Pi Agent：https://github.com/earendil-works/pi

## 插件
1、**bocha-search.ts**：自写的基于博查搜索的轻量级web-search，实测可用。博查链接：https://open.bochaai.com/  
2、**@pi-lab/webfetch**： 第三方开源插件，实现wsb-fetch能力，配合第一个插件丰富Agent的搜索能力。插件链接：https://pi.dev/packages/@pi-lab/webfetch  
3、**permission.ts**：自写的轻量级权限管理，实现高危命令及工作区外文件访问需要人为同意。但后者是软约束，AI仍然通过bash实现工作区外文件访问。  
## Skills
1、**作为全局人格**：很简洁的一些约束，放到`~/.pi/agent/AGENTS.md`。链接：https://github.com/multica-ai/andrej-karpathy-skills  
2、**作为详细的coding手册**：详细的每个具体的行为应该如何做的说明，放到`~/.pi/agent/skills`。链接htps://github.com/mattpocock/skills  
 
**实际上我把1的全部和2的全局说明部分整合到一个`~/.pi/agent/AGENTS.md`**
## 细节
1、配置模型在`~/.pi/agent/models.json`，示例：
```
{
  "providers": {
    "deepseek": {
      "baseUrl": "https://api.deepseek.com",
      "api": "openai-completions",
      "apiKey": "你的key",
      "models": [
        {
          "id": "deepseek-v4-flash-vision-exp",
          "name": "DS-V4-Flash-Vsion",
          "contextWindow": 1000000,
          "input": ["text", "image"],
          "reasoning": true
        },
        {
          "id": "deepseek-v4-pro",
          "name": "DS-V4-Pro",
          "contextWindow": 1000000,
          "reasoning": true
        }
      ]
    }
  }
}
```
**这里对于多模态模型需要特别说明input参数支持image，对于reasoning参数一般显式开启**