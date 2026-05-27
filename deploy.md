# NORVIK SHOP 部署指南

## 方案一：Streamlit Cloud（推荐，最简单）

### 第 1 步：注册 GitHub 账号

1. 打开 https://github.com
2. 点 **Sign up** 注册（免费）
3. 验证邮箱

### 第 2 步：创建 GitHub 仓库

1. 登录 GitHub
2. 点右上角 **+** → **New repository**
3. Repository name: `norvik-shop`
4. 选 **Public**（免费部署必须公开）
5. 点 **Create repository**

### 第 3 步：上传项目文件

**方式 A：网页上传（最简单）**

1. 在仓库页面点 **Add file** → **Upload files**
2. 把以下文件和文件夹拖入：
   ```
   app.py
   config.py
   requirements.txt
   runtime.txt
   .streamlit/          （整个文件夹）
   auth/                （整个文件夹）
   database/            （整个文件夹）
   pages/               （整个文件夹）
   utils/               （整个文件夹）
   data/                （整个文件夹，含 thai_keywords_lexicon.json）
   ```
3. 点 **Commit changes**

**方式 B：Git 命令行**

```bash
cd suho/omni_seo_system
git init
git add app.py config.py requirements.txt runtime.txt .streamlit/ auth/ database/ pages/ utils/ data/
git commit -m "NORVIK SHOP v3.0"
git remote add origin https://github.com/你的用户名/norvik-shop.git
git push -u origin main
```

### 第 4 步：部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io
2. 点 **Continue with GitHub**
3. 点 **Create app**
4. 选择仓库: `你的用户名/norvik-shop`
5. Branch: `main`
6. Main file path: **`app.py`**（如果文件在根目录）或 **`suho/omni_seo_system/app.py`**（如果在子目录）
7. 点 **Deploy!**

等待 1-3 分钟，你会得到一个链接：
```
https://norvik-shop-xxxxx.streamlit.app
```

把这个链接发给团队成员即可使用。

### 第 5 步：查看部署日志

1. 回到 https://share.streamlit.io
2. 点击你的 app
3. 点 **Manage app**（右下角）
4. 查看底部日志输出
5. 如果报错，日志会显示具体文件和行号

### 第 6 步：更新代码

修改代码后，重新推送到 GitHub：

```bash
git add -A
git commit -m "更新说明"
git push
```

Streamlit Cloud 会自动检测并重新部署（约 1-2 分钟）。

### 激活码

系统使用 SHA256 时间算法自动生成激活码，无需手动操作。

获取本周激活码（在本地 Python 终端执行）：

```python
python -c "
import hashlib
from datetime import datetime
now = datetime.now()
y, w, _ = now.isocalendar()
raw = f'{y}-W{w:02d}-NORVIKSHOP'
print(hashlib.sha256(raw.encode()).hexdigest()[:12].upper())
"
```

输出 12 位激活码，有效期 7 天。

---

## 方案二：HuggingFace Spaces

### 第 1 步：注册 HuggingFace

1. 打开 https://huggingface.co
2. 点 **Sign Up**（免费）

### 第 2 步：创建 Space

1. 登录后点右上角头像 → **New Space**
2. Space name: `norvik-shop`
3. SDK: 选 **Streamlit**
4. Visibility: 选 **Public**
5. 点 **Create Space**

### 第 3 步：上传文件

1. 在 Space 页面点 **Files** 标签
2. 点 **Add file** → **Upload files**
3. 上传所有项目文件（同上）
4. 确保 `requirements.txt` 在根目录
5. 点 **Commit changes to main**

HuggingFace 会自动开始构建，约 2-5 分钟。

### 第 4 步：访问

构建完成后，访问：
```
https://huggingface.co/spaces/你的用户名/norvik-shop
```

---

## 常见部署问题

### Q: 部署后白屏

检查：
1. `requirements.txt` 是否在仓库根目录
2. Main file path 是否填对（`app.py` 或 `suho/omni_seo_system/app.py`）
3. 查看部署日志中的错误信息

### Q: 显示 "ModuleNotFoundError"

检查：
1. 所有 `__init__.py` 文件是否都上传了
2. `utils/__init__.py` 是否存在（负责 sys.path 配置）

### Q: 数据库丢失

正常现象。SQLite 存储在云服务器临时磁盘，重启后丢失。
激活码基于时间算法，不依赖数据库，重启后仍然有效。

### Q: 部署很慢

- Streamlit Cloud 首次部署需安装依赖，约 2-3 分钟
- 后续更新约 1-2 分钟
- HuggingFace 首次约 3-5 分钟

### Q: 如何更换激活码盐值

修改 `config.py` 中的 `SECRET_SALT`：
```python
SECRET_SALT = os.environ.get("NORVIK_SECRET", "你的新盐值")
```
推送到 GitHub 后自动生效。

也可以在 Streamlit Cloud 的 **Secrets** 中设置环境变量 `NORVIK_SECRET`。
