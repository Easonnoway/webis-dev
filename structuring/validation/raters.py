"""基于Meta-rater论文逻辑的中文LLM评分器"""
import re
from typing import Dict, Any, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseRater, RatingResult, RaterRegistry


class MetaRaterChineseBase(BaseRater):
    """Meta-rater论文中文版评分器基类"""

    def _build_chain(self, system_prompt: str):
        """构建中文评估链"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "待评估文本：\n{text}")
        ])
        return prompt | self.llm | StrOutputParser()

    def _parse_meta_score(self, response: str, dimension_cn: str) -> Tuple[float, str]:
        """
        解析Meta-rater论文格式的中文评分响应。

        期望格式:
        "专业性: 4" 或 "可读性: 3"
        Cleanliness特殊格式: 四行分数
        """
        response = response.strip()

        # 尝试解析标准格式 "维度: 分数"
        pattern = rf"{dimension_cn}:\s*(\d+(\.\d+)?)"
        match = re.search(pattern, response)

        if match:
            try:
                score = float(match.group(1))
                # 确保分数在1-5范围内
                score = max(1.0, min(5.0, score))
                return score, response
            except ValueError:
                pass

        # 对于清洁度维度，有特殊的多行格式
        if dimension_cn == "清洁度":
            return self._parse_cleanliness_score_cn(response)

        # 后备方案：搜索数字
        numbers = re.findall(r'\b(\d+(\.\d+)?)\b', response)
        if numbers:
            try:
                for num_str, _ in numbers:
                    score = float(num_str)
                    if 1 <= score <= 5:
                        return score, response
            except ValueError:
                pass

        # 启发式回退
        if any(word in response for word in ['优秀', '卓越', '5', '五', '非常好']):
            return 4.5, response
        elif any(word in response for word in ['良好', '不错', '4', '四', '较好']):
            return 4.0, response
        elif any(word in response for word in ['一般', '中等', '3', '三', '普通']):
            return 3.0, response
        else:
            return 2.0, response

    def _parse_cleanliness_score_cn(self, response: str) -> Tuple[float, str]:
        """解析清洁度的特殊格式（中文版）"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]

        # 查找总体分数
        overall_match = re.search(r'清洁度:\s*(\d+(\.\d+)?)', response)
        if overall_match:
            try:
                overall = float(overall_match.group(1))
                return max(1.0, min(5.0, overall)), response
            except ValueError:
                pass

        # 尝试计算子分数的平均值
        sub_scores = []
        sub_score_patterns = [
            r'正确格式:\s*(\d+(\.\d+)?)',
            r'恰当内容:\s*(\d+(\.\d+)?)',
            r'内容完整:\s*(\d+(\.\d+)?)'
        ]

        for pattern in sub_score_patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    sub_scores.append(float(match.group(1)))
                except ValueError:
                    pass

        if sub_scores:
            avg_score = sum(sub_scores) / len(sub_scores)
            return max(1.0, min(5.0, avg_score)), response

        return 3.0, response


