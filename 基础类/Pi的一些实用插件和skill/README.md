# Pi的一些实用插件、skill、细节
这里说的是Pi Agent：https://github.com/earendil-works/pi

## 插件
* **bocha-search.ts**：自写的基于博查搜索的轻量级web-search，实测可用。博查链接：https://open.bochaai.com/  
* **@pi-lab/webfetch**： 第三方开源插件，实现wsb-fetch能力，配合第一个插件丰富Agent的搜索能力。插件链接：https://pi.dev/packages/@pi-lab/webfetch  
* **pi-token-speed**：第三方开源插件，显示token速率。插件链接：https://pi.dev/packages/pi-token-speed  
* **permission.ts**：自写的轻量级权限管理，实现高危命令需要人为同意。
## Skills
* **作为全局人格**：很简洁的一些约束，放到`~/.pi/agent/AGENTS.md`。链接：https://github.com/multica-ai/andrej-karpathy-skills  
* **作为详细的coding手册**：详细的每个具体的行为应该如何做的说明，放到`~/.pi/agent/skills`。链接https://github.com/mattpocock/skills  
 
**实际上我把1的全部和2的全局说明部分整合到一个`~/.pi/agent/AGENTS.md`**
## 配置
配置模型在`~/.pi/agent/models.json`，示例：
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
          "reasoning": true,
          "maxTokens": 100000
        },
        {
          "id": "deepseek-v4-pro",
          "name": "DS-V4-Pro",
          "contextWindow": 1000000,
          "reasoning": true,
          "maxTokens": 100000
        }
      ]
    }
  }
}
```
* **input**：对于多模态模型需要特别说明该参数支持image  
* **reasoning**：该参数一般显式开启
* **maxTokens**：该模型单次请求能输出的最大Token数