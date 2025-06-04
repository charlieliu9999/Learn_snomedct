# 医学影像报告SNOMED CT结构化分析系统

## 项目简介

医学影像报告SNOMED CT结构化分析系统是一个基于大模型技术的医学文本处理平台，能够将自由文本形式的医学影像报告转换为标准化的SNOMED CT表示，并通过可视化技术直观呈现实体关系网络。系统支持各类医学影像报告（CT、MRI、超声、X线等）的分析，能够准确识别医学实体、抽取实体间关系，并映射到SNOMED CT标准术语和编码。

## 主要功能

- **医学影像报告文本输入与处理**：支持输入患者基本信息、检查项目、影像所见和诊断意见
- **基于大模型的SNOMED CT术语解析**：利用OpenAI API进行医学文本的深度语义理解
- **医学实体与关系的识别与编码**：自动识别解剖部位、病理发现、影像学表现等实体及其关系
- **结构化结果的可视化展示**：通过交互式关系图直观呈现实体关系网络
- **历史记录的保存与查询**：保存分析结果，支持历史记录查询和管理

## 系统架构

```
项目结构
medical_report_analyzer/
├── venv/                      # Python虚拟环境
├── src/                       # 源代码目录
│   ├── models/                # 数据模型和分析引擎
│   │   ├── report.py          # 报告数据模型
│   │   ├── snomed_analyzer.py # SNOMED CT分析引擎
│   │   └── user.py            # 用户数据模型
│   ├── routes/                # API路由
│   │   └── report.py          # 报告相关API
│   ├── static/                # 静态资源
│   │   ├── css/               # 样式文件
│   │   ├── js/                # JavaScript文件
│   │   └── index.html         # 主页面
│   └── main.py                # 应用入口
├── requirements.txt           # 依赖包列表
├── research_document.md       # 研究文档
├── solution_plan.md           # 解决方案计划
└── README.md                  # 项目说明文档
```

## 技术栈

- **后端**：Flask, SQLAlchemy, SQLite/MySQL
- **前端**：HTML5, CSS3, JavaScript, Bootstrap 5
- **数据可视化**：D3.js
- **医学术语分析**：OpenAI GPT-4 API
- **部署**：Docker (可选)

## 安装指南

### 系统要求

- Python 3.8+
- pip 包管理器
- 现代化浏览器（Chrome, Firefox, Edge等）
- OpenAI API密钥

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/yourusername/medical_report_analyzer.git
cd medical_report_analyzer
```

2. **创建并激活虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建`.env`文件并添加以下内容：

```
OPENAI_API_KEY=your_openai_api_key_here
FLASK_APP=src/main.py
FLASK_ENV=development
```

替换`your_openai_api_key_here`为您的实际OpenAI API密钥。

5. **初始化数据库**

```bash
python -c "from src.main import db; db.create_all()"
```

6. **启动应用**

```bash
flask run
```

应用将在`http://localhost:5000`上运行。

## 使用指南

### 基本使用流程

1. **访问系统**：打开浏览器，访问`http://localhost:5000`或部署后的URL
2. **输入医学影像报告**：
   - 填写患者年龄、性别
   - 选择检查项目（如"胸部CT"、"脑部MRI"等）
   - 输入影像所见文本
   - 输入诊断意见文本
3. **分析报告**：点击"分析报告"按钮，系统将自动进行SNOMED CT结构化分析
4. **查看结果**：
   - "影像所见分析"标签显示影像所见部分的实体和关系
   - "诊断意见分析"标签显示诊断意见部分的实体和关系
   - "关系可视化"标签显示实体关系图
5. **查看历史记录**：点击导航栏的"历史记录"，可查看和管理之前的分析结果

### 示例输入

**影像所见**：
```
右上肺可见一枚类圆形结节，大小约8mm×7mm，边缘略呈毛刺状，CT值约45HU，较3个月前（6mm×5mm）略有增大。右下肺见一枚磨玻璃样结节，直径约5mm，边界清晰，与3个月前大小无明显变化。
```

