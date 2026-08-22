import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import path from "node:path";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    // 1. 高危 Bash 命令确认
    if (event.toolName === "bash") {
      const command = event.input.command ?? "";

      if (/\b(sudo|rm\s+-rf|mkfs|dd\s+if=|shutdown|reboot)\b/.test(command)) {
        const ok = await ctx.ui.confirm(
          "⚠️ 高危 Bash 命令",
          command,
        );

        if (!ok) {
          return { block: true, reason: "用户拒绝了高危命令" };
        }
      }
    }

    // 2. 工作区外文件访问确认
    if (["read", "write", "edit"].includes(event.toolName)) {
      const filePath =
        event.input.path ??
        event.input.file_path ??
        "";

      if (!filePath) return;

      const absolute = path.resolve(ctx.cwd, filePath);
      const workspace = path.resolve(ctx.cwd);

      if (
        absolute !== workspace &&
        !absolute.startsWith(workspace + path.sep)
      ) {
        const ok = await ctx.ui.confirm(
          "⚠️ 工作区外文件访问",
          `${event.toolName}: ${absolute}`,
        );

        if (!ok) {
          return { block: true, reason: "用户拒绝了工作区外文件访问" };
        }
      }
    }
  });
}