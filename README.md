# 招标投标规范智能审核系统

基于AI大模型的招标投标规范智能审核系统

## 🚀 项目状态

**当前版本**: v1.0.0  
**开发阶段**: Week 1 - 项目基础搭建  
**服务状态**: ✅ 运行中 (http://127.0.0.1:8090)

## 📋 Week 1 完成情况

### ✅ 已完成任务
- [x] 环境准备：Python 3.10虚拟环境搭建
- [x] 项目结构：FastAPI项目骨架创建
- [x] 配置管理：环境配置和设置管理
- [x] API基础框架：路由、中间件、异常处理
- [x] 基础API端点：健康检查、文档管理接口
- [x] 依赖管理：核心包安装，兼容性问题修复
- [x] 端口配置：使用8090端口避免冲突

### ⚠️ 临时禁用组件
- PostgreSQL：等待数据库配置
- MongoDB：Motor兼容性问题待解决
- Neo4j：等待图数据库配置

### 🔄 进行中任务
- 数据库设计和配置

## 🛠️ 技术栈

### 核心框架
- **Backend**: FastAPI + Python 3.10
- **API Server**: Uvicorn
- **配置管理**: Pydantic Settings

### 数据库（规划中）
- **关系数据库**: PostgreSQL 
- **图数据库**: Neo4j
- **文档数据库**: MongoDB
- **缓存**: Redis

### AI & NLP（待集成）
- **大语言模型**: DeepSeek API
- **文档解析**: TextIn API
- **向量数据库**: FAISS

## 🚦 启动方式

```bash
# 激活虚拟环境
source zaobiao_env/bin/activate

# 启动开发服务器
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```

## 📡 API端点

### 系统监控
- `GET /` - 根路径信息
- `GET /health` - 健康检查
- `GET /api/v1/health/` - 详细健康检查

### 文档管理
- `GET /api/v1/documents/` - 获取文档列表
- `GET /api/v1/documents/{id}` - 获取文档详情
- `POST /api/v1/documents/upload` - 上传文档
- `POST /api/v1/documents/{id}/parse` - 解析文档
- `DELETE /api/v1/documents/{id}` - 删除文档

### API文档
- `GET /docs` - Swagger UI (开发环境)
- `GET /redoc` - ReDoc (开发环境)

## 🔧 开发环境

```bash
# Python版本
Python 3.10.17

# 主要依赖
fastapi==0.104.1
uvicorn==0.24.0
pydantic-settings==2.0.3
sqlalchemy==2.0.23
```

## 📁 项目结构

```
zaobiaoshenhe/
├── app/                    # 应用主目录
│   ├── api/               # API接口
│   │   └── endpoints/     # 具体端点实现
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   ├── database.py    # 数据库连接
│   │   └── logging.py     # 日志配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   ├── utils/             # 工具函数
│   └── main.py            # 应用入口
├── base/                  # 基础数据
│   └── biaozun.md         # 招标规范文档
├── config/                # 配置文件
├── docs/                  # 文档目录
├── tests/                 # 测试文件
├── zaobiao_env/          # 虚拟环境
├── requirements.txt       # Python依赖
├── pyproject.toml        # 项目配置
├── env.example           # 环境变量模板
└── README.md             # 项目说明
```

## 🎯 下一步计划

### Week 1 剩余任务
- [ ] 数据库设计：PostgreSQL模型设计
- [ ] 数据库连接：配置和测试数据库连接
- [ ] 数据迁移：Alembic迁移脚本

### Week 2 规划
- [ ] 微服务架构搭建
- [ ] 外部API集成（DeepSeek、TextIn）
- [ ] 知识图谱基础模块

## 📝 开发日志

### 2025-09-21
- ✅ 创建Python 3.10虚拟环境
- ✅ 安装核心依赖包
- ✅ 实现FastAPI基础框架
- ✅ 配置8090端口避免冲突
- ✅ 实现健康检查和文档管理API
- ⚠️ 临时禁用MongoDB（Motor兼容性问题）
- ⚠️ 临时禁用PostgreSQL（等待数据库配置）

---

**开发团队**: AI助手 + 荣哥  
**最后更新**: 2025-09-21
