<div align="center">

# ChatKG - 基于知识图谱的大模型问答系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D.svg?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**基于原始文本自动构建知识图谱，结合大模型实现智能问答**

[功能特点](#功能特点) • [快速开始](#快速开始) • [系统架构](#系统架构) • [项目结构](#项目结构) • [配置说明](#配置说明)

</div>

---

## 功能特点

### 核心功能

| 功能 | 说明 |
|------|------|
| **知识图谱构建** | 从原始文本自动抽取实体和关系，构建结构化知识图谱 |
| **图谱迭代补全** | 使用 SPN4RE 模型对种子图谱进行迭代扩展 |
| **智能问答** | 接入 OpenAI 兼容 API（支持 DeepSeek、通义千问、MiMo 等） |
| **NER 实体识别** | 基于 jieba + 图谱实体匹配的轻量级命名实体识别 |
| **知识检索** | 根据用户问题自动检索相关三元组和 Wikipedia 背景知识 |
| **图谱可视化** | 使用 ECharts 实现交互式知识图谱展示 |
| **流式对话** | SSE 流式输出，实时显示回答 |

### 技术特性

- **UIE 抽取** - PaddleNLP 通用信息抽取模型
- **SPN4RE** - 关系三元组联合抽取模型
- **API 模式** - 支持任意 OpenAI 兼容 API，无需本地 GPU
- **懒加载** - 模块按需加载，启动速度快
- **超时控制** - Wikipedia 搜索自动超时，避免阻塞

---

## 系统架构

### 整体流程

```
原始文本 → 数据预处理 → UIE 信息抽取 → 种子图谱 → SPN4RE 训练 → 图谱补全 → 最终图谱
                                                                                        ↓
用户提问 → NER 实体识别 → 图谱三元组检索 → Wikipedia 搜索 → 构建参考资料 → API 大模型生成回答
                                                                                        ↓
                                                                              流式返回前端展示
```

### 模块说明

| 模块 | 路径 | 功能 |
|------|------|------|
| 数据预处理 | `modules/prepare/` | 文本清洗、分句、标准化 |
| UIE 抽取 | `modules/Uie-finetune/` | 基于 PaddleNLP 的信息抽取 |
| SPN4RE | `modules/SPN4RE/` | 关系三元组联合抽取模型 |
| 图谱构建 | `modules/knowledge_graph_builder.py` | 知识图谱构建与迭代 |
| API 服务 | `server/main_api.py` | Flask 后端，集成 NER、图谱、Wikipedia、API |
| 前端界面 | `chat-kg/` | Vue 3 + ECharts 交互界面 |

---

## 快速开始

### 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10+ | 推荐使用 conda 管理 |
| Node.js | 16+ | 前端构建 |
| GPU | 可选 | API 模式无需 GPU |

### 1. 克隆项目

```bash
git clone https://github.com/littlewwwhite/KnowledgeGraph-based-on-Raw-text-A27.git
cd KnowledgeGraph-based-on-Raw-text-A27
```

### 2. 安装后端依赖

```bash
# 创建 conda 环境
conda create -n chatkg python=3.10 -y
conda activate chatkg

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env
```

编辑 `.env` 文件，配置 API 信息：

```bash
# 启用 API 模式
USE_API_MODE=true

# OpenAI 兼容 API 配置
API_BASE_URL=https://api.deepseek.com/v1
API_KEY=your_api_key_here
API_MODEL_NAME=deepseek-chat
```

**支持的 API 提供商：**

| 提供商 | API_BASE_URL | API_MODEL_NAME |
|--------|-------------|----------------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` |
| MiMo | `https://token-plan-cn.xiaomimimo.com/v1` | `mimo-v2.5-pro` |

### 4. 安装前端依赖

```bash
cd chat-kg
npm install
cd ..
```

### 5. 准备知识图谱数据

将构建好的知识图谱数据放到 `server/data/data.json`：

```bash
# 如果使用项目自带的示例数据，跳过此步骤
# 如果自行构建图谱：
python main.py --project my_project --gpu 0
cp data/my_project/iter_vN.json server/data/data.json
```

### 6. 一键启动

```bash
python start.py
```

浏览器将自动打开 http://localhost:5173

---

## 项目结构

```
KnowledgeGraph-based-on-Raw-text-A27/
│
├── start.py                    # 一键启动脚本
├── main.py                     # 图谱构建主入口
├── .env                        # 环境配置（需自行创建）
├── .env.example                # 配置模板
├── requirements.txt            # Python 依赖
├── pytest.ini                  # 测试配置
│
├── server/                     # 后端 API 服务
│   ├── main_api.py             # 主服务器（API 模式）
│   ├── data/
│   │   └── data.json           # 知识图谱数据
│   └── app/
│       └── utils/
│           ├── ner_api.py      # NER 实体识别（jieba）
│           ├── graph_utils.py  # 图谱检索工具
│           ├── query_wiki.py   # Wikipedia 搜索
│           └── image_searcher.py # 图片搜索
│
├── chat-kg/                    # 前端 Vue 3 应用
│   ├── src/
│   │   ├── views/
│   │   │   ├── ChatView.vue    # 聊天页面
│   │   │   ├── GraphView.vue   # 图谱可视化页面
│   │   │   └── HomeView.vue    # 首页
│   │   ├── components/
│   │   │   └── chat/
│   │   │       ├── KnowledgeGraph.vue  # 图谱组件
│   │   │       ├── InfoPanel.vue       # 信息面板
│   │   │       ├── MessageList.vue     # 消息列表
│   │   │       └── MessageInput.vue    # 输入框
│   │   └── router/
│   └── vite.config.js          # Vite 配置（含 API 代理）
│
├── config/                     # 配置管理
│   └── settings.py             # 集中式配置
│
├── modules/                    # 图谱构建模块
│   ├── knowledge_graph_builder.py  # 图谱构建器
│   ├── model_trainer.py        # SPN4RE 训练器
│   ├── prepare/                # 数据预处理
│   ├── SPN4RE/                 # 关系抽取模型
│   ├── Uie-finetune/           # UIE 微调
│   ├── fewshot_model/          # 小样本模型
│   └── utils/                  # 工具函数
│
├── data/                       # 训练数据
│   ├── raw_data/               # 原始文本
│   ├── schema/                 # 关系 Schema 定义
│   └── project_v1/             # 构建结果
│
├── weights/                    # 模型权重（不上传 GitHub）
│   └── model_41_100/           # NER 模型权重
│
├── tests/                      # 测试用例
└── docs/                       # 文档图片
```

---

## API 接口

### 聊天接口

```bash
POST /chat
Content-Type: application/json

{
  "prompt": "舰艇起火后应该如何处理？",
  "history": []
}
```

响应（流式 JSON）：

```json
{
  "history": [["舰艇起火后应该如何处理？", "根据知识图谱信息..."]],
  "updates": {"query": "舰艇起火后应该如何处理？", "response": "根据知识图谱信息..."},
  "image": null,
  "graph": {"nodes": [...], "links": [...], "sents": [...]},
  "wiki": {"title": "损管", "summary": "..."}
}
```

### 图谱接口

```bash
GET /graph          # 获取完整知识图谱
GET /entity/<name>  # 查询实体信息
GET /config         # 获取服务配置
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `USE_API_MODE` | `false` | 是否使用外部 API |
| `API_BASE_URL` | - | API 端点地址 |
| `API_KEY` | - | API 密钥 |
| `API_MODEL_NAME` | - | 模型名称 |
| `SERVER_HOST` | `0.0.0.0` | 服务监听地址 |
| `SERVER_PORT` | `8000` | 服务端口 |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 设备（本地模型用） |

### Schema 配置

系统支持多版本关系 Schema，在 `data/schema/` 目录下定义：

```python
# data/schema/schema_v4.py
schema = {
    "实体类型": ["设备", "人员", "技术", "方法"],
    "关系类型": {
        "设备": ["组成部分", "功能", "位置"],
        "技术": ["应用于", "依赖", "包含"],
    }
}
```

---

## 图谱构建（可选）

如果需要从原始文本构建知识图谱：

### 1. 准备数据

```bash
# 将原始文本放入 data/raw_data/
cp your_data.txt data/raw_data/raw_data.txt
```

### 2. 构建图谱

```bash
# 需要 GPU 环境
python main.py --project my_project --gpu 0

# 从检查点恢复
python main.py --project my_project --resume checkpoint_v3 --gpu 0
```

### 3. 部署图谱

```bash
# 将构建结果复制到服务器数据目录
cp data/my_project/iter_vN.json server/data/data.json
```

---

## 常见问题

### Q: API 调用超时？

A: 检查网络连接和 API 配置。Wikipedia 搜索已有 5 秒超时保护，不会阻塞太久。

### Q: NER 识别不准确？

A: 当前使用 jieba + 图谱实体匹配方案。确保 `server/data/data.json` 中的实体名称准确。

### Q: 前端无法连接后端？

A: 确认后端已启动（`curl http://localhost:8000/`），检查 `chat-kg/.env.local` 中的 `VITE_API_URL` 配置。

### Q: 权重文件怎么获取？

A: `weights/` 目录已加入 `.gitignore`，不会上传到 GitHub。权重文件会在首次运行时自动下载到 `~/.paddlenlp/taskflow/` 目录。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python, Flask, Flask-CORS |
| **前端** | Vue 3, Vite, ECharts, Ant Design Vue |
| **NLP** | PaddleNLP (UIE), jieba, OpenCC |
| **图谱** | SPN4RE, 自定义图谱构建器 |
| **大模型** | OpenAI 兼容 API (DeepSeek/通义千问/MiMo 等) |

---

## 数据来源

| 数据集 | 描述 |
|--------|------|
| 《舰艇损管和潜水技术》 | 初始核心数据 |
| 《舰船损管技术》 | 扩充数据集 |

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## License

本项目采用 MIT 许可证

---

<div align="center">

**如果这个项目对你有帮助，请给一个 Star**

Made by [littlewwwhite](https://github.com/littlewwwhite)

</div>