class ProfessionalismRaterCN(MetaRaterChineseBase):
    """专业性评估 - 中文版"""

    @property
    def description(self):
        return "评估文本的专业性程度（所需理解门槛和专业知识深度）"

    def rate(self, text: str) -> RatingResult:
        # 基于论文Prompt的中文版
        system_prompt = """【上下文】我是一名数据科学家，专注于研究从非结构化数据中提取高质量的结构化数据。

【目标】你是一名专家评估员。请评估以下文本的【专业性】，即理解该文本所需的知识深度和专业门槛，使用下面描述的累加5分制评分系统。你的评估应基于内容的深度、准确性和可理解性，不考虑写作风格、语法、拼写或标点。

评分标准（累加计分）：
- 加1分：如果文本相对简单，只需极少的技术知识或专业知识即可理解。文本可能包括儿歌、儿童读物或其他面向广大受众的基础内容。信息直截了当，不涉及复杂概念或专业主题。
- 再加1分：如果文本稍微复杂，可能需要基本的专业知识才能完全理解。例如大众读物、科普文章或小说。内容稍微深入，但仍对广大读者可及。
- 授予第三分：如果文本处于中等水平，需要一定程度的专业知识才能理解，但不过于复杂或专业。内容可能包括进阶书籍、详细文章或复杂主题的介绍。提供相当程度的深度和细节，但不需要深厚的学科背景。
- 授予第四分：如果文本复杂，需要相当程度的专业知识和技术理解。例如学术论文、高级教科书或详细技术报告。内容详细准确，但没有相关背景的读者可能难以理解。
- 授予第五分：如果文本专业性极高，需要高度的专业知识和前置知识。文本可能仅限于具有高级理解或该领域经验的人阅读，如高级学术论文、复杂技术手册或专利。内容深刻、准确且富有洞察力，但没有相当背景的读者基本无法理解。

以下三个方面不应影响你的判断：
(1) 文本使用的具体语言。
(2) 文本的长度。
(3) 出于数据隐私或安全考虑使用的占位符。

【风格】正式、清晰，包括分数和理由。
【语气】专业、客观、正式、清晰。
【受众】对大语言模型数据感兴趣的数据科学家和其他专业人士。

【要求】检查文本后，简要说明你的总分理由（不超过100字）。最后使用格式："专业性:总分"结束。"""

        chain = self._build_chain(system_prompt)

        try:
            response = chain.invoke({"text": text})
            score, full_response = self._parse_meta_score(response, "专业性")

            # 提取理由部分
            explanation = self._extract_explanation(full_response, "专业性")

            return RatingResult(
                score=score,
                explanation=explanation,
                confidence=0.9,
                metadata={
                    "raw_response": full_response,
                    "dimension": "professionalism"
                }
            )
        except Exception as e:
            print(f"专业性评估失败: {e}")
            return RatingResult(
                score=3.0,
                explanation=f"评估过程出错: {str(e)[:50]}",
                confidence=0.3
            )

    def _extract_explanation(self, response: str, dimension: str) -> str:
        """从响应中提取解释部分"""
        lines = response.split('\n')
        explanation_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith(dimension) and ':' not in line:
                explanation_lines.append(line)
            elif line.startswith(f"{dimension}:"):
                break

        explanation = ' '.join(explanation_lines)[:150]
        return explanation if explanation else "基于文本内容和评分标准进行评估"


class ReadabilityRaterCN(MetaRaterChineseBase):
    """可读性评估 - 中文版"""

    @property
    def description(self):
        return "评估文本的清晰度和易理解性"

    def rate(self, text: str) -> RatingResult:
        system_prompt = """【上下文】我是一名数据科学家，专注于研究从非结构化数据中提取高质量的结构化数据。

【目标】你是一名专家评估员。请评估以下文本的【可读性】，使用下面描述的累加5分制评分系统。

评分标准（累加计分）：
- 加1分：如果文本基本可读，但在清晰度或连贯性方面存在显著问题。可能包含需要高级阅读技能的复杂词汇或句子结构，或者存在大量语法和拼写错误。
- 再加1分：如果文本总体清晰连贯，但某些部分因偶尔的语法、拼写错误或复杂的句子结构而难以理解。
- 授予第三分：如果文本在大部分情况下清晰连贯，使用易于理解的恰当词汇和句子结构。可能仍存在轻微的语法或拼写问题。
- 授予第四分：如果文本非常清晰连贯，几乎没有或完全没有语法和拼写错误。文本使用正确的标点、词汇和易于跟进的句子结构。
- 授予第五分：如果文本在清晰度和连贯性方面表现卓越。它使用易于理解的语言和句子结构，同时有效传达观点和细微差别。允许存在轻微的语法、拼写和标点错误，但这些错误不应影响整体理解。

以下三个方面不应影响你的判断：
(1) 文本使用的具体语言。
(2) 文本的长度。
(3) 出于数据隐私或安全考虑使用的占位符。

【风格】正式、清晰，包括分数和理由。
【语气】专业、客观、正式、清晰。
【受众】对大语言模型数据感兴趣的数据科学家和其他专业人士。

【要求】检查文本后，简要说明你的总分理由（不超过100字）。最后使用格式："可读性:总分"结束。"""

        chain = self._build_chain(system_prompt)

        try:
            response = chain.invoke({"text": text})
            score, full_response = self._parse_meta_score(response, "可读性")

            explanation = self._extract_explanation(full_response, "可读性")

            return RatingResult(
                score=score,
                explanation=explanation,
                confidence=0.9,
                metadata={
                    "raw_response": full_response,
                    "dimension": "readability"
                }
            )
        except Exception as e:
            print(f"可读性评估失败: {e}")
            return RatingResult(
                score=3.0,
                explanation=f"评估过程出错: {str(e)[:50]}",
                confidence=0.3
            )

    def _extract_explanation(self, response: str, dimension: str) -> str:
        """从响应中提取解释部分"""
        lines = response.split('\n')
        explanation_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith(dimension) and ':' not in line:
                explanation_lines.append(line)
            elif line.startswith(f"{dimension}:"):
                break

        explanation = ' '.join(explanation_lines)[:150]
        return explanation if explanation else "基于文本内容和评分标准进行评估"


