import pygame
import sys

# 初始化 Pygame
pygame.init()
pygame.mixer.init()  # 作用：声音播放

# 屏幕设置
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("连缘戏名实　～ Mirror_in_Mirrors")
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
stroke_color = (0, 0, 0)  # BLACK
left1_color = (90, 121, 255)
left2_color = (198, 51, 54)
right_color = (171, 171, 171)
char6_color = (100, 200, 100)  # 编号6角色对话颜色

# ====================== 全局触发变量（方便修改调试）======================

char6_leave_trigger = "——？！"
char10_leave_trigger = "——？！"
char4_enter_trigger = "度芽大人！你怎么了？"
char6_enter_trigger = "怎么又碰到你们了"
right_char_out_trigger = "out"
title_trigger = "晴空万里，碧空如洗"
bgm_trigger = "多说无用"

CHAR00_IDX = 00  # 自机羽泽度芽
CHAR10_IDX = 10  # 自机羽初赤红
CHAR6_IDX = 6  # 敌方???
CHAR4_IDX = 5  # 敌方羽泽度芽
boss_num = CHAR4_IDX  # 右侧角色默认是编号4

background_path = "image/background/bg_8_02.png"
title_path = "image/title/title_8.png"
bgm_path = "image/bgm/bgm_8_1.png"
text_path = "text/talk_4_1_2.txt"

# 字体单独加载
# load_resource 是为了 “集中管理可替换、高成本、场景化的资源”，而字体是 “全局唯一、低成本、启动即需” 的资源 —— 单独加载更贴合其使用场景。
# 字体是 全局配置项（对话字号 12、名字字号 12，全程不变），而 load_resource 加载的是 场景相关资源（比如某个关卡的背景图、某个对话的音效）

# 字体加载
# 对话字体与大小
dialogue_font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
dialogue_font = pygame.font.Font(dialogue_font_path, 12)
name_font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
name_font = pygame.font.Font(name_font_path, 12)


# 通用的 “带淡入淡出效果的图片加载”
class FadeImage:
    def __init__(self, img_path, center_pos, target_width=None, target_height=None, fade_speed=5, show_duration=1000):
        # 1. 加载并缩放图片
        self.surface = pygame.image.load(img_path).convert_alpha()
        if target_width or target_height:
            self.surface = self.scale_image(self.surface, target_width, target_height)

        # 2. 初始化显示位置
        self.rect = self.surface.get_rect(center=center_pos)

        # 3. 初始化显示状态
        self.visible = False
        self.alpha = 0
        self.fade_speed = fade_speed
        self.show_duration = show_duration
        self.entering = False
        self.showing = False
        self.show_start_time = 0
        self.has_shown = False

    # 等比缩放函数
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

    # trigger
    def trigger_show(self):
        if not self.has_shown:
            self.visible = True
            self.entering = True
            self.alpha = 0
            self.has_shown = True

    # 更新显示状态
    def update(self):
        if self.entering:
            # 淡入：透明度递增到255
            self.alpha += self.fade_speed
            if self.alpha >= 255:
                self.alpha = 255
                self.entering = False
                self.showing = True
                self.show_start_time = pygame.time.get_ticks()  # 记录显示开始时间
        elif self.showing:
            # 保持显示：持续show_duration毫秒后开始淡出
            if pygame.time.get_ticks() - self.show_start_time >= self.show_duration:
                self.showing = False
        elif self.visible and not self.entering and not self.showing:
            # 淡出：透明度递减到0
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.alpha = 0
                self.visible = False

    # 绘制图片
    def draw(self, screen):
        if self.visible:
            temp_surf = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
            temp_surf.blit(self.surface, (0, 0))
            temp_surf.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(temp_surf, self.rect)


