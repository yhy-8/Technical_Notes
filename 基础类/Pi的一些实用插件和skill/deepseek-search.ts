import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// DeepSeek 官方联网搜索是服务端工具，只在 Anthropic 兼容协议里存在
// （tool 类型 web_search_20260209）。这里把它注入进 deepseek 的每一次对话请求，
// 让搜索在模型服务端原生完成：一次请求 = 搜索 + 作答，没有额外工具往返。
//
// 覆盖范围仅限主对话循环：pi 的压缩/摘要/缓存预热等内部请求不经过
// before_provider_request，因此不会被注入、也不会误触发搜索。
//
// 注意：只有走 anthropic-messages 的模型才注入；OpenAI 兼容端点不认这个工具。
const SEARCH_TOOL = {
  type: "web_search_20260209",
  name: "web_search",
  max_uses: 10,
  allowed_callers: ["direct"],
};

export default function (pi: ExtensionAPI) {
  pi.on("before_provider_request", (event, ctx) => {
    if (ctx.model?.provider !== "deepseek") return;
    if (ctx.model.api !== "anthropic-messages") return;

    const payload = event.payload as { tools?: unknown[] } | undefined;
    if (!payload || !Array.isArray(payload.tools)) return;

    payload.tools = [...payload.tools, SEARCH_TOOL];
    return payload;
  });
}