class ReasoningRaterCN(MetaRaterChineseBase):
    """推理性评估 - 中文版"""

    @property
    def description(self):
        return "评估文本的逻辑推理复杂度和深度"

    def rate(self, text: str) -> RatingResult:
        system_prompt = """【上下文】我是一名数据科学家，专注于研究从非结构化数据中提取高质量的结构化数据。

【目标】你是一名专家评估员。请评估以下文本的【推理性】，使用下面描述的累加5分制评分系统。

评分标准（累加计分）：
- 加1分：如果内容包含初步推理要素，可能涉及单一的因果关系或简单逻辑判断，但缺乏深入分析（例如，提出观点但没有支持证据或详细解释）。
- 再加1分：如果内容展示了基本的推理能力，包含一些需要读者进行一定程度思考的逻辑关系。这可能涉及简单的论证结构或例子，但分析仍较表面（例如，提出问题和直接解决方案并附带一些例子，但缺乏深度）。
- 授予第三分：如果内容展现出良好的推理复杂度，涉及多个推理步骤，需要读者进行更复杂的思考。读者应能识别出几个相互关联的论点，并可能包含一定深度的分析（例如，分析不同因素如何影响结果或比较各种观点）。
- 授予第四分：如果内容具有高度的推理复杂度，包括多层逻辑推理和深入分析。读者需要进行复杂思考，并能识别多个相互关联的论点，同时进行综合评估（例如，分析多个变量或评估不同解决方案的优缺点）。
- 授予第五分：如果内容在推理复杂度方面表现卓越，要求读者进行深入分析和创新思考。推理过程复杂且多维，涉及跨学科知识，要求读者整合各种信息以做出全面判断（例如，讨论复杂的数学模型、设计优化算法或进行高层战略思考）。

以下三个方面不应影响你的判断：
(1) 文本使用的具体语言。
(2) 文本的长度。
(3) 出于数据隐私或安全考虑使用的占位符。

【风格】正式、清晰，包括分数和理由。
【语气】专业、客观、正式、清晰。
【受众】对大语言模型数据感兴趣的数据科学家和其他专业人士。

【要求】检查文本后，简要说明你的总分理由（不超过100字）。最后使用格式："推理性:总分"结束。"""

        chain = self._build_chain(system_prompt)

        try:
            response = chain.invoke({"text": text})
            score, full_response = self._parse_meta_score(response, "推理性")

            explanation = self._extract_explanation(full_response, "推理性")

            return RatingResult(
                score=score,
                explanation=explanation,
                confidence=0.85,
                metadata={
                    "raw_response": full_response,
                    "dimension": "reasoning"
                }
            )
        except Exception as e:
            print(f"推理性评估失败: {e}")
            return RatingResult(
                score=2.5,
                explanation=f"评估过程出错: {str(e)[:50]}",
                confidence=0.3
            )

    def _extract_explanation(self, response: str, dimension: str) -> str:
        """从响应中提取解释部分"""
        lines = response.split('\n')
        explanation_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith(dimension) and ':' not in line:
                explanation_lines.append(line)
            elif line.startswith(f"{dimension}:"):
                break

        explanation = ' '.join(explanation_lines)[:150]
        return explanation if explanation else "基于文本内容和评分标准进行评估"