# 通用角色移动类（右侧角色：从右入场、从右离场）
class SpriteMover:
    def __init__(self, start_x, enter_target_x, leave_target_x, enter_speed=16, leave_speed=16):
        self.x = start_x  # 当前X坐标
        self.enter_target_x = enter_target_x  # 入场目标X
        self.leave_target_x = leave_target_x  # 离场目标X
        self.enter_speed = enter_speed  # 入场速度
        self.leave_speed = leave_speed  # 离场速度

        # 移动状态标记
        self.is_show = False  # 是否显示角色
        self.is_entering = False  # 是否正在入场
        self.is_leaving = False  # 是否正在离场
        self.enter_done = False  # 入场完成标记（避免重复入场）
        self.leave_done = False  # 离场完成标记（避免重复离场）

    # 触发入场（外部调用）
    def trigger_enter(self):
        if not self.enter_done:
            self.is_show = True
            self.is_entering = True
            self.enter_done = True

    # 触发离场（外部调用，比如对话触发）
    def trigger_leave(self):
        if not self.leave_done:
            self.is_leaving = True
            self.leave_done = True

    # 更新移动状态（每帧调用，自动处理入场/离场）
    def update(self):
        if self.is_show:
            if self.is_leaving:
                # 离场：向leave_target_x移动（从左→右）
                if self.x < self.leave_target_x:
                    self.x += self.leave_speed
                else:
                    self.x = self.leave_target_x
                    self.is_show = False  # 完全离场后隐藏
            elif self.is_entering:
                # 入场：向enter_target_x移动（从右→左）
                if self.x > self.enter_target_x:
                    self.x -= self.enter_speed
                else:
                    self.x = self.enter_target_x  # 固定到目标位置
                    self.is_entering = False  # 入场完成


# 通用角色移动类2（左侧角色：从左入场、从左离场）
class SpriteMover2:
    def __init__(self, start_x, enter_target_x, leave_target_x, enter_speed=16, leave_speed=16):
        self.x = start_x  # 当前X坐标
        self.enter_target_x = enter_target_x  # 入场目标X
        self.leave_target_x = leave_target_x  # 离场目标X
        self.enter_speed = enter_speed  # 入场速度
        self.leave_speed = leave_speed  # 离场速度

        # 移动状态标记
        self.is_show = False  # 是否显示角色
        self.is_entering = False  # 是否正在入场
        self.is_leaving = False  # 是否正在离场
        self.enter_done = False  # 入场完成标记（避免重复入场）
        self.leave_done = False  # 离场完成标记（避免重复离场）

    # 触发入场（外部调用）
    def trigger_enter(self):
        if not self.enter_done:
            self.is_show = True
            self.is_entering = True
            self.enter_done = True

    # 触发离场（外部调用，比如对话触发）
    def trigger_leave(self):
        if not self.leave_done:
            self.is_leaving = True
            self.leave_done = True

    # 更新移动状态（每帧调用，自动处理入场/离场）
    def update(self):
        if self.is_show:
            if self.is_leaving:
                # 离场：向leave_target_x移动（从右→左）
                if self.x > self.leave_target_x:
                    self.x -= self.leave_speed
                else:
                    self.x = self.leave_target_x
                    self.is_show = False  # 完全离场后隐藏
            elif self.is_entering:
                # 入场：向enter_target_x移动（从左→右）
                if self.x < self.enter_target_x:
                    self.x += self.enter_speed
                else:
                    self.x = self.enter_target_x  # 固定到目标位置
                    self.is_entering = False  # 入场完成


# 加载资源
def load_resource():
    resources = {}
    resources["background"] = pygame.image.load(background_path).convert_alpha()
    resources["talk_board"] = pygame.image.load("image/else/talk_board.png").convert_alpha()
    resources["talk_sound"] = pygame.mixer.Sound("sound/talk_00.wav")
    resources["board"] = pygame.image.load("image/else/game_board_1.png").convert_alpha()
    return resources


resources = load_resource()

# 加载称号图片
title_img = FadeImage(
    img_path=title_path,
    center_pos=(290, 340),  # center位置
    fade_speed=5,
    show_duration=1000
)

# 加载BGM图片
bgm_img = FadeImage(
    img_path=bgm_path,
    center_pos=(230, 455),
    target_height=18,
    fade_speed=5,
    show_duration=1000
)

# ====================== 角色位置配置 =======================
LEFT_CHAR1_POS = (-320, 200)  # 左1角色（00）基础位置
LEFT_CHAR2_POS = (25, 150)  # 左2角色（10）基础位置
RIGHT_CHAR_POS_Y = 175  # 右侧角色（6、5、4）基础Y坐标
LEFT_SPEAKER_OFFSET = -10  # 说话者向上偏移量

# ====================== 角色移动实例配置 =======================
# 左1角色（00：羽泽度芽）
left1_sprite_mover = SpriteMover2(
    start_x=-320,
    enter_target_x=-20,
    leave_target_x=-320,
    enter_speed=25,
    leave_speed=25
)

