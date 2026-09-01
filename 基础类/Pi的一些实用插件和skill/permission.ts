import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import path from "node:path";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash") {
      const command = event.input.command ?? "";

      // 高危命令名单（仅匹配命令名，不解析参数）
      const dangerousCommands = [
        /\brm\b/,       // 删除文件/目录
        /\brmdir\b/,    // 删除空目录
        /\bunlink\b/,   // 删除文件
        /\bshred\b/,    // 安全删除（覆盖后删除）
        /\bdd\b/,       // 磁盘复制（可破坏数据）
        /\bmkfs\b/,     // 格式化文件系统
        /\bfdisk\b/,    // 修改分区表
        /\bparted\b/,   // 修改分区表
        /\bshutdown\b/, // 关机
        /\breboot\b/,   // 重启
        /\bsudo\b/,     // 提权（与危险命令组合时尤其注意）
      ];

      const isDangerous = dangerousCommands.some((pattern) => pattern.test(command));

      if (isDangerous) {
        const ok = await ctx.ui.confirm(
          "⚠️ 高危 Bash 命令",
          command,
        );

        if (!ok) {
          return {
            block: true,
            reason: "用户拒绝了高危命令",
          };
        }
      }
    }
  });
}