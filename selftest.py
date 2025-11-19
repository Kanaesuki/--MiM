import pygame
import sys

# 初始化 Pygame
pygame.init()
pygame.mixer.init()      #作用：声音播放

# 屏幕设置
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("连缘无现里")
clock = pygame.time.Clock()

# 颜色定义
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 字体加载
dialogue_font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
dialogue_font = pygame.font.Font(dialogue_font_path, 15)  # 按需调整字号
name_font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
name_font = pygame.font.Font(name_font_path, 15)  # 按需调整字号

# 加载资源
def load_resource():
    resources = {}
    resources["background"] = pygame.image.load("background.png").convert_alpha()

    resources["talk_board"] = pygame.image.load("talk_board.png").convert_alpha()
    resources["talk_sound"] = pygame.mixer.Sound("talk_00.wav")

    resources["board"] = pygame.image.load("game_board_1.png").convert_alpha()

    return resources

resources = load_resource()

# 加载称号图片（假设路径为 "title.png"，需提前准备）
title_surface = pygame.image.load("title.png").convert_alpha()
title_rect = title_surface.get_rect(center=(290, 340))  # 特定显示位置

# 称号显示状态
title_visible = False    # 是否显示
title_alpha = 0          # 透明度（0-255，初始为0）
fade_speed = 5           # 透明度变化速度（入场+出场共用）
title_entering = False   # 入场中标记
title_showing = False    # 显示中标记（保持不透明）
title_duration = 1000    # 显示持续时间（毫秒，可选，默认1秒）
title_show_start_time = 0# 开始显示的时间戳



# 加载BGM图片（假设路径为 "bgm.png"，需提前准备）
bgm_surface = pygame.image.load("bgm.png").convert_alpha()
target_height = 20  # 目标高度（按需调整，如25、35）
original_width, original_height = bgm_surface.get_size()
target_width = int(original_width * (target_height / original_height))  # 按比例计算宽度
bgm_surface = pygame.transform.smoothscale(bgm_surface, (target_width, target_height))
bgm_rect = bgm_surface.get_rect(center=(230, 455))  # 特定显示位置


# bgm显示状态
bgm_visible = False      # 是否显示
bgm_alpha = 0            # 透明度（0-255，初始为0）
bgm_fade_speed = 5       # BGM透明度变化速度
bgm_entering = False     # BGM入场中标记
bgm_showing = False      # BGM显示中标记
bgm_duration = 1000      # BGM显示持续时间（毫秒）
bgm_show_start_time = 0  # BGM开始显示的时间戳

# 右侧角色移动相关（仅一次移动）
right_sprite_show = False  # 右侧角色是否显示
right_sprite_x = 550  # 初始位置（屏幕右侧外，不可见）
move_speed = 16  # 移动速度（像素/帧，越大越快）
move_done = False  # 移动完成标记（确保仅移动一次）
target_right_x = 200  # 角色最终目标X坐标（原230，保持不变）



# 解析对话文本
def parse_dialogue(file_path):
    dialogue = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip() # 去掉首尾空白字符
            if not line or line.startswith("9,"):  # 跳过空行和结束标记
                continue
            # 分割格式：角色索引,角色名,立绘编号,对话内容（忽略末尾逗号）
            parts = [p.strip() for p in line.split(",") if p.strip()]
            #line.split(",")：按逗号分割文本  将当前对话行按 , 拆分成列表
            #p.strip()：去除元素前后的空白字符
            if len(parts) >= 4:
                char_idx = int(parts[0])
                char_name = parts[1]
                sprite_idx = int(parts[2])
                content = ",".join(parts[3:])  # 处理对话内容含逗号的情况
                dialogue.append({
                    "char_idx": char_idx,
                    "char_name": char_name,
                    "sprite_idx": sprite_idx,
                    "content": content
                })
    return dialogue


# 加载角色立绘
def load_sprite(char_idx, sprite_idx):
    sprite_path = f"image/talk_{char_idx}_{sprite_idx:02d}.png"  # 立绘命名格式：talk_0_03.png
    sprite = pygame.image.load(sprite_path).convert_alpha()
    return sprite