# 左2角色（10：自机羽初赤红）
left2_sprite_mover = SpriteMover2(
    start_x=-275,
    enter_target_x=25,
    leave_target_x=-275,
    enter_speed=25,
    leave_speed=16
)

# 右侧角色1（6：???）
char6_sprite_mover = SpriteMover(
    start_x=550,  # 初始位置（右侧场外）
    enter_target_x=170,  # 入场目标位置（和其他右侧角色一致）
    leave_target_x=550,  # 离场目标位置（右侧场外）
    enter_speed=25,
    leave_speed=25
)



# 右侧角色3（5：敌方羽泽度芽）
char4_sprite_mover = SpriteMover(
    start_x=550,  # 初始位置（右侧场外）
    enter_target_x=170,  # 入场目标位置
    leave_target_x=550,  # 离场目标位置
    enter_speed=25,
    leave_speed=25
)


# 解析对话文本（返回对话列表+触发索引）
def parse_dialogue(file_path):
    dialogue = []
    trigger_indices = {
        "char6_leave": -1,  # 编号6离场的台词索引
        "char10_leave": -1,  # 编号10离场的台词索引
        "char4_enter": -1,  # 编号4入场的台词索引
        "char6_enter": -1  # 编号4入场的台词索引
    }
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("9,"):  # 跳过空行和结束标记
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 4:
                char_idx = int(parts[0])
                char_name = parts[1]
                sprite_idx = int(parts[2])
                content = ",".join(parts[3:])

                # 根据全局触发变量，记录对应台词的索引
                if  char6_leave_trigger in content:
                    trigger_indices["char6_leave"] = len(dialogue)
                if char10_leave_trigger in content:
                    trigger_indices["char10_leave"] = len(dialogue)
                if char4_enter_trigger in content:
                    trigger_indices["char4_enter"] = len(dialogue)
                if char6_enter_trigger in content:
                    trigger_indices["char6_enter"] = len(dialogue)

                dialogue.append({
                    "char_idx": char_idx,
                    "char_name": char_name,
                    "sprite_idx": sprite_idx,
                    "content": content
                })
    return dialogue, trigger_indices


# 加载单个角色立绘
def load_sprite(char_idx, sprite_idx):
    sprite_path = f"image/talk/talk_{char_idx}_{sprite_idx:02d}.png"
    sprite = pygame.image.load(sprite_path).convert_alpha()
    return sprite


# 立绘变暗
def get_gray_sprite(sprite):
    dark_sprite = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    dark_sprite.lock()
    sprite.lock()

    dark_factor = 0.05  # 变暗强度
    saturation_factor = 0.2  # 饱和度

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


# 通用立绘加载函数（带缓存）
def load_character_sprite(char_idx, sprite_idx, char_sprites_cache):
    cache_key = (char_idx, sprite_idx)
    if cache_key in char_sprites_cache:
        return char_sprites_cache[cache_key]
    original_sprite = load_sprite(char_idx, sprite_idx)
    dark_sprite = get_gray_sprite(original_sprite)
    char_sprites_cache[cache_key] = (original_sprite, dark_sprite)
    return original_sprite, dark_sprite


# 绘制文字（对话面板+名字+台词）
def draw_dialog_box(screen, char_name, content, speaker_idx):
    # 文字配置
    stroke_offset = 1  # 描边粗细
    letter_spacing = 3  # 字间距

    # ========== 角色名字（带描边+字间距） ==========
    current_x = 40
    current_y = 373
    for char in char_name:
        # 1. 绘制描边（4个方向）
        char_stroke = name_font.render(char, True, stroke_color)
        screen.blit(char_stroke, (current_x - stroke_offset, current_y - stroke_offset))
        screen.blit(char_stroke, (current_x + stroke_offset, current_y - stroke_offset))
        screen.blit(char_stroke, (current_x - stroke_offset, current_y + stroke_offset))
        screen.blit(char_stroke, (current_x + stroke_offset, current_y + stroke_offset))
        # 2. 绘制原颜色字符
        char_surf = name_font.render(char, True, (255, 255, 255))
        screen.blit(char_surf, (current_x, current_y))
        # 3. 移动x坐标（字符宽度 + 字间距）
        current_x += name_font.size(char)[0] + letter_spacing

    # ========== 对话颜色配置（按角色编号匹配） ==========
    if speaker_idx == CHAR00_IDX:
        text_color = left1_color
    elif speaker_idx == CHAR10_IDX:
        text_color = left2_color
    elif speaker_idx == CHAR6_IDX:
        text_color = char6_color
    elif speaker_idx == CHAR4_IDX:
        text_color = right_color
    else:
        text_color = WHITE

    # ========== 对话文本（带描边+字间距+自动换行） ==========
    line_height = 22
    x, y = 40, 395  # 对话起始位置
    current_line_width = 0  # 当前行已用宽度
    current_line_chars = []  # 当前行的字符列表

    for char in content:
        char_width = dialogue_font.size(char)[0]
        predicted_width = current_line_width + char_width + (letter_spacing if current_line_chars else 0)

        if predicted_width <= 365:  # 未超出最大宽度
            current_line_chars.append(char)
            current_line_width = predicted_width
        else:  # 超出宽度，换行绘制
            draw_x = x
            for c in current_line_chars:
                # 绘制描边
                c_stroke = dialogue_font.render(c, True, stroke_color)
                screen.blit(c_stroke, (draw_x - stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y - stroke_offset))
                screen.blit(c_stroke, (draw_x - stroke_offset, y + stroke_offset))
                screen.blit(c_stroke, (draw_x + stroke_offset, y + stroke_offset))
                # 绘制原字符
                c_surf = dialogue_font.render(c, True, text_color)
                screen.blit(c_surf, (draw_x, y))
                # 移动x坐标
                draw_x += dialogue_font.size(c)[0] + letter_spacing
            # 换行重置
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


