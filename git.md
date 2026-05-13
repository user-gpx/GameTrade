## Git命令大全（含功能注释和使用方法）

### 一、项目初始化阶段

#### 1.1 成员C：创建基础框架并上传

```bash
# -------------------- 首次创建项目 --------------------

# 初始化git仓库（在当前目录创建.git文件夹）
git init

# 查看文件状态（红色表示未跟踪，绿色表示已暂存）
git status

# 添加所有文件到暂存区
git add .
# 或者添加指定文件
git add README.md
git add config/settings.py

# 提交到本地仓库（-m后面是提交信息）
git commit -m "Initial commit: 创建Django项目基础结构"

# 添加远程仓库地址（origin是远程仓库的默认名称）
git remote add origin https://github.com/你的用户名/game_trade.git

# 查看远程仓库
git remote -v

# 推送到远程仓库（-u建立追踪关系，以后可以直接用git push）
git push -u origin main

# 创建dev开发分支并切换
git checkout -b dev

# 推送dev分支到远程
git push -u origin dev
```

#### 1.2 成员A/B：克隆项目

```bash
# -------------------- 首次克隆项目 --------------------

# 克隆远程仓库到本地
git clone https://github.com/用户名/game_trade.git

# 进入项目目录
cd game_trade

# 查看所有分支（包括远程）
git branch -a

# 切换到dev分支
git checkout dev

# 从远程更新所有分支信息
git fetch --all
```

### 二、日常开发流程

#### 2.1 每天开始工作

```bash
# -------------------- 开始一天的工作 --------------------

# 查看当前分支（确保在自己分支上）
git branch

# 切换到dev分支获取最新代码
git checkout dev

# 拉取最新代码（等于git fetch + git merge）
git pull origin dev

# 切换回自己的功能分支
git checkout feature/auth

# 将dev的新代码合并到自己的分支
git merge dev

# 如果合并时有冲突，解决冲突后
git add .
git commit -m "merge: 合并dev分支更新"
```

#### 2.2 开发中常用命令

```bash
# -------------------- 开发过程中的操作 --------------------

# 查看当前修改的文件
git status

# 查看具体修改了哪些内容
git diff

# 查看指定文件的修改
git diff apps/users/models.py

# 添加单个文件到暂存区
git add apps/users/models.py

# 添加多个文件
git add apps/users/views.py apps/users/urls.py

# 添加所有修改（包括删除）
git add -A

# 添加当前目录所有修改（不包括上层）
git add .

# 提交修改（-m后面写清晰的提交信息）
git commit -m "feat: 完成用户注册功能"

# 如果提交信息写错了，修改最后一次提交
git commit --amend -m "feat: 完成用户注册和登录功能"

# 推送到远程自己的分支
git push origin feature/auth

# 如果推送被拒绝（远程有更新），先拉取再推送
git pull origin feature-auth
git push origin feature-auth
```

#### 2.3 分支操作

```bash
# -------------------- 分支管理 --------------------

# 查看所有本地分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 创建新分支（基于当前分支）
git branch feature/payment

# 切换分支
git checkout feature/payment

# 创建并切换分支（一步完成）
git checkout -b feature/payment

# 删除本地分支（必须不在要删除的分支上）
git branch -d feature/old-branch

# 强制删除未合并的分支
git branch -D feature/abandoned

# 删除远程分支
git push origin --delete feature/old-branch

# 重命名分支
git branch -m old-name new-name
```

### 三、解决冲突

#### 3.1 合并时遇到冲突

```bash
# -------------------- 解决合并冲突 --------------------

# 当合并时出现冲突
git merge dev
# 输出：CONFLICT in apps/users/models.py

# 查看冲突文件
git status
# 显示：both modified: apps/users/models.py

# 打开冲突文件，会看到：
<<<<<<< HEAD
# 你的代码
=======
# 别人的代码
>>>>>>> dev

# 手动编辑文件，删除冲突标记，保留正确代码

# 解决完冲突后，标记为已解决
git add apps/users/models.py

# 继续合并
git commit -m "merge: 解决users/models.py冲突"

# 推送到远程
git push origin feature/auth
```

#### 3.2 暂存当前工作

```bash
# -------------------- 临时保存工作（重要！） --------------------

# 当你需要切换分支，但不想提交当前修改时
git stash
# 这会暂存所有未提交的修改，工作区变干净

# 查看暂存列表
git stash list

# 恢复最近的暂存
git stash pop

# 恢复指定暂存
git stash apply stash@{0}

# 删除最近的暂存
git stash drop

# 暂存并添加说明
git stash save "正在开发登录功能，未完成"
```

### 四、撤销和回退

```bash
# -------------------- 撤销操作（小心使用） --------------------

# 撤销工作区的修改（未git add）
git checkout -- filename.py

# 撤销所有工作区修改
git checkout -- .

# 从暂存区撤出（文件保留修改）
git reset HEAD filename.py

# 撤销最近一次提交（保留修改）
git reset --soft HEAD^

# 撤销最近一次提交（不保留修改）
git reset --hard HEAD^

# 撤销最近3次提交
git reset --hard HEAD~3

# 查看操作历史（可用于找回丢失的提交）
git reflog

# 回退到指定版本（通过reflog找到的hash值）
git reset --hard 7f3d5a2
```

