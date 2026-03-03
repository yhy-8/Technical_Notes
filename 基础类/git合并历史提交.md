# Git 历史清理指南：合并旧提交并保留最近10次

适用于单人开发项目，使用 JetBrains IDE (IntelliJ/WebStorm/PyCharm) 配合命令行操作。

---

## 第一步：安全备份与分界线定位
在开始任何破坏性操作前，先为当前状态打一个完整备份分支。

```bash
# 1. 创建备份分支
git branch backup-main

# 2. 查看提交历史，找到倒数第 11 个提交的 Hash
git log -n 12 --oneline
```

记下从上往下数第 11 个提交的 `Commit ID (Hash)`。我们将它标记为 `OLD_HASH`。

---

## 第二步：重组本地提交历史
这一步会把 `OLD_HASH` 之前的所有代码合并成一个“孤儿”提交，并接回最近的 10 次记录。

```bash
# 1. 创建并切换到一个全新的“无父辈”临时分支
git checkout --orphan temp-branch <OLD_HASH>

# 2. 将当前暂存区的所有内容提交（这包含了旧历史的所有代码状态）
git add .
git commit -m "清理历史：合并之前的全部提交"

# 3. 使用 Cherry-pick 将原 main 分支最近的 10 个提交接过来
git cherry-pick main~10..main

# 4. 切换回 main 分支，并将其强制指向 temp-branch 的新状态
git checkout main
git reset --hard temp-branch
```

---

## 第三步：解除 IDE 强制推送限制 (GUI)
**IDE 操作路径：**

1. 点击菜单栏 **File (文件)** -> **Settings (设置)** [Mac 为 IntelliJ IDEA -> Settings]。
2. 导航到 **Version Control (版本控制)** -> **Git**。
3. 在右侧找到 **Protected branches (保护的分支)** 列表。
4. 选中列表中的 `main` (或 master)，点击右侧的 **-** 号将其移除。
5. 点击 **OK** 保存设置。

---

## 第四步：强制推送至远程 (GUI + Token)
**注意：由于历史已改变，必须使用“强制推送”，且需要使用 Personal Access Token。**

**GUI 推送细节：**
1. 按 `Ctrl + Shift + K` 打开推送窗口。
2. **关键点：** 点击蓝色“Push”按钮旁边的**下拉箭头 ⌵**。
3. 选择 **Force Push (强制推送)**。

**关于认证失败：**
当弹出用户名密码框时：
* **Username:** 输入你的平台账号。
* **Password:** **不要输登录密码！** 请输入你在 GitHub/Gitee 后台生成的 **Personal Access Token (个人访问令牌)**。

**如果推送弹出“Merge”或“Rebase”提示，请务必关闭，绝不能点合并！必须确保执行的是 Force Push。**

---

## 第五步：善后清理与环境恢复
确认远程代码无误后，清理临时分支并恢复 IDE 设置。

```bash
# 1. 删除临时分支
git branch -D temp-branch

# 2. 如果不需要备份了，也可以删除备份分支
git branch -D backup-main
```

**恢复安全设置：**
回到 **Settings -> Version Control -> Git**，在 **Protected branches** 中点击 **+** 号，重新把 `main` 加回去，防止未来误操作。

---