class CleanlinessRaterCN(MetaRaterChineseBase):
    """清洁度评估 - 中文版"""

    @property
    def description(self):
        return "评估文本的格式规范性和内容纯净度"

    def rate(self, text: str) -> RatingResult:
        system_prompt = """【上下文】我是一名数据科学家，专注于研究从非结构化数据中提取高质量的结构化数据。

【目标】你是一名专家评估员。请评估以下文本的【清洁度】，使用下面描述的累加5分制评分系统。

评分标准（累加计分）：
- 1分：表示存在严重影响阅读流畅性的问题。
- 2分：表示文本存在明显影响阅读流畅性的问题。
- 3分：表示文本存在一些问题，但不严重影响阅读流畅性。
- 4分：表示文本存在微小问题，但不影响阅读。
- 5分：表示文本在所有标准上都是完美的。

高清洁度由以下四个标准定义，请为每个标准按5分制评分：
- 正确格式：文本应看起来是人工编辑的，而非机器提取的，没有不恰当的字符。
- 恰当内容：文本不应包含链接、广告或其他影响阅读的无关文字。文本的有效内容足够长，能够提取出清晰的结构和主题。
- 内容完整：文章主体由人工自然书写的完整句子组成，而非短语和列表，包含观点、事实或故事。

然而，如果末尾有$TRUNCATED$符号，应将其视为作者设置的手动文章结束标志，无需考虑完整性。

以下三个方面不应影响你的判断：
(1) 文本使用的具体语言。
(2) 文本的长度。
(3) 出于数据隐私或安全考虑使用的占位符。

【风格】正式、清晰，包括分数和理由。
【语气】专业、客观、正式、清晰。
【受众】对大语言模型数据感兴趣的数据科学家和其他专业人士。

【要求】检查文本后，简要说明你的总分理由（不超过100字）。最后使用以下格式输出：
清洁度: 总分
正确格式: 正确格式分数
恰当内容: 恰当内容分数
内容完整: 内容完整分数"""

        chain = self._build_chain(system_prompt)

        try:
            response = chain.invoke({"text": text})
            score, full_response = self._parse_meta_score(response, "清洁度")

            # 为清洁度生成更详细的解释
            explanation = self._generate_cleanliness_explanation(full_response)

            return RatingResult(
                score=score,
                explanation=explanation,
                confidence=0.9,
                metadata={
                    "raw_response": full_response,
                    "dimension": "cleanliness",
                    "sub_scores": self._extract_cleanliness_sub_scores(full_response)
                }
            )
        except Exception as e:
            print(f"清洁度评估失败: {e}")
            return RatingResult(
                score=3.0,
                explanation=f"评估过程出错: {str(e)[:50]}",
                confidence=0.3
            )

    def _generate_cleanliness_explanation(self, response: str) -> str:
        """为清洁度生成详细的解释"""
        lines = response.split('\n')

        sub_scores = {}
        for line in lines:
            line = line.strip()
            if '正确格式:' in line:
                match = re.search(r'正确格式:\s*(\d+(\.\d+)?)', line)
                if match:
                    sub_scores['format'] = float(match.group(1))
            elif '恰当内容:' in line:
                match = re.search(r'恰当内容:\s*(\d+(\.\d+)?)', line)
                if match:
                    sub_scores['content'] = float(match.group(1))
            elif '内容完整:' in line:
                match = re.search(r'内容完整:\s*(\d+(\.\d+)?)', line)
                if match:
                    sub_scores['completeness'] = float(match.group(1))

        if sub_scores:
            issues = []
            for key, score in sub_scores.items():
                if score < 3.0:
                    if key == 'format':
                        issues.append('格式问题')
                    elif key == 'content':
                        issues.append('无关内容')
                    elif key == 'completeness':
                        issues.append('内容不完整')

            if issues:
                return f"存在{''.join(issues)}，建议优化"
            else:
                return "格式规范，内容恰当且完整"

        return "基于清洁度标准进行评估"

    def _extract_cleanliness_sub_scores(self, response: str) -> Dict[str, float]:
        """提取清洁度的子分数"""
        sub_scores = {}
        patterns = [
            (r'正确格式:\s*(\d+(\.\d+)?)', 'format'),
            (r'恰当内容:\s*(\d+(\.\d+)?)', 'content'),
            (r'内容完整:\s*(\d+(\.\d+)?)', 'completeness')
        ]

        for pattern, key in patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    sub_scores[key] = float(match.group(1))
                except ValueError:
                    pass

        return sub_scores

