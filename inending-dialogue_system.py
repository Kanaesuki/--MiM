import pygame
import sys
import json
import os

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("连缘戏名实　～ Mirror_in_Mirrors")
clock = pygame.time.Clock()

# ====================== 通用类定义 ======================
"""带淡入淡出效果的图片类"""


class FadeImage:

    def __init__(self, img_path, center_pos, target_width=None, target_height=None, fade_speed=5, show_duration=1000):
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图片文件不存在: {img_path}\n请检查配置文件中的路径是否正确")
        self.surface = pygame.image.load(img_path).convert_alpha()
        if target_width or target_height:
            self.surface = self.scale_image(self.surface, target_width, target_height)
        self.rect = self.surface.get_rect(center=center_pos)

        self.visible = False
        self.alpha = 0
        self.fade_speed = fade_speed
        self.show_duration = show_duration
        self.entering = False
        self.showing = False
        self.show_start_time = 0
        self.has_shown = False

    def scale_image(self, image, target_width=None, target_height=None):
        orig_w, orig_h = image.get_size()
        if target_width:
            scale_ratio = target_width / orig_w
            new_h = int(orig_h * scale_ratio)
            return pygame.transform.smoothscale(image, (target_width, new_h))
        elif target_height:
            scale_ratio = target_height / orig_h
            new_w = int(orig_w * scale_ratio)
            return pygame.transform.smoothscale(image, (new_w, target_height))
        return image

    def trigger_show(self):
        if not self.has_shown:
            self.visible = True
            self.entering = True
            self.alpha = 0
            self.has_shown = True

    def update(self):
        if self.entering:
            self.alpha += self.fade_speed
            if self.alpha >= 255:
                self.alpha = 255
                self.entering = False
                self.showing = True
                self.show_start_time = pygame.time.get_ticks()
        elif self.showing:
            if pygame.time.get_ticks() - self.show_start_time >= self.show_duration:
                self.showing = False
        elif self.visible and not self.entering and not self.showing:
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.alpha = 0
                self.visible = False

    def draw(self, screen):
        if self.visible:
            temp_surf = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
            temp_surf.blit(self.surface, (0, 0))
            temp_surf.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(temp_surf, self.rect)


"""角色移动类（右侧：从右入场/离场）"""


class SpriteMover:

    def __init__(self, start_x, enter_target_x, leave_target_x, enter_speed=16, leave_speed=16):
        self.x = start_x
        self.enter_target_x = enter_target_x
        self.leave_target_x = leave_target_x
        self.enter_speed = enter_speed
        self.leave_speed = leave_speed

        self.is_show = False
        self.is_entering = False
        self.is_leaving = False
        self.enter_done = False
        self.leave_done = False

    def trigger_enter(self):
        if not self.enter_done:
            self.is_show = True
            self.is_entering = True
            self.enter_done = True

    def trigger_leave(self):
        if not self.leave_done:
            self.is_leaving = True
            self.leave_done = True

    def update(self):
        if self.is_show:
            if self.is_leaving:
                if self.x < self.leave_target_x:
                    self.x += self.leave_speed
                else:
                    self.x = self.leave_target_x
                    self.is_show = False
            elif self.is_entering:
                if self.x > self.enter_target_x:
                    self.x -= self.enter_speed
                else:
                    self.x = self.enter_target_x
                    self.is_entering = False


"""角色移动类（左侧：从左入场/离场）"""


class SpriteMover2:

    def __init__(self, start_x, enter_target_x, leave_target_x, enter_speed=16, leave_speed=16):
        self.x = start_x
        self.enter_target_x = enter_target_x
        self.leave_target_x = leave_target_x
        self.enter_speed = enter_speed
        self.leave_speed = leave_speed

        self.is_show = False
        self.is_entering = False
        self.is_leaving = False
        self.enter_done = False
        self.leave_done = False

    def trigger_enter(self):
        if not self.enter_done:
            self.is_show = True
            self.is_entering = True
            self.enter_done = True

    def trigger_leave(self):
        if not self.leave_done:
            self.is_leaving = True
            self.leave_done = True

    def update(self):
        if self.is_show:
            if self.is_leaving:
                if self.x > self.leave_target_x:
                    self.x -= self.leave_speed
                else:
                    self.x = self.leave_target_x
                    self.is_show = False
            elif self.is_entering:
                if self.x < self.enter_target_x:
                    self.x += self.enter_speed
                else:
                    self.x = self.enter_target_x
                    self.is_entering = False


