# Pi的一些实用插件、skill、细节
这里说的是Pi Agent：https://github.com/earendil-works/pi

## 插件
* **bocha-search.ts**：自写的基于博查搜索的轻量级web-search，实测可用。博查链接：https://open.bochaai.com/  
* **deepseek-search.ts**：把 DeepSeek 官方服务端联网搜索（`web_search_20260209`）原生注入进对话请求，一次请求完成“搜索+作答”，无需外挂工具。需把 DeepSeek 切到 Anthropic 协议，配置示例见文末。  
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
          "id": "deepseek-flash",
          "name": "DS-V4.1-Flash",
          "contextWindow": 1000000,
          "input": ["text", "image"],
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

## DeepSeek 原生联网搜索（Anthropic 协议）
DeepSeek 的服务端搜索工具 `web_search_20260209` **只存在于 Anthropic 兼容端点**；OpenAI 兼容端点会直接报 `unknown variant 'web_search_20260209', expected 'function'`。想要原生搜索（一次请求完成“搜索+作答”，不需要外挂工具），把 DeepSeek 切到 Anthropic 协议：
```
{
  "providers": {
    "deepseek": {
      "apiKey": "你的key",
      "baseUrl": "https://api.deepseek.com/anthropic",
      "models": [
        {
          "id": "deepseek-flash",
          "name": "DS-V4.1-Flash",
          "api": "anthropic-messages",
          "reasoning": true,
          "thinkingLevelMap": { "minimal": null, "low": "low", "medium": null, "high": "high", "max": "max" },
          "input": ["text", "image"],
          "contextWindow": 1000000,
          "maxTokens": 100000,
          "inputLimits": { "images": { "resize": { "maxWidth": 2000, "maxHeight": 2000, "maxBytes": 4718592, "jpegQuality": 80 } } }
        }
      ]
    }
  }
}
```
再配合 `deepseek-search.ts`，用 `before_provider_request` 钩子把 `web_search` 工具注入每次对话请求。

* **`api` 必须写在 model 级**：provider 级的 `api` 不会覆盖内置目录里已有的 model（内置的是 `openai-completions`），协议切不过去。`baseUrl` 写 provider 级即可，会应用到该 provider 下所有 model。
* **model 定义是“整体替换”不是“合并”**：在 models.json 里写了同名 model，内置目录那条就被整个换掉，没写的字段退回通用默认值（`reasoning=false`、`input=["text"]`、`contextWindow=128000`、`maxTokens=16384`）。所以 `reasoning` / `input` / `contextWindow` / `maxTokens` / `thinkingLevelMap` 不是协议要求的，而是为了不让模型能力缩水才必须显式写上。
* **`cost` 可以不写**：只影响界面的费用显示（以及缓存预热的性价比判断，但 DeepSeek 没配 `promptCache`，预热本就不启用）。不写就按 0 显示。
* 图片输入、reasoning、prompt cache 均正常；搜索能力仅对 DeepSeek 生效，其他模型需要搜索时用 `bocha-search.ts`。