# 主对话逻辑
def main():
    # 全局变量声明（仅用于兼容原有代码，实际未使用）
    global title_visible, title_alpha, title_entering, title_showing, title_show_start_time, title_has_shown
    global bgm_visible, bgm_alpha, bgm_entering, bgm_showing, bgm_show_start_time, bgm_has_shown
    flag = 0  # 初始入场标记

    # 解析对话和触发索引
    dialogue, trigger_indices = parse_dialogue(text_path)
    current_line = 0
    char_sprites_cache = {}
    running = True
    last_left_speaker = None  # 记录上一次左侧说话者
    # 立绘索引缓存（包含所有角色编号）
    last_sprite_idx = {
        CHAR00_IDX: 0,
        CHAR10_IDX: 0,
        CHAR6_IDX: 0,
        CHAR4_IDX: 0
    }

    while running:
        # 绘制背景
        screen.blit(resources["background"], (0, 0))

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                resources["talk_sound"].play()
                current_line = (current_line + 1) % len(dialogue)

        # 获取当前对话数据
        current = dialogue[current_line]
        speaker_idx = current["char_idx"]
        char_name = current["char_name"]
        content = current["content"]
        current_sprite_idx = current["sprite_idx"]

        # ====================== 角色立绘加载 =======================
        # 更新当前说话角色的立绘索引
        if speaker_idx in last_sprite_idx:
            last_sprite_idx[speaker_idx] = current_sprite_idx

        # 加载所有角色的立绘（亮态+暗态）
        char0_orig, char0_dark = load_character_sprite(
            char_idx=CHAR00_IDX,
            sprite_idx=last_sprite_idx[CHAR00_IDX],
            char_sprites_cache=char_sprites_cache
        )
        char10_orig, char10_dark = load_character_sprite(
            char_idx=CHAR10_IDX,
            sprite_idx=last_sprite_idx[CHAR10_IDX],
            char_sprites_cache=char_sprites_cache
        )
        char6_orig, char6_dark = load_character_sprite(
            char_idx=CHAR6_IDX,
            sprite_idx=last_sprite_idx[CHAR6_IDX],
            char_sprites_cache=char_sprites_cache
        )
        char4_orig, char4_dark = load_character_sprite(
            char_idx=CHAR4_IDX,
            sprite_idx=last_sprite_idx[CHAR4_IDX],
            char_sprites_cache=char_sprites_cache
        )

        # 更新上一次左侧说话者
        if speaker_idx in (CHAR00_IDX, CHAR10_IDX):
            last_left_speaker = speaker_idx

        # ====================== 初始入场触发 =======================
        if flag == 0:
            left2_sprite_mover.trigger_enter()  # 10入场
            char4_sprite_mover.trigger_enter()  # 4入场
            flag = 1

        # ====================== 角色移动触发（基于全局变量）=======================
        # 1. 编号6（???）离场触发
        if current_line == trigger_indices["char6_leave"] and not char6_sprite_mover.leave_done:
            char6_sprite_mover.trigger_leave()

        # 2. 编号10（自机赤红）离场触发
        if current_line == trigger_indices["char10_leave"] and not left1_sprite_mover.leave_done:
            left1_sprite_mover.trigger_leave()

        if current_line == trigger_indices["char6_enter"] and not char6_sprite_mover.enter_done:
            char6_sprite_mover.trigger_enter()  # 6入场

        # 3. 编号4（敌方赤红）入场触发
        if current_line == trigger_indices["char4_enter"] and not char4_sprite_mover.enter_done:
            char4_sprite_mover.trigger_enter()

        # 4. 编号4（敌方赤红）离场触发（保留原有逻辑）
        if right_char_out_trigger in content and not char4_sprite_mover.leave_done:
            char4_sprite_mover.trigger_leave()

        # ====================== 移动状态更新 =======================
        left1_sprite_mover.update()
        left2_sprite_mover.update()
        char6_sprite_mover.update()
        char4_sprite_mover.update()

        # 主对话逻辑中「角色绘制」部分修改后的代码段（替换原绘制逻辑）
        # ====================== 角色绘制（修复亮态移动露底问题）=======================
        # 1. 初始化绘制标记（默认不绘制任何暗态）
        draw_char0_dark = False
        draw_char10_dark = False
        draw_char6_dark = False
        draw_char4_dark = False

        # 2. 根据当前说话者，标记需要绘制的暗态角色（仅非说话者绘制暗态）
        if speaker_idx != CHAR00_IDX and left1_sprite_mover.is_show:
            draw_char0_dark = True  # 非00说话，绘制00暗态
        if speaker_idx != CHAR10_IDX and left2_sprite_mover.is_show:
            draw_char10_dark = True  # 非10说话，绘制10暗态
        if speaker_idx != CHAR6_IDX and char6_sprite_mover.is_show:
            draw_char6_dark = True  # 非6说话，绘制6暗态
        if speaker_idx != CHAR4_IDX and char4_sprite_mover.is_show:
            draw_char4_dark = True  # 非4说话，绘制4暗态

        # 3. 绘制标记的暗态角色（无重叠，不会露底）
        if draw_char0_dark:
            screen.blit(char0_dark, (left1_sprite_mover.x, LEFT_CHAR1_POS[1]))
        if draw_char10_dark:
            screen.blit(char10_dark, (left2_sprite_mover.x, LEFT_CHAR2_POS[1]))
        if draw_char6_dark:
            screen.blit(char6_dark, (char6_sprite_mover.x, RIGHT_CHAR_POS_Y))
        if draw_char4_dark:
            screen.blit(char4_dark, (char4_sprite_mover.x, RIGHT_CHAR_POS_Y))

        # 4. 绘制当前说话角色亮态（覆盖暗态，无重叠）
        if speaker_idx == CHAR00_IDX and left1_sprite_mover.is_show:
            char0_speak_pos = (left1_sprite_mover.x, LEFT_CHAR1_POS[1] + LEFT_SPEAKER_OFFSET)
            screen.blit(char0_orig, char0_speak_pos)
        elif speaker_idx == CHAR10_IDX and left2_sprite_mover.is_show:
            char10_speak_pos = (left2_sprite_mover.x, LEFT_CHAR2_POS[1] + LEFT_SPEAKER_OFFSET)
            screen.blit(char10_orig, char10_speak_pos)
        elif speaker_idx == CHAR6_IDX and char6_sprite_mover.is_show:
            screen.blit(char6_orig, (char6_sprite_mover.x, RIGHT_CHAR_POS_Y))
        elif speaker_idx == CHAR4_IDX and char4_sprite_mover.is_show:
            screen.blit(char4_orig, (char4_sprite_mover.x, RIGHT_CHAR_POS_Y))

        # ====================== 界面元素绘制 =======================
        screen.blit(resources["talk_board"], (0, 0))  # 对话面板背景

        # 称号、BGM图片绘制
        if title_trigger in content and not title_img.has_shown:
            title_img.trigger_show()
        if bgm_trigger in content and not bgm_img.has_shown:
            bgm_img.trigger_show()
        title_img.update()
        bgm_img.update()
        title_img.draw(screen)
        bgm_img.draw(screen)

        # 绘制对话文字
        draw_dialog_box(screen, char_name, content, speaker_idx)

        screen.blit(resources["board"], (0, 0))  # 游戏面板前景
        pygame.display.flip()  # 更新屏幕
        clock.tick(60)  # 帧率限制

    # 退出程序
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()