# ====================== 核心功能函数 ======================
"""解析对话文本文件"""


def parse_dialogue(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"对话文件不存在: {file_path}\n请检查配置文件中的 text_path 是否正确")
    dialogue = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("9,"):
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 4:
                char_idx = int(parts[0])
                char_name = parts[1]
                sprite_idx = int(parts[2])
                content = ",".join(parts[3:])
                dialogue.append({
                    "char_idx": char_idx,
                    "char_name": char_name,
                    "sprite_idx": sprite_idx,
                    "content": content
                })
    return dialogue


"""加载角色立绘"""


def load_sprite(char_idx, sprite_idx, image_dir="image/talk"):
    sprite_path = f"{image_dir}/talk_{char_idx}_{sprite_idx:02d}.png"
    if not os.path.exists(sprite_path):
        raise FileNotFoundError(f"立绘文件不存在: {sprite_path}\n角色编号: {char_idx}, 立绘编号: {sprite_idx:02d}")
    sprite = pygame.image.load(sprite_path).convert_alpha()
    return sprite


"""立绘变暗处理"""


def get_gray_sprite(sprite):
    dark_sprite = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    dark_sprite.lock()
    sprite.lock()

    dark_factor = 0.05
    saturation_factor = 0.2

    for x in range(sprite.get_width()):
        for y in range(sprite.get_height()):
            r, g, b, a = sprite.get_at((x, y))
            if a > 10:
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                dark_gray = int(gray * dark_factor)
                new_r = int(r * saturation_factor + dark_gray * (1 - saturation_factor))
                new_g = int(g * saturation_factor + dark_gray * (1 - saturation_factor))
                new_b = int(b * saturation_factor + dark_gray * (1 - saturation_factor))
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))
                dark_sprite.set_at((x, y), (new_r, new_g, new_b, a))
            else:
                dark_sprite.set_at((x, y), (0, 0, 0, a))

    dark_sprite.unlock()
    sprite.unlock()
    return dark_sprite


"""绘制对话框（支持描边和字间距）"""


def draw_dialog_box(screen, char_name, content, speaker_idx, char_colors,
                    name_font, dialogue_font, stroke_color=(0, 0, 0),
                    stroke_offset=1, letter_spacing=3):

    name_x = 40
    current_x = name_x
    for char in char_name:
        char_stroke = name_font.render(char, True, stroke_color)
        screen.blit(char_stroke, (current_x - stroke_offset, 373 - stroke_offset))
        screen.blit(char_stroke, (current_x + stroke_offset, 373 - stroke_offset))
        screen.blit(char_stroke, (current_x - stroke_offset, 373 + stroke_offset))
        screen.blit(char_stroke, (current_x + stroke_offset, 373 + stroke_offset))
        char_surf = name_font.render(char, True, (255, 255, 255))
        screen.blit(char_surf, (current_x, 373))
        current_x += name_font.size(char)[0] + letter_spacing


    # 对话颜色
    text_color = char_colors.get(speaker_idx, (255, 255, 255))

    # 绘制对话内容（带描边和字间距）
    line_height = 22
    x, y = 40, 395
    current_line_width = 0
    current_line_chars = []

    for char in content:
        char_width = dialogue_font.size(char)[0]
        predicted_width = current_line_width + char_width + (letter_spacing if current_line_chars else 0)

        if predicted_width <= 365:
            current_line_chars.append(char)
            current_line_width = predicted_width
        else:
            draw_x = x
            for c in current_line_chars:
                c_stroke = dialogue_font.render(c, True, stroke_color)
                screen.blit(c_stroke, (draw_x - stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x - stroke_offset, y + stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y + stroke_offset))
                c_surf = dialogue_font.render(c, True, text_color)
                screen.blit(c_surf, (draw_x, y))
                draw_x += dialogue_font.size(c)[0] + letter_spacing
            y += line_height
            current_line_chars = [char]
            current_line_width = char_width

    # 绘制最后一行
    draw_x = x
    for c in current_line_chars:
        c_stroke = dialogue_font.render(c, True, stroke_color)
        screen.blit(c_stroke, (draw_x - stroke_offset, y - stroke_offset))
        screen.blit(c_stroke, (draw_x + stroke_offset, y - stroke_offset))
        screen.blit(c_stroke, (draw_x - stroke_offset, y + stroke_offset))
        screen.blit(c_stroke, (draw_x + stroke_offset, y + stroke_offset))
        c_surf = dialogue_font.render(c, True, text_color)
        screen.blit(c_surf, (draw_x, y))
        draw_x += dialogue_font.size(c)[0] + letter_spacing


