[根目录](../CLAUDE.md) > **session_diary**

# session_diary 模块

> Claude Code Session Diary 核心插件包

## 模块职责

提供轻量级的会话日记功能，包括：
- Stop Hook：自动保存会话摘要到 Markdown 文件
- SessionStart Hook：自动注入历史记忆到系统提示词
- 安装配置工具：一键配置 Claude Code hooks

## 入口与启动

### 命令行入口

```bash
# Stop Hook（Claude Code 自动调用）
session-diary-save-hook

# SessionStart Hook（Claude Code 自动调用）
session-diary-sessionstart-hook

# 安装配置工具（用户手动执行）
session-diary-install
```

### 入口文件

- `save_hook.py:main()` - Stop Hook 入口，读取 stdin JSON，输出决策
- `sessionstart_hook.py:main()` - SessionStart Hook 入口，输出记忆注入
- `installer.py:main()` - 安装工具入口，自动配置 settings.json

### 调用流程

**Stop Hook 流程**：
```
Claude Code → stdin JSON → save_hook.main()
  → count_human_messages() 消息计数
  → HookState 读取状态
  → 双重条件判断（消息数 + 时间间隔）
  → 触发保存：
      → extract_summary_section() 提取历史摘要
      → generate_current_entry() 生成当前条目
      → accumulate_and_trim_summary() 增量累积
      → write_diary_file() 写入 Markdown
  → stdout JSON 决策（block 或空）
```

**SessionStart Hook 流程**：
```
Claude Code → sessionstart_hook.main()
  → load_diary_dir() 加载日记目录
  → find_latest_diary() 查找最新日记
  → extract_summary_section() 提取历史摘要
  → extract_recent_progress() 提取最近进展
  → stdout 输出格式化记忆注入
```

## 对外接口

### 公开 API

#### save_hook 模块

```python
def main():
    """Stop Hook 主入口

    输入（stdin JSON）：
    {
        "session_id": "...",
        "stop_hook_active": false,
        "transcript_path": "..."
    }

    输出（stdout JSON）：
    - {} - 不触发保存，正常停止
    - {"decision": "block", "reason": "..."} - 阻止并提示执行 /save-session-auto
    """
```

#### sessionstart_hook 模块

```python
def main():
    """SessionStart Hook 主入口

    输出（stdout）：
    格式化的记忆注入文本，包含：
    - 历史任务摘要
    - 最近进展
    - 注入统计
    """
```

#### installer 模块

```python
def main():
    """自动配置 Claude Code settings.json

    功能：
    1. 查找 settings.local.json 或 settings.json
    2. 检查 hooks 是否已配置
    3. 添加 Stop 和 SessionStart hooks
    """
```

#### extractor 模块

```python
def extract_summary_section(diary_path: Path) -> str:
    """提取日记中的历史任务摘要部分"""

def generate_current_entry(diary_path: Path, timestamp: str) -> str:
    """生成当前会话摘要条目"""

def accumulate_and_trim_summary(old_summary: str, new_entry: str) -> str:
    """增量累积摘要并裁剪（30KB 限制）"""
```

#### counter 模块

```python
def count_human_messages(transcript_path: Path) -> int:
    """计数 JSONL transcript 中的人类消息（排除命令消息）"""
```

#### state 模块

```python
class HookState:
    """Hook 状态管理

    属性：
    - session_id: 会话 ID
    - last_save: 上次保存时的消息计数
    - last_save_timestamp: 上次保存时间戳
    """

    def save(self):
        """保存状态到 JSON 文件"""

    def log(self, message: str):
        """追加日志到 hook.log"""
```

#### config 模块

```python
# 配置常量
SAVE_INTERVAL: int           # 保存间隔（消息数）
MIN_SAVE_INTERVAL_MINUTES: int  # 最小时间间隔（分钟）
STATE_DIR: Path              # 状态目录
DIARY_DIR: Path              # 日记目录
VERBOSE_MODE: bool           # 详细模式
MAX_SUMMARY_SIZE: int        # 摘要大小限制（30KB）
MAX_SUMMARY_ENTRIES: int     # 最大条目数（6）
```