**诊断意见**：
```
1. 右上肺结节，考虑恶性可能，建议短期随访或进一步检查。
2. 右下肺磨玻璃样结节，考虑炎性病变可能性大，建议随访观察。
```

## API密钥配置

系统使用OpenAI API进行医学文本的结构化分析，需要配置有效的API密钥。

### 获取API密钥

1. 访问[OpenAI官网](https://openai.com/)并注册账号
2. 导航至API密钥管理页面
3. 创建新的API密钥
4. 复制生成的密钥

### 配置API密钥

有两种方式配置API密钥：

1. **环境变量方式**：
   - 在`.env`文件中设置`OPENAI_API_KEY=your_api_key`
   - 或在系统环境变量中设置`OPENAI_API_KEY`

2. **代码配置方式**：
   - 打开`src/models/snomed_analyzer.py`
   - 找到`self.api_key`初始化部分
   - 替换为您的API密钥

## 部署指南

### 本地部署

按照上述安装步骤在本地部署即可。

### 服务器部署

1. **准备服务器环境**：
   - 安装Python 3.8+
   - 安装必要的系统依赖

2. **克隆并设置项目**：
   - 克隆项目到服务器
   - 创建虚拟环境并安装依赖
   - 配置环境变量

3. **配置生产环境**：
   - 修改`.env`文件，设置`FLASK_ENV=production`
   - 配置数据库连接（可选）

4. **使用Gunicorn运行**：
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 "src.main:app"
   ```

5. **配置Nginx**（可选）：
   - 安装Nginx
   - 配置反向代理到Gunicorn
   - 设置SSL证书

### Docker部署（可选）

1. **创建Dockerfile**：
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   ENV FLASK_APP=src/main.py
   ENV FLASK_ENV=production
   
   EXPOSE 5000
   
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
   ```

2. **构建并运行Docker镜像**：
   ```bash
   docker build -t medical-report-analyzer .
   docker run -p 5000:5000 -e OPENAI_API_KEY=your_api_key medical-report-analyzer
   ```

## 常见问题

### Q: 系统无法连接到OpenAI API

**A**: 检查以下几点：
- 确认API密钥正确配置
- 检查网络连接是否正常
- 验证API密钥是否有效（未过期、有足够额度）

### Q: 分析结果不准确或不完整

**A**: 可能的原因和解决方法：
- 输入文本过于复杂或含有罕见术语，尝试简化描述
- 大模型API调用失败，检查日志并重试
- 提示词模板可能需要优化，可修改`src/models/snomed_analyzer.py`中的提示词

### Q: 关系图不显示或显示异常

**A**: 尝试以下解决方法：
- 确保浏览器支持D3.js（推荐使用Chrome或Firefox最新版本）
- 检查浏览器控制台是否有JavaScript错误
- 验证分析结果中是否包含足够的实体和关系数据

### Q: 数据库操作失败

**A**: 可能的解决方法：
- 检查数据库配置是否正确
- 确认数据库用户有足够权限
- 验证数据库表结构是否正确初始化

## 自定义与扩展

### 修改提示词模板

如需调整SNOMED CT分析的提示词模板，编辑`src/models/snomed_analyzer.py`文件中的`_build_prompt`方法。

### 添加新的实体类型

要支持新的医学实体类型，需要：
1. 修改提示词模板，添加新实体类型的描述
2. 更新前端代码，支持新实体类型的显示
3. 调整可视化模块，为新实体类型添加适当的样式

### 扩展API功能

如需添加新的API端点，可在`src/routes/`目录下创建新的路由文件，并在`src/main.py`中注册。

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请联系项目维护者：

- 邮箱：example@example.com
- GitHub：https://github.com/yourusername

## 致谢

- OpenAI提供的GPT-4 API
- SNOMED International提供的SNOMED CT术语体系
- 所有为本项目做出贡献的开发者和医学专家
