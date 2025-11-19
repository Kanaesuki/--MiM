xms/
├── dialogue_system.py    # 主程序
├── configs/              # 配置文件目录
│   ├── default.json
│   ├── stage4a.json
│   └── 新关卡.json      # 新建的配置文件
├── text/                 # 对话文本目录
│   └── talk_X_X_X.txt
├── image/                # 图片资源目录
│   ├── background/
│   ├── title/
│   ├── bgm/
│   └── talk/
└── sound/                # 音效目录


##  添加新关卡

### 1. 创建配置文件
在 `configs/` 目录下创建 `新关卡名.json`

### 2. 复制模板
```json
{
  "background_path": "image/background/bg_XX_XX.png",
  "title_path": "image/title/title_XX.png",
  "bgm_path": "image/bgm/bgm_XX_X.png",
  "text_path": "text/talk_X_X_X.txt",
  "char_colors": {},
  "characters": {},
  "triggers": {}
}
```

### 3. 填写路径
修改 `background_path`, `title_path`, `bgm_path`, `text_path`

### 4. 添加角色
在 `char_colors` 和 `characters` 中添加角色配置

### 5. 添加触发（可选）
在 `triggers` 中添加触发条件