## 关键依赖与配置

### 依赖关系

```python
# 外部依赖（仅标准库）
json          # JSON 解析
sys           # stdin/stdout
pathlib       # 路径操作
datetime      # 时间处理
os            # 环境变量

# 内部依赖关系
save_hook
  ├── counter (消息计数)
  ├── extractor (摘要提取)
  ├── state (状态管理)
  └── config (配置管理)

sessionstart_hook
  ├── extractor (摘要提取)
  ├── state (状态管理)
  └── config (配置管理)

installer
  └── (无内部依赖)
```

### 配置优先级

1. **环境变量**：最高优先级
   - `SESSION_DIARY_SAVE_INTERVAL`
   - `SESSION_DIARY_MIN_INTERVAL`
   - `SESSION_DIARY_MEMORY_DIR`
   - `SESSION_DIARY_STATE_DIR`
   - `SESSION_DIARY_VERBOSE`

2. **settings.local.json**：次优先级
   ```json
   {
     "sessionDiary": {"directory": ".session-memory"}
   }
   ```
   或
   ```json
   {
     "sessionDiaryDirectory": ".session-memory"
   }
   ```

3. **默认值**：最低优先级
   - `SAVE_INTERVAL = 15`
   - `MIN_SAVE_INTERVAL_MINUTES = 30`
   - `DIARY_DIR = <project_root>/.session-memory`

### 配置解析策略

```python
# config.py:_find_project_root()
1. 尝试解码 Claude Code 包装目录（~/.claude/projects/-path-to-project/）
2. 向上查找 .git 目录
3. 向上查找项目标记文件（pyproject.toml, package.json 等）
4. 回退到当前目录
```

## 数据模型

### 日记文件格式

**文件命名**：`.session-diary-YYYY-MM-DD-HHMM.md`

**Markdown 结构**：
```
# Session Diary - YYYY-MM-DD HH:MM

## 历史任务摘要（截止本次会话）

### YYYY-MM-DD HH:MM Task Title
- **成果：** Outcome 1, Outcome 2, ...
- **决策：** Decision 1, Decision 2, ...

---

## 本次进展

### Task Title
Progress content...

## 关键发现

- Finding 1
- Finding 2

## 关键决策

**决策 1: Decision Title**
- Reason

**决策 2: Decision Title**
- Reason
```

### 状态文件格式

**文件位置**：`~/.session-diary/hook_state/<session_id>_state.json`

**JSON 格式**：
```json
{
  "last_save_count": 15,
  "last_save_timestamp": "2026-05-05T10:30:00"
}
```

**遗留格式兼容**：
- `<session_id>_last_save.txt`：纯数字格式（向后兼容）

### Transcript 格式

**文件格式**：JSONL（每行一个 JSON 对象）

**消息结构**：
```json
{
  "message": {
    "role": "user",
    "content": "..."
  }
}
```

**过滤规则**：
- 仅计数 `role == "user"` 的消息
- 排除包含 `<command-message>` 的命令消息

## 测试与质量

### 测试文件

- `test_save_hook.py` - Stop Hook 测试
  - 消息计数触发条件
  - 时间间隔阻塞条件
  - 状态持久化
  - 无限循环防护

- `test_sessionstart_hook.py` - SessionStart Hook 测试
  - 新格式 diary 提取
  - 旧格式兼容
  - 日记缺失降级
  - Token 估算

- `test_extractor.py` - 摘要提取测试
  - 各种 diary 格式解析
  - 边缘情况处理
  - 大小裁剪逻辑

- `test_counter.py` - 消息计数测试
  - JSONL 解析
  - 命令消息过滤
  - 错误处理