def get_gray_sprite(sprite):
    """
    立绘变暗（类似正片叠底，保留色彩基调），透明区域不变
    :param sprite: 原始立绘 Surface（带 Alpha 通道）
    :return: 变暗后的立绘 Surface
    """
    # 创建与原始立绘完全一致的新 Surface（保留 Alpha 通道）
    dark_sprite = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    # 锁定 Surface 以提高像素操作效率
    dark_sprite.lock()
    sprite.lock()

    # 变暗参数（可调整）
    dark_factor = 0.05  # 变暗强度（0-1，越小越暗，推荐0.4-0.6）
    saturation_factor = 0.2  # 饱和度保留比例（0-1，1=原饱和度，推荐0.7-0.9）

    # 遍历每个像素的 x,y 坐标
    for x in range(sprite.get_width()):
        for y in range(sprite.get_height()):
            # 获取原始像素的 RGBA 值（r=红, g=绿, b=蓝, a=透明）
            r, g, b, a = sprite.get_at((x, y))
            if a > 10:  # 仅处理非透明像素（Alpha>10，避免边缘噪点）
                # 步骤1：计算原始亮度的灰度值
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                # 步骤2：按变暗强度降低亮度（正片叠底核心：保留亮度比例）
                dark_gray = int(gray * dark_factor)
                # 步骤3：计算原始颜色与暗化后灰度的混合（保留色彩，降低亮度）
                # 公式：新颜色 = 原始颜色 * 饱和度 + 暗化灰度 * (1-饱和度)
                new_r = int(r * saturation_factor + dark_gray * (1 - saturation_factor))
                new_g = int(g * saturation_factor + dark_gray * (1 - saturation_factor))
                new_b = int(b * saturation_factor + dark_gray * (1 - saturation_factor))
                # 步骤4：限制 RGB 值在 0-255 范围内（避免溢出）
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))
                # 保持 Alpha 不变，写入新颜色
                dark_sprite.set_at((x, y), (new_r, new_g, new_b, a))
            else:
                # 透明像素：直接复制原始 Alpha，RGB 设为黑色（不影响显示）
                dark_sprite.set_at((x, y), (0, 0, 0, a))

    # 解锁 Surface
    dark_sprite.unlock()
    sprite.unlock()
    return dark_sprite


def draw_dialog_box(screen, char_name, content, speaker_idx):
    # 绘制角色名字
    name_surf = name_font.render(f"{char_name}", True, (255, 255, 255))
    screen.blit(name_surf, (40, 370))

    # 绘制对话内容（中文自动换行：按单个字符拆分）
    text_color = CYAN if speaker_idx == 0 else RED
    line_height = 22  # 适配15号字体的行高（避免重叠）
    x, y = 40, 395
    current_line = ""  # 存储当前行的字符

    # 关键修改：按单个字符拆分中文（无需空格，直接遍历字符串）
    for char in content:
        # 1. 尝试将当前字符拼接到当前行
        test_line = current_line + char
        # 2. 虚拟渲染拼接后的行，获取实际宽度
        test_surf = dialogue_font.render(test_line, True, text_color)

        # 3. 校验：拼接后的行宽是否超出对话框限制（365px）
        if test_surf.get_width() < 365:
            # 3.1 没超出：更新当前行，继续拼接下一个字符
            current_line = test_line
        else:
            # 3.2 超出了：先绘制当前行，再换行
            surf = dialogue_font.render(current_line, True, text_color)
            screen.blit(surf, (x, y))
            y += line_height  # 换行：y坐标向下偏移
            current_line = char  # 新行从当前字符开始

    # 4. 绘制最后一行（循环结束后残留的字符）
    surf = dialogue_font.render(current_line, True, text_color)
    screen.blit(surf, (x, y))