def draw_dialog_box_ending(screen, char_name, content, speaker_idx, char_colors,
                    name_font, dialogue_font, stroke_color=(0, 0, 0),
                    stroke_offset=1, letter_spacing=3):

    name_x = 40
    current_x = name_x
    # 从颜色字典中获取当前说话者的颜色，没有则用白色
    name_color = char_colors.get(speaker_idx, (255, 255, 255))

    if char_name != '.':
        for char in char_name:
            char_stroke = name_font.render(char, True, stroke_color)
            screen.blit(char_stroke, (current_x - stroke_offset, 376 - stroke_offset))
            screen.blit(char_stroke, (current_x + stroke_offset, 376 - stroke_offset))
            screen.blit(char_stroke, (current_x - stroke_offset, 376 + stroke_offset))
            screen.blit(char_stroke, (current_x + stroke_offset, 376 + stroke_offset))
            char_surf = name_font.render(char, True, name_color)
            screen.blit(char_surf, (current_x, 376))
            current_x += name_font.size(char)[0] + letter_spacing
    else:
        char_surf = name_font.render(' ', True, name_color)
        screen.blit(char_surf, (current_x, 376))


    # 对话颜色
    text_color = char_colors.get(speaker_idx, (255, 255, 255))

    # 绘制对话内容（带描边和字间距）
    line_height = 22
    x, y = 40, 400
    current_line_width = 0
    current_line_chars = []

    for char in content:
        char_width = dialogue_font.size(char)[0]
        predicted_width = current_line_width + char_width + (letter_spacing if current_line_chars else 0)

        if predicted_width <= 560:
            current_line_chars.append(char)
            current_line_width = predicted_width
        else:
            draw_x = x
            for c in current_line_chars:
                c_stroke = dialogue_font.render(c, True, stroke_color)
                screen.blit(c_stroke, (draw_x - stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x - stroke_offset, y + stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y + stroke_offset))
                c_surf = dialogue_font.render(c, True, text_color)
                screen.blit(c_surf, (draw_x, y))
                draw_x += dialogue_font.size(c)[0] + letter_spacing
            y += line_height
            current_line_chars = [char]
            current_line_width = char_width

    # 绘制最后一行
    draw_x = x
    for c in current_line_chars:
        c_stroke = dialogue_font.render(c, True, stroke_color)
        screen.blit(c_stroke, (draw_x - stroke_offset, y - stroke_offset))
        screen.blit(c_stroke, (draw_x + stroke_offset, y - stroke_offset))
        screen.blit(c_stroke, (draw_x - stroke_offset, y + stroke_offset))
        screen.blit(c_stroke, (draw_x + stroke_offset, y + stroke_offset))
        c_surf = dialogue_font.render(c, True, text_color)
        screen.blit(c_surf, (draw_x, y))
        draw_x += dialogue_font.size(c)[0] + letter_spacing

# ====================== 配置加载 ======================
"""获取所有可用的关卡列表"""


def get_available_stages():
    stages = []
    if os.path.exists("configs"):
        for file in os.listdir("configs"):
            if file.endswith(".json"):
                stage_name = file[:-5]  # 去掉.json后缀
                stages.append(stage_name)
    # 如果没有找到任何关卡，返回默认关卡
    if not stages:
        stages = ["default"]
    return sorted(stages)


"""加载关卡配置"""


def load_stage_config(stage_name):
    config_file = f"configs/{stage_name}.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 返回默认配置
        return {
            "background_path": "image/background/bg_1_02.png",
            "title_path": "image/title/title_1.png",
            "bgm_path": "image/bgm/bgm_1_1.png",
            "text_path": "text/talk_1_0_1.txt",
            "char_colors": {
                0: [90, 121, 255],
                1: [255, 156, 159],
                2: [198, 51, 54]
            },
            "triggers": {}
        }


"""关卡选择界面（带自动滚动）"""