- `test_state.py` - 状态管理测试
  - JSON 格式读写
  - 遗留格式迁移
  - 日志记录

- `test_config.py` - 配置管理测试
  - 环境变量覆盖
  - settings.local.json 解析
  - 路径解析策略

- `test_installer.py` - 安装工具测试
  - 配置文件查找
  - Hooks 自动配置
  - 重复配置检测

### 测试覆盖率

**当前覆盖率**：> 80%（目标）

**关键覆盖点**：
- ✅ 双重触发条件（消息数 + 时间间隔）
- ✅ 向后兼容（新旧 diary 格式）
- ✅ 错误降级（文件缺失、格式错误）
- ✅ 大小控制（30KB 裁剪）
- ✅ 路径解析（多种项目根定位策略）

### 质量工具

```bash
# 运行测试并生成覆盖率报告
pytest --cov=session_diary --cov-report=term-missing

# 覆盖率要求
# pyproject.toml: fail_under = 80
```

## 常见问题 (FAQ)

### Q1: Stop Hook 没有触发保存？

**排查步骤**：
1. 检查 `~/.session-diary/hook_state/hook.log` 日志
2. 确认消息数是否达到 `SAVE_INTERVAL`（默认 15）
3. 确认时间间隔是否满足 `MIN_SAVE_INTERVAL_MINUTES`（默认 30 分钟）
4. 验证环境变量配置是否正确

### Q2: SessionStart Hook 注入失败？

**可能原因**：
1. Diary 目录不存在或为空
2. Diary 文件格式不正确
3. 状态文件损坏

**解决方法**：
- 检查 `SESSION_DIARY_MEMORY_DIR` 环境变量
- 验证 `.session-memory/` 目录权限
- 清除状态文件重新测试

### Q3: 如何调试 Hook？

```bash
# 启用详细模式
export SESSION_DIARY_VERBOSE=true

# 手动测试 Stop Hook
echo '{"session_id":"test","stop_hook_active":false,"transcript_path":"/tmp/test.jsonl"}' | session-diary-save-hook

# 手动测试 SessionStart Hook
session-diary-sessionstart-hook

# 查看日志
cat ~/.session-diary/hook_state/hook.log
```

### Q4: 如何自定义 Diary 目录？

**方法 1：环境变量**
```bash
export SESSION_DIARY_MEMORY_DIR=/path/to/custom/diary
```

**方法 2：settings.local.json**
```json
{
  "sessionDiary": {
    "directory": ".custom-memory"
  }
}
```

### Q5: 为什么要双重触发条件？

避免过于频繁的保存：
- 消息数条件：确保足够的对话内容
- 时间条件：避免短时间内多次保存

两个条件同时满足才触发，实现智能节流。

## 相关文件清单

### 核心文件

- `save_hook.py` - Stop Hook 主逻辑（200 行）
- `sessionstart_hook.py` - SessionStart Hook 主逻辑（184 行）
- `extractor.py` - 摘要提取与生成（273 行）
- `config.py` - 配置管理与路径解析（200 行）
- `state.py` - Hook 状态持久化（104 行）
- `counter.py` - JSONL 消息计数（45 行）
- `installer.py` - 自动配置工具（169 行）
- `__init__.py` - 包元数据（8 行）

### 数据文件

- `.session-memory/.session-diary-*.md` - 会话日记文件
- `~/.session-diary/hook_state/<session_id>_state.json` - Hook 状态
- `~/.session-diary/hook_state/hook.log` - Hook 日志
- `~/.session-diary/hook_state/last_diary_dir.txt` - 全局日记目录记录

### 配置文件

- `pyproject.toml` - 项目配置与依赖
- `.claude/settings.local.json` - Claude Code 配置（用户自定义）

## 变更记录 (Changelog)

### 2026-05-05 - 初始化模块文档

- 创建模块级 CLAUDE.md
- 完整记录模块职责、接口、依赖、数据模型
- 添加测试策略与常见问题