# 主对话逻辑
def main():
    global title_visible, title_alpha, title_entering, title_showing, title_show_start_time
    global bgm_visible, bgm_alpha, bgm_entering, bgm_showing, bgm_show_start_time
    global right_sprite_show, right_sprite_x, move_done
    # 解析对话文件（请替换为你的对话文件路径）
    dialogue = parse_dialogue("talk_1_0_0.txt")

    current_line = 0  # 当前对话行索引
    char_sprites = {}  # 缓存已加载的立绘：key=(char_idx, sprite_idx), value=surface
    running = True

    while running:
        screen.blit(resources["background"], (0, 0))


        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # 按 Z 键切换下一句
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    # 播放音效
                    if resources["talk_sound"]:
                        resources["talk_sound"].play()
                    # 切换到下一句，超出范围则循环（可改为结束对话）
                    current_line = (current_line + 1) % len(dialogue)

        # 获取当前对话数据
        current = dialogue[current_line]
        speaker_idx = current["char_idx"]  # 正在说话的角色索引
        content = current["content"]




        # 角色0：左侧
        char0_sprite_key = (0, current["sprite_idx"] if current["char_idx"] == 0 else 0)
        if char0_sprite_key not in char_sprites:
            # 加载原始立绘后，直接生成对应的灰色立绘（缓存起来，避免重复计算）
            original_sprite = load_sprite(*char0_sprite_key)
            gray_sprite = get_gray_sprite(original_sprite)
            char_sprites[char0_sprite_key] = (original_sprite, gray_sprite)  # 缓存（原始+灰色）
        # 从缓存中获取立绘
        original_sprite0, gray_sprite0 = char_sprites[char0_sprite_key]
        if speaker_idx == 0:
            screen.blit(original_sprite0, (-15, 150))  # 说话者：显示原始立绘
        else:
            screen.blit(gray_sprite0, (-15, 150))  # 非说话者：显示灰色立绘

        # 角色1：右侧（修改后，添加移动逻辑）
        char1_sprite_key = (1, current["sprite_idx"] if current["char_idx"] == 1 else 0)
        if char1_sprite_key not in char_sprites:
            original_sprite = load_sprite(*char1_sprite_key)
            gray_sprite = get_gray_sprite(original_sprite)
            char_sprites[char1_sprite_key] = (original_sprite, gray_sprite)
        original_sprite1, gray_sprite1 = char_sprites[char1_sprite_key]

        # 关键：特定台词触发角色显示和移动（仅一次）
        # 触发条件：右侧角色的某句特定台词（如"我来晚了！"，需替换为你的实际台词）
        trigger_line = "什么嘛，原来是薮雨啊。"  # 替换为你要触发角色出现的台词
        if speaker_idx == 1 and trigger_line in content and not move_done:
            right_sprite_show = True  # 显示角色
            move_done = True  # 标记移动完成，避免重复触发

        # 移动逻辑（仅当角色显示且未到达目标位置时执行）
        if right_sprite_show and right_sprite_x > target_right_x:
            right_sprite_x -= move_speed  # 向左移动
        elif right_sprite_show and right_sprite_x <= target_right_x:
            right_sprite_x = target_right_x  # 锁定目标位置

        # 绘制右侧角色（根据显示状态和当前X坐标）
        if right_sprite_show:
            if speaker_idx == 1:
                # 说话者：绘制原始立绘
                screen.blit(original_sprite1, (right_sprite_x, 150))  # Y坐标仍为150
            else:
                # 非说话者：绘制变暗立绘
                screen.blit(gray_sprite1, (right_sprite_x, 150))

        screen.blit(resources["talk_board"], (0, 0))

        #称号
        # 触发条件：右侧角色（speaker_idx=1）讲特定台词（如"我乃乌蛇..."）
        if speaker_idx == 1 and "“什么嘛”是个什麽鬼啦。" in content and not title_visible:
            title_visible = True
            title_entering = True  # 标记为入场中
            title_alpha = 0  # 入场初始透明度0

        # 入场阶段：透明度从0递增到255
        if title_entering:
            title_alpha += fade_speed
            if title_alpha >= 255:
                title_alpha = 255
                title_entering = False  # 结束入场
                title_showing = True  # 标记为显示中
                title_show_start_time = pygame.time.get_ticks()  # 记录开始显示的时间

        # 显示阶段：保持透明度255，持续指定时间后启动出场
        if title_showing:
            current_time = pygame.time.get_ticks()
            # 持续时间到，启动出场
            if current_time - title_show_start_time >= title_duration:
                title_showing = False

        # 出场阶段：透明度从255递减到0
        if title_visible and not title_entering and not title_showing:
            title_alpha -= fade_speed
            if title_alpha <= 0:
                title_alpha = 0
                title_visible = False  # 完全隐藏

        # 绘制称号（入场/显示/出场阶段均绘制）
        if title_visible:
            temp_surf = pygame.Surface(title_surface.get_size(), pygame.SRCALPHA)
            temp_surf.blit(title_surface, (0, 0))
            temp_surf.fill((255, 255, 255, title_alpha), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(temp_surf, title_rect)




        #bmg
        if speaker_idx == 1 and "正是如此。" in content and not bgm_visible:
            bgm_visible = True
            bgm_entering = True  # 标记为入场中
            bgm_alpha = 0  # 入场初始透明度0

        # 入场阶段：透明度从0递增到255
        if bgm_entering:
            bgm_alpha += bgm_fade_speed
            if bgm_alpha >= 255:
                bgm_alpha = 255
                bgm_entering = False  # 结束入场
                bgm_showing = True  # 标记为显示中
                bgm_show_start_time = pygame.time.get_ticks()  # 记录开始显示的时间

        # 显示阶段：保持透明度255，持续指定时间后启动出场
        if bgm_showing:
            current_time = pygame.time.get_ticks()
            # 持续时间到，启动出场
            if current_time - bgm_show_start_time >= bgm_duration:
                bgm_showing = False

        # 出场阶段：透明度从255递减到0
        if bgm_visible and not bgm_entering and not bgm_showing:
            bgm_alpha -= bgm_fade_speed
            if bgm_alpha <= 0:
                bgm_alpha = 0
                bgm_visible = False  # 完全隐藏

        # 绘制BGM（入场/显示/出场阶段均绘制）
        if bgm_visible:
            bgm_surf_temp = pygame.Surface(bgm_surface.get_size(), pygame.SRCALPHA)
            bgm_surf_temp.blit(bgm_surface, (0, 0))
            bgm_surf_temp.fill((255, 255, 255, bgm_alpha), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(bgm_surf_temp, bgm_rect)


        draw_dialog_box(screen, current["char_name"], current["content"], current["char_idx"])

        screen.blit(resources["board"], (0, 0))

        # 更新屏幕
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()