### 五、查看历史和日志

```bash
# -------------------- 查看历史 --------------------

# 查看提交历史
git log

# 查看简洁的历史（一行显示）
git log --oneline

# 查看图形化历史
git log --graph --oneline --decorate

# 查看指定文件的修改历史
git log -p filename.py

# 查看谁修改了文件（责任追究）
git blame filename.py

# 查看当前分支的详细状态
git show
```

### 六、与远程仓库交互

```bash
# -------------------- 远程操作 --------------------

# 查看远程仓库
git remote -v

# 添加新的远程仓库
git remote add upstream https://github.com/原项目地址.git

# 从远程获取更新（不自动合并）
git fetch origin

# 从远程获取并合并
git pull origin dev

# 推送代码到远程
git push origin feature/auth

# 强制推送（危险！会覆盖远程）
git push -f origin feature/auth

# 设置上游分支（以后可以直接git push）
git push -u origin feature/auth
```

### 七、团队协作专用命令

#### 7.1 创建Pull Request前的准备

```bash
# -------------------- 准备合并到dev --------------------

# 确保在自己的功能分支上
git branch

# 先切换到dev拉取最新代码
git checkout dev
git pull origin dev

# 回到功能分支
git checkout feature/auth

# 将dev的最新代码合并进来
git merge dev

# 如果有冲突，解决冲突并提交

# 运行测试确保功能正常
python manage.py test

# 最后推送
git push origin feature/auth
```

#### 7.2 代码审查后

```bash
# -------------------- 审查反馈修改 --------------------

# 根据审查意见修改代码
git add .
git commit -m "fix: 根据review意见修改代码"

# 推送到同一分支（PR会自动更新）
git push origin feature/auth

# 如果审查通过，在GitHub网页上点击Merge
```

#### 7.3 合并完成后清理

```bash
# -------------------- 清理工作 --------------------

# 切换到dev分支
git checkout dev

# 拉取最新代码（包含刚才合并的）
git pull origin dev

# 删除本地功能分支
git branch -d feature/auth

# 删除远程功能分支
git push origin --delete feature/auth

# 查看本地分支，确认已删除
git branch
```

### 八、实用技巧和快捷键

#### 8.1 配置别名（简化命令）

```bash
# -------------------- 设置别名 --------------------

# 设置常用命令的简写
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"

# 现在可以用简写
git st        # 代替 git status
git co dev    # 代替 git checkout dev
git br        # 代替 git branch
git ci -m "msg" # 代替 git commit -m
git lg        # 查看漂亮的日志
```

#### 8.2 常用组合命令

```bash
# -------------------- 日常开发标准流程 --------------------

# 早上开始工作
git checkout dev && git pull && git checkout -b feature/new

# 下班前提交
git add . && git commit -m "update" && git push origin feature/new

# 查看今天的提交
git log --since="today" --oneline

# 查看自己的提交
git log --author="你的名字" --oneline
```

### 九、紧急情况处理

```bash
# -------------------- 救命命令 --------------------

# 不小心删了文件，还没提交
git checkout -- 被删的文件

# 提交错了，想撤回但保留代码
git reset --soft HEAD^

# 彻底回退到某个版本（丢失之后的所有修改）
git reset --hard 版本号

# 误操作后找回来
git reflog  # 找到操作前的版本号
git reset --hard 那个版本号

# 想放弃所有本地修改，完全同步远程
git fetch origin
git reset --hard origin/dev
```

### 十、提交信息规范

```bash
# -------------------- 提交信息示例 --------------------

# 新功能
git commit -m "feat: 添加用户注册功能"

# 修复bug
git commit -m "fix: 修复登录验证码不显示的问题"

# 文档更新
git commit -m "docs: 更新README部署说明"

# 样式修改
git commit -m "style: 格式化代码，符合PEP8"

# 重构
git commit -m "refactor: 重构订单状态机逻辑"

# 测试相关
git commit -m "test: 添加订单模型单元测试"

# 性能优化
git commit -m "perf: 优化道具列表查询速度"
```

### 十一、最常用的命令速查表

| 场景       | 命令                          | 说明                |
| ---------- | ----------------------------- | ------------------- |
| 开始新功能 | `git checkout -b feature/xxx` | 创建并切换到新分支  |
| 查看修改   | `git status`                  | 查看哪些文件改了    |
| 添加文件   | `git add .`                   | 添加所有修改        |
| 提交       | `git commit -m "信息"`        | 提交到本地          |
| 推送       | `git push origin 分支名`      | 推送到远程          |
| 更新代码   | `git pull origin dev`         | 拉取最新代码        |
| 合并分支   | `git merge dev`               | 把dev合并到当前分支 |
| 暂存修改   | `git stash`                   | 临时保存修改        |
| 恢复暂存   | `git stash pop`               | 恢复最近暂存        |

记住：**遇到不确定的情况，先用 `git status` 查看状态，再用 `git log` 查看历史，最后才执行修改命令！**