def stage_select_screen():
    # 获取可用关卡
    stages = get_available_stages()
    if not stages:
        return "default"

    # 加载背景图片
    background = None
    bg_path = "image/background/select_bg.png"
    if os.path.exists(bg_path):
        background = pygame.image.load(bg_path).convert()
    else:
        print(f"警告: 选择界面背景图片不存在 {bg_path}，将使用默认黑色背景")

    # 字体设置
    title_font_path = "C:/Windows/Fonts/msyh.ttc"
    stage_font = pygame.font.Font(title_font_path, 20)

    selected_index = 0
    running = True

    # 描边配置（可调整）
    stroke_color = (0, 0, 0)  # 描边颜色（黑色）
    stroke_offset = 1  # 描边偏移量（像素）

    # 计算显示参数
    start_y = 150
    line_height = 40
    center_y = 320
    visible_lines = 5

    while running:
        # 绘制背景
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # 计算显示范围
        display_start = max(0, selected_index - visible_lines // 2)
        display_end = min(len(stages), display_start + visible_lines)

        # 计算选中项相对位置
        selected_offset = selected_index - display_start

        # 绘制可见范围内的关卡列表（核心修改：添加描边）
        for i in range(display_start, display_end):
            stage_name = stages[i]
            relative_index = i - display_start

            # 选择颜色
            if i == selected_index:
                color = (255, 255, 0)  # 选中项黄色
                prefix = "> "
            else:
                color = (200, 200, 200)  # 未选中项灰色
                prefix = "  "

            # 计算Y坐标
            y_pos = center_y + (relative_index - selected_offset) * line_height

            # 只绘制可见区域内的项
            if 100 <= y_pos <= SCREEN_HEIGHT - 120:
                text_content = f"{prefix}{stage_name}"

                # 1. 绘制描边（上下左右四个方向）
                stroke_surf = stage_font.render(text_content, True, stroke_color)
                screen.blit(stroke_surf, (SCREEN_WIDTH - 220 - stroke_offset, y_pos - stroke_offset))  # 左上
                screen.blit(stroke_surf, (SCREEN_WIDTH - 220 + stroke_offset, y_pos - stroke_offset))  # 右上
                screen.blit(stroke_surf, (SCREEN_WIDTH - 220 - stroke_offset, y_pos + stroke_offset))  # 左下
                screen.blit(stroke_surf, (SCREEN_WIDTH - 220 + stroke_offset, y_pos + stroke_offset))  # 右下

                # 2. 绘制原文本（叠在描边上方）
                text_surf = stage_font.render(text_content, True, color)
                screen.blit(text_surf, (SCREEN_WIDTH - 220, y_pos))

        # 事件处理（保持原逻辑不变）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(stages)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(stages)
                elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                    return stages[selected_index]
                elif event.key == pygame.K_ESCAPE:
                    return None

        pygame.display.flip()
        clock.tick(60)

    return None


# ====================== 主游戏循环 ======================

def main(stage_name="default"):
    """主游戏函数"""
    # 加载配置
    config = load_stage_config(stage_name)

    # 字体加载
    dialogue_font_path = "C:/Windows/Fonts/msyh.ttc"
    dialogue_font = pygame.font.Font(dialogue_font_path, 12)
    name_font_path = "C:/Windows/Fonts/msyh.ttc"
    name_font = pygame.font.Font(name_font_path, 12)

    # 颜色配置（键转换为整数）
    char_colors = {int(k): tuple(v) for k, v in config.get("char_colors", {}).items()}

    # 加载资源（添加文件存在性检查）
    resource_files = {
        "background": config["background_path"],
        "talk_board": "image/else/talk_board.png" if "ending" not in config["title_path"] else "image/else/talk_board_ending.png",
        "talk_sound": "sound/talk_00.wav",
        "board": config["game_board_path"]
    }

    resources = {}
    for key, path in resource_files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"资源文件不存在: {path}\n请确保文件存在于正确的位置")
        if key == "talk_sound":
            resources[key] = pygame.mixer.Sound(path)
        else:
            resources[key] = pygame.image.load(path).convert_alpha()


    # 加载称号和BGM图片
    title_img = FadeImage(
        img_path=config["title_path"],
        center_pos=(320, 240) if "ending" in config["title_path"] else (290, 340),
        fade_speed=5,
        show_duration=100000 if "ending" in config["title_path"] else 1000
    )

    bgm_img = FadeImage(
        img_path=config["bgm_path"],
        center_pos=(320, 240) if "ending" in config["title_path"] else (230, 455),
        target_height=480 if "ending" in config["title_path"] else 18,
        fade_speed=5,
        show_duration=100000 if "ending" in config["title_path"] else 1000
    )

    # 解析对话
    dialogue = parse_dialogue(config["text_path"])

    # 角色移动器配置（根据配置创建）
    char_movers = {}
    triggers = config.get("triggers", {})

    # 角色配置
    char_configs = config.get("characters", {})
    for char_idx, char_config in char_configs.items():
        char_idx = int(char_idx)
        if char_config.get("side") == "left":
            mover = SpriteMover2(
                start_x=char_config["start_x"],
                enter_target_x=char_config["enter_target_x"],
                leave_target_x=char_config["leave_target_x"],
                enter_speed=char_config.get("enter_speed", 16),
                leave_speed=char_config.get("leave_speed", 16)
            )
        else:
            mover = SpriteMover(
                start_x=char_config["start_x"],
                enter_target_x=char_config["enter_target_x"],
                leave_target_x=char_config["leave_target_x"],
                enter_speed=char_config.get("enter_speed", 16),
                leave_speed=char_config.get("leave_speed", 16)
            )
        char_movers[char_idx] = {
            "mover": mover,
            "pos_y": char_config.get("pos_y", 150),
            "side": char_config.get("side", "right")
        }

    # 游戏状态
    current_line = 0
    char_sprites = {}
    last_sprite_idx = {}
    last_left_speaker = None
    LEFT_SPEAKER_OFFSET = -10

    # 对话开始时，自动触发所有左侧角色同时入场
    for char_idx, char_data in char_movers.items():
        if char_data["side"] == "left":
            char_data["mover"].trigger_enter()

    # 如果关卡名称以 _02 结尾，也自动触发右侧角色入场
    # 但 stage4 的 _02 关卡中，角色6在离场后不应该再次登场
    if stage_name.endswith("_02"):
        for char_idx, char_data in char_movers.items():
            if char_data["side"] == "right":
                # stage4 的 _02 关卡中，角色6不自动入场（因为在前面的_01中已离场）
                if stage_name.startswith("stage4") and char_idx == 6:
                    continue
                char_data["mover"].trigger_enter()

    running = True

    while running:
        screen.blit(resources["background"], (0, 0))

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # 完全退出
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    if resources["talk_sound"]:
                        resources["talk_sound"].play()
                    current_line = (current_line + 1) % len(dialogue)
                elif event.key == pygame.K_x:
                    # 按X键返回选择界面
                    return True  # 返回选择界面

        # 获取当前对话
        current = dialogue[current_line]
        speaker_idx = current["char_idx"]
        char_name = current["char_name"]
        content = current["content"]
        current_sprite_idx = current["sprite_idx"]

        # 更新角色立绘索引
        if speaker_idx not in last_sprite_idx:
            last_sprite_idx[speaker_idx] = 0
        if speaker_idx == current["char_idx"]:
            last_sprite_idx[speaker_idx] = current_sprite_idx

        # 如果角色第一次说话且配置中有该角色，自动触发入场
        if speaker_idx in char_movers and not char_movers[speaker_idx]["mover"].is_show:
            char_movers[speaker_idx]["mover"].trigger_enter()

        # 处理触发
        for trigger_type, trigger_config in triggers.items():
            trigger_text = trigger_config.get("trigger_text", "")
            if trigger_text and trigger_text in content:
                # 称号触发
                if trigger_type == "title":
                    required_speaker = trigger_config.get("speaker")
                    # 确保类型一致（JSON中的数字可能是int或str）
                    if required_speaker is not None:
                        required_speaker = int(required_speaker)
                    if required_speaker is None or speaker_idx == required_speaker:
                        title_img.trigger_show()
                # BGM触发
                elif trigger_type == "bgm":
                    required_speaker = trigger_config.get("speaker")
                    # 确保类型一致（JSON中的数字可能是int或str）
                    if required_speaker is not None:
                        required_speaker = int(required_speaker)
                    if required_speaker is None or speaker_idx == required_speaker:
                        bgm_img.trigger_show()
                # 角色入场触发
                elif trigger_type.startswith("char_") and "_enter" in trigger_type:
                    char_idx = int(trigger_config.get("char_idx", 0))
                    if char_idx in char_movers:
                        char_movers[char_idx]["mover"].trigger_enter()
                # 角色离场触发
                elif trigger_type.startswith("char_") and "_leave" in trigger_type:
                    char_idx = int(trigger_config.get("char_idx", 0))
                    if char_idx in char_movers:
                        char_movers[char_idx]["mover"].trigger_leave()

        # 更新移动器
        for char_idx, char_data in char_movers.items():
            char_data["mover"].update()

        # 分离说话者和非说话者
        speaker_char_data = None
        non_speaker_chars = []

        for char_idx, char_data in char_movers.items():
            if char_idx == speaker_idx:
                speaker_char_data = (char_idx, char_data)
            else:
                non_speaker_chars.append((char_idx, char_data))

        # 第一步：绘制所有非说话者（下层）
        for char_idx, char_data in non_speaker_chars:
            mover = char_data["mover"]
            pos_y = char_data["pos_y"]
            side = char_data["side"]

            if mover.is_show:
                # 加载立绘（使用上次的立绘索引）
                sprite_idx = last_sprite_idx.get(char_idx, 0)
                sprite_key = (char_idx, sprite_idx)

                if sprite_key not in char_sprites:
                    original = load_sprite(char_idx, sprite_idx)
                    gray = get_gray_sprite(original)
                    char_sprites[sprite_key] = (original, gray)

                _, gray_sprite = char_sprites[sprite_key]

                # 计算位置
                draw_x = mover.x
                draw_y = pos_y

                # 绘制变暗的立绘
                screen.blit(gray_sprite, (draw_x, draw_y))

        # 第二步：绘制说话者（上层，无论是左侧还是右侧）
        if speaker_char_data:
            char_idx, char_data = speaker_char_data
            mover = char_data["mover"]
            pos_y = char_data["pos_y"]
            side = char_data["side"]

            if mover.is_show:
                # 加载立绘（使用当前的立绘索引）
                sprite_idx = current_sprite_idx
                sprite_key = (char_idx, sprite_idx)

                if sprite_key not in char_sprites:
                    original = load_sprite(char_idx, sprite_idx)
                    gray = get_gray_sprite(original)
                    char_sprites[sprite_key] = (original, gray)

                original_sprite, _ = char_sprites[sprite_key]

                # 计算位置
                draw_x = mover.x
                if side == "left":
                    # 左侧说话者向上偏移
                    draw_y = pos_y + LEFT_SPEAKER_OFFSET
                else:
                    # 右侧说话者正常位置
                    draw_y = pos_y

                # 绘制亮色的立绘（说话者）
                screen.blit(original_sprite, (draw_x, draw_y))

        # 更新左侧说话者记录
        if speaker_idx in char_movers and char_movers[speaker_idx]["side"] == "left":
            last_left_speaker = speaker_idx

        # 绘制UI
        if "ending" not in config["title_path"]:
            screen.blit(resources["talk_board"], (0, 0))

        # 更新并绘制称号和BGM
        title_img.update()
        title_img.draw(screen)
        bgm_img.update()
        bgm_img.draw(screen)

        if "ending"  in config["title_path"]:
            screen.blit(resources["talk_board"], (0, 0))

        # 绘制对话框
        if "ending" not in config["title_path"]:
            draw_dialog_box(screen, char_name, content, speaker_idx, char_colors,
                        name_font, dialogue_font)
        else:
            draw_dialog_box_ending(screen, char_name, content, speaker_idx, char_colors,
                            name_font, dialogue_font)

        screen.blit(resources["board"], (0, 0))

        pygame.display.flip()
        clock.tick(60)

    return False  # 正常结束，退出程序


if __name__ == "__main__":

    while True:
        if len(sys.argv) > 1:
            # 命令行参数模式：直接运行指定关卡，运行后退出
            stage = sys.argv[1]
            main(stage)
            break
        else:
            # 显示关卡选择界面
            stage = stage_select_screen()
            if stage is None:
                # 用户取消了选择或关闭了窗口
                break

            # 运行选中的关卡
            should_return = main(stage)

            # 如果返回True，说明按了X键，继续循环显示选择界面
            # 如果返回False，说明正常结束或关闭窗口，退出程序
            if not should_return:
                break

    pygame.quit()
    sys.exit()

