import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self._setup_fonts()
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='SimHei'
        )
        
        # 段落标题样式
        self.part_title_style = ParagraphStyle(
            'PartTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkgreen,
            fontName='SimHei'
        )
        
        # 正文样式
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='SimHei',
            leading=20
        )
    
    def _setup_fonts(self):
        """设置中文字体支持"""
        try:
            # 尝试注册中文字体，如果系统中有的话
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
                "C:/Windows/Fonts/simsun.ttc",  # Windows 宋体
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    if "simhei" in font_path.lower():
                        pdfmetrics.registerFont(TTFont('SimHei', font_path))
                        logger.info(f"成功注册字体: {font_path}")
                        break
                    elif "simsun" in font_path.lower():
                        pdfmetrics.registerFont(TTFont('SimSun', font_path))
                        logger.info(f"成功注册字体: {font_path}")
                        break
        except Exception as e:
            logger.warning(f"字体注册失败: {e}")
            # 使用默认字体
            pass
    
    def create_story_pdf(self, story_data, output_path=None):
        """
        创建故事PDF，每一段合成一页
        
        Args:
            story_data: 故事数据结构
            output_path: 输出PDF路径，如果为None则自动生成
            
        Returns:
            str: 生成的PDF文件路径
        """
        if not story_data:
            logger.error("没有故事数据")
            return None
        
        title = story_data.get("title", "未命名故事")
        story_parts = story_data.get("story_parts", [])
        
        if not story_parts:
            logger.error("故事段落为空")
            return None
        
        # 确定输出路径
        if output_path is None:
            base_path = "books"
            book_folder = os.path.join(base_path, title)
            output_path = os.path.join(book_folder, f"{title}.pdf")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story_elements = []
            
            # 添加封面页
            story_elements.extend(self._create_cover_page(title))
            story_elements.append(PageBreak())
            
            # 为每个段落创建页面
            for part in story_parts:
                part_elements = self._create_part_page(part, title)
                story_elements.extend(part_elements)
                story_elements.append(PageBreak())
            
            # 构建PDF
            doc.build(story_elements)
            logger.info(f"PDF生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            return None
    
    def _create_cover_page(self, title):
        """创建封面页"""
        elements = []
        
        # 添加标题
        title_para = Paragraph(title, self.title_style)
        elements.append(title_para)
        
        # 添加装饰性元素
        elements.append(Spacer(1, 2*inch))
        
        # 可以在这里添加更多封面元素，如图片、作者信息等
        
        return elements
    
    def _create_part_page(self, part, book_title):
        """为每个段落创建页面"""
        elements = []
        
        part_number = part.get("part_number", 1)
        content = part.get("content", "")
        t2i_prompt = part.get("t2i_prompt", "")
        
        # 添加段落标题
        part_title = f"第{part_number}段"
        part_title_para = Paragraph(part_title, self.part_title_style)
        elements.append(part_title_para)
        
        # 添加段落内容
        if content:
            content_para = Paragraph(content, self.body_style)
            elements.append(content_para)
            elements.append(Spacer(1, 0.5*inch))
        
        # 添加对应的图片
        image_path = self._find_part_image(book_title, part_number)
        if image_path and os.path.exists(image_path):
            try:
                # 计算图片尺寸，确保适合页面
                img = Image(image_path)
                # 设置图片最大尺寸为页面宽度的80%
                max_width = A4[0] * 0.8
                max_height = A4[1] * 0.4
                
                # 保持宽高比缩放图片
                img.drawWidth = min(img.drawWidth, max_width)
                img.drawHeight = min(img.drawHeight, max_height)
                
                # 居中显示图片
                img.hAlign = 'CENTER'
                elements.append(img)
                logger.info(f"成功添加图片: {image_path}")
            except Exception as e:
                logger.warning(f"添加图片失败: {e}")
        else:
            logger.warning(f"未找到段落 {part_number} 的图片: {image_path}")
        
        return elements
    
    def _find_part_image(self, book_title, part_number):
        """查找段落对应的图片文件"""
        base_path = "books"
        book_folder = os.path.join(base_path, book_title)
        
        # 可能的图片文件名模式
        image_patterns = [
            f"image_{part_number}.png",
            f"image_{part_number}.jpg",
            f"image_{part_number}.jpeg",
            f"part{part_number}.png",
            f"part{part_number}.jpg",
            f"part{part_number}.jpeg"
        ]
        
        for pattern in image_patterns:
            image_path = os.path.join(book_folder, pattern)
            if os.path.exists(image_path):
                return image_path
        
        return None

def process_story_for_pdf(story_data):
    """
    处理故事数据并生成PDF
    
    Args:
        story_data: 故事数据结构
        
    Returns:
        bool: 是否成功生成PDF
    """
    try:
        generator = PDFGenerator()
        pdf_path = generator.create_story_pdf(story_data)
        
        if pdf_path:
            print(f"✅ PDF生成成功: {pdf_path}")
            return True
        else:
            print("❌ PDF生成失败")
            return False
            
    except Exception as e:
        print(f"❌ PDF生成过程中出错: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    test_story = {
  "title": "壮壮的奇幻冒险",
  "story_parts": [
    {
      "part_number": 1,
      "content": "在一个氤氲的清晨，壮壮背着书包走在森林小路上。突然，他听到一阵欢声笑语，原来是一只叫吱吱的小鸟在树枝上唱歌。吱吱邀请壮壮一起冒险，壮壮兴奋地答应了。",
      "t2i_prompt": "一个阳光透过树叶的森林，小男孩壮壮仰头看着树枝上的小鸟吱吱。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 2,
      "content": "壮壮和吱吱来到一片神秘的花园，花园里开满了五颜六色的花朵。吱吱告诉壮壮，花园里藏着一颗能实现愿望的宝石，但只有诚实的人才能找到它。",
      "t2i_prompt": "小男孩和小鸟站在满是鲜花的奇幻花园中，远处有一道神秘的光芒。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 3,
      "content": "壮壮迫不及待地跑进花园，但他不小心踩坏了一朵小花。吱吱提醒他要诚实守信，壮壮羞愧地低下头，决定向花园道歉。",
      "t2i_prompt": "小男孩低头看着被踩坏的小花，小鸟站在他肩膀上安慰他。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 4,
      "content": "壮壮真诚地向花园道歉，突然，一朵更大的花在他面前绽放，花蕊中躺着一颗闪闪发光的宝石。吱吱高兴地说：“你的诚实打动了花园！”",
      "t2i_prompt": "小男孩和小鸟站在一朵巨大的花前，花蕊中有一颗发光的宝石。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 5,
      "content": "壮壮拿起宝石，许愿让花园恢复原样。瞬间，花园变得更加美丽，花朵们欢快地摇曳着。吱吱笑着说：“诚实的力量真神奇！”",
      "t2i_prompt": "小男孩举起宝石，花园里的花朵重新绽放，小鸟在一旁飞舞。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 6,
      "content": "回家的路上，壮壮遇到了一只迷路的小兔子。他想起吱吱的话，决定帮助小兔子找到家。吱吱赞许地点点头。",
      "t2i_prompt": "小男孩和小鸟蹲在迷路的小兔子旁边，森林背景温馨。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 7,
      "content": "壮壮和吱吱带着小兔子穿过森林，终于找到了它的家。兔妈妈感激地送给他们一篮子胡萝卜。壮壮开心地说：“帮助别人真快乐！”",
      "t2i_prompt": "小男孩和小鸟站在兔子洞前，兔妈妈递给他们一篮子胡萝卜。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 8,
      "content": "第二天，壮壮在学校里发现同桌的小明偷拿了别人的铅笔。他想起自己的经历，决定劝小明痛改前非。",
      "t2i_prompt": "小男孩在教室里，严肃地对另一个小男孩说话，小鸟停在窗台上。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 9,
      "content": "小明起初不以为然，但壮壮耐心地告诉他诚实的重要性。小明终于承认错误，归还了铅笔。老师表扬了他们。",
      "t2i_prompt": "两个小男孩在教室里握手言和，老师微笑着看着他们。",
      "width": 800,
      "height": 600
    },
    {
      "part_number": 10,
      "content": "晚上，壮壮躺在床上，回想这一天的冒险。吱吱飞进窗口，对他说：“诚实守信会让你拥有更多朋友。”壮壮微笑着进入了梦乡。",
      "t2i_prompt": "小男孩躺在床上，小鸟停在窗台上，月光洒进房间。",
      "width": 800,
      "height": 600
    }
  ]
}
    
    success = process_story_for_pdf(test_story)
    print(f"测试结果: {'成功' if success else '失败'}")
