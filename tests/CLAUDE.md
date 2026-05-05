[根目录](../CLAUDE.md) > **tests**

# tests 模块

> Session Diary Plugin 单元测试套件

## 模块职责

提供完整的单元测试覆盖，确保核心功能的正确性和稳定性。

## 入口与启动

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_save_hook.py

# 运行特定测试函数
pytest tests/test_extractor.py::test_extract_summary_section_new_format

# 查看覆盖率
pytest --cov=session_diary --cov-report=term-missing

# 详细输出
pytest -v
```

### 测试配置

**pyproject.toml**：
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=session_diary --cov-report=term-missing"

[tool.coverage.run]
source = ["session_diary"]
omit = ["tests/*"]

[tool.coverage.report]
fail_under = 80
```

## 对外接口

### 测试夹具（conftest.py）

提供共享测试数据，供所有测试文件使用：

```python
@pytest.fixture
def sample_transcript():
    """示例 JSONL transcript（6 条用户消息，排除 1 条命令消息）"""

@pytest.fixture
def empty_transcript():
    """空 JSONL transcript"""

@pytest.fixture
def malformed_transcript():
    """格式错误的 JSONL transcript"""

@pytest.fixture
def sample_diary_new_format():
    """新格式 diary（包含历史任务摘要）"""

@pytest.fixture
def sample_diary_old_format():
    """旧格式 diary（无摘要）"""

@pytest.fixture
def sample_diary_no_end_marker():
    """无结束标记的 diary"""

@pytest.fixture
def sample_diary_trailing_separator():
    """末尾 --- 的 diary（边缘情况）"""

@pytest.fixture
def sample_diary_progress_last_section():
    """本次进展为最后一个 section 的 diary"""

@pytest.fixture
def sample_diary_no_task_title():
    """无任务标题的 diary"""

@pytest.fixture
def sample_diary_many_findings():
    """多个发现和决策的 diary"""

@pytest.fixture
def sample_diary_discoveries_last_section():
    """关键发现为最后一个 section 的 diary"""

@pytest.fixture
def sample_diary_decisions_last_section():
    """关键决策为最后一个 section 的 diary"""

@pytest.fixture
def sample_diary_title_no_trailing_newline():
    """标题在文件末尾无换行的 diary"""
```

## 关键依赖与配置

### 测试依赖

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

### 测试策略

1. **单元测试**：每个模块独立测试
2. **集成测试**：完整的 hook 流程测试
3. **边缘情况**：错误处理、格式兼容性
4. **向后兼容**：新旧 diary 格式支持

## 数据模型

### 测试数据结构

**Transcript 测试数据**：
- 正常消息（user + assistant）
- 命令消息（`<command-message>`）
- 空文件
- 格式错误文件

**Diary 测试数据**：
- 新格式（包含历史任务摘要）
- 旧格式（无摘要）
- 边缘情况（无结束标记、末尾 ---、section 缺失等）

## 测试与质量

### 测试文件清单

- **test_save_hook.py**（200 行）
  - `test_read_stdin_json_invalid` - 无效 JSON 输入
  - `test_output_block_with_agent_trigger` - Block 决策输出
  - `test_find_latest_diary` - 查找最新 diary
  - `test_process_summary_no_diary` - 无 diary 时的处理
  - `test_save_hook_empty_json` - 空 JSON 输入
  - `test_save_hook_stop_hook_active` - 无限循环防护
  - `test_save_hook_triggers_save` - 触发保存条件
  - `test_save_hook_time_interval_blocks_save` - 时间间隔阻塞

- **test_sessionstart_hook.py**（247 行）
  - `test_find_latest_diary_basic` - 查找最新 diary
  - `test_extract_recent_progress` - 提取最近进展
  - `test_estimate_tokens` - Token 估算
  - `test_output_no_diary_fallback` - 无 diary 降级
  - `test_output_new_format` - 新格式输出
  - `test_output_old_format` - 旧格式输出

