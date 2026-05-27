# NORVIK SHOP AI OPERATING SYSTEM

企业级跨境电商 AI 运营工具平台

## 功能

- 多平台 SEO 爆款标题生成（Shopee / Lazada / TikTok / Temu / Amazon / 淘宝 / 拼多多 / 抖音）
- 广告保本 ROI 分析（上传 Excel 自动计算）
- Google Trends 泰国区热词同步
- 全类目词库管理
- 用户登录 + 角色权限（管理员/主管/运营）
- 企业后台（用户管理/激活码/操作日志/在线用户）

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开浏览器访问 http://localhost:8501

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 部署

详见 [deploy.md](deploy.md)

## 项目结构

```
├── app.py                      # 主入口
├── config.py                   # 全局配置
├── requirements.txt            # 依赖（5个，无编译依赖）
├── runtime.txt                 # Python 3.11
├── .streamlit/config.toml      # 暗色主题
├── database/db.py              # SQLite WAL 模式
├── auth/auth.py                # 登录/权限
├── pages/                      # 页面
│   ├── page_login.py
│   ├── page_seo.py
│   ├── page_roi.py
│   ├── page_keywords.py
│   ├── page_lexicon.py
│   └── page_admin.py
├── utils/                      # 工具
│   ├── seo_engine.py
│   ├── excel_handler.py
│   ├── roi_analyzer.py
│   ├── trend_scraper.py
│   └── lexicon_manager.py
└── data/
    └── thai_keywords_lexicon.json
```

## 五大类目

| # | 类目 | 子类目示例 |
|---|------|-----------|
| 1 | 数码3C/家电 | 智能手表、蓝牙耳机、手机壳、充电宝 |
| 2 | 美妆个护/服装鞋包 | 面霜、防晒霜、时装套装、包包 |
| 3 | 母婴玩具 | 婴儿推车、餐椅、纸尿裤、奶瓶 |
| 4 | 居家生活/户外露营 | 月亮椅、折叠桌、帐篷、藤编家具 |
| 5 | 食品饮料 | 零食、茶叶、咖啡、保健品 |

## 八大平台字数限制

| 平台 | 限制 | 平台 | 限制 |
|------|------|------|------|
| Shopee 泰国站 | 120 | Temu | 150 |
| Lazada 泰国站 | 130 | Amazon | 200 |
| TikTok 海外 | 100 | 淘宝 | 60 |
| 拼多多 | 120 | 抖音 | 55 |

## 技术栈

- **前端**: Streamlit 1.44
- **数据**: Pandas 2.2 / openpyxl 3.1
- **网络**: Requests / BeautifulSoup4
- **部署**: Streamlit Cloud / HuggingFace Spaces（免费）