- **test_extractor.py**（185 行）
  - `test_extract_summary_section_*` - 各种格式摘要提取
  - `test_extract_first_task_title_*` - 任务标题提取
  - `test_extract_outcomes_*` - 成果提取
  - `test_extract_decisions_*` - 决策提取
  - `test_generate_current_entry_*` - 当前条目生成
  - `test_accumulate_and_trim_summary_*` - 增量累积与裁剪

- **test_counter.py**（待补充）
  - `test_count_human_messages` - 正常消息计数
  - `test_count_command_messages` - 命令消息过滤
  - `test_count_empty_transcript` - 空 transcript
  - `test_count_malformed_json` - 格式错误处理

- **test_state.py**（105 行）
  - `test_save_and_load_diary_dir` - 全局状态读写
  - `test_hook_state_init` - 状态初始化
  - `test_hook_state_save_and_read` - JSON 格式持久化
  - `test_hook_state_log` - 日志记录
  - `test_hook_state_legacy_format_migration` - 遗留格式迁移

- **test_config.py**（211 行）
  - `test_default_*` - 默认配置值
  - `test_env_override_*` - 环境变量覆盖
  - `test_find_settings_file` - 配置文件查找
  - `test_get_diary_dir_from_settings` - 日记目录配置

- **test_installer.py**（196 行）
  - `test_find_settings_json_*` - 配置文件查找
  - `test_read_settings_*` - 配置读取
  - `test_write_settings` - 配置写入
  - `test_hooks_already_configured` - 重复配置检测
  - `test_add_hooks` - Hooks 添加
  - `test_main_*` - 主流程测试

### 覆盖率报告

**目标**：>= 80%

**关键覆盖点**：
- ✅ 双重触发条件（消息数 + 时间间隔）
- ✅ 向后兼容（新旧 diary 格式、遗留状态格式）
- ✅ 错误降级（文件缺失、格式错误）
- ✅ 大小控制（30KB 裁剪）
- ✅ 路径解析（多种项目根定位策略）
- ✅ 边缘情况（空文件、无结束标记、末尾 --- 等）

## 常见问题 (FAQ)

### Q1: 测试失败如何调试？

```bash
# 运行单个测试并显示打印输出
pytest -s tests/test_save_hook.py::test_save_hook_triggers_save

# 运行并进入调试器
pytest --pdb tests/test_save_hook.py

# 查看详细错误信息
pytest -v --tb=long tests/test_save_hook.py
```

### Q2: 如何添加新测试？

1. 在 `tests/test_*.py` 中添加测试函数
2. 使用 `conftest.py` 中的 fixture 或创建新 fixture
3. 确保测试覆盖率不降低
4. 运行 `pytest --cov=session_diary --cov-report=term-missing`

### Q3: 如何测试环境变量配置？

```python
import os
import importlib
from session_diary import config

def test_env_override():
    os.environ['SESSION_DIARY_SAVE_INTERVAL'] = '10'
    importlib.reload(config)
    assert config.SAVE_INTERVAL == 10
    del os.environ['SESSION_DIARY_SAVE_INTERVAL']
    importlib.reload(config)
```

### Q4: 如何测试文件系统操作？

使用 `tempfile.TemporaryDirectory` 创建临时目录：

```python
import tempfile
from pathlib import Path

def test_file_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("content")
        assert test_file.read_text() == "content"
```

## 相关文件清单

### 测试文件

- `conftest.py` - 共享测试夹具（304 行）
- `test_save_hook.py` - Stop Hook 测试（200 行）
- `test_sessionstart_hook.py` - SessionStart Hook 测试（247 行）
- `test_extractor.py` - 摘要提取测试（185 行）
- `test_state.py` - 状态管理测试（105 行）
- `test_config.py` - 配置管理测试（211 行）
- `test_installer.py` - 安装工具测试（196 行）

### 测试数据

- `sample_transcript` - JSONL transcript 样例
- `sample_diary_*` - 各种 diary 格式样例

## 变更记录 (Changelog)

### 2026-05-05 - 初始化测试文档

- 创建 tests 模块文档
- 完整记录测试策略、夹具、覆盖率
- 添加测试运行与调试指南