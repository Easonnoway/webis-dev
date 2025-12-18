# validation/feedback_generator.py
from typing import Dict, List
from .base import RatingResult


class FeedbackGenerator:
    """根据PRRC评分结果生成精准优化建议"""

    # 基于PRRC评分标准的详细问题描述
    _dimension_descriptions = {
        "professionalism": {
            "name": "专业性",
            "level_1": "内容过于简单，类似儿童读物或日常对话，缺乏专业深度。",
            "level_2": "类似大众读物或科普文章，虽有专业内容但较为浅显。",
            "level_3": "中等专业水平，需要一定背景知识但不过于复杂。",
            "level_4": "学术论文或技术报告级别，需要相当的专业背景。",
            "level_5": "高度专业化的领域文献，需要深厚的专业知识。",
            "optimization_advice": "请明确要求抽取结果应体现原文的专业深度，确保关键专业术语、概念和深层次分析被准确提取。"
        },
        "readability": {
            "name": "可读性",
            "level_1": "存在严重的清晰度或连贯性问题，可能有大量语法错误。",
            "level_2": "基本可读但有明显问题，部分内容因语法或结构问题难以理解。",
            "level_3": "整体清晰但有轻微瑕疵，不影响整体理解。",
            "level_4": "非常清晰连贯，几乎没有错误。",
            "level_5": "表达出色，清晰有效地传达观点和细微差别。",
            "optimization_advice": "请在抽取Prompt中强调输出格式的清晰性，要求使用简洁明了的句子结构、恰当的标点，并避免复杂的嵌套表达。"
        },
        "reasoning": {
            "name": "推理性",
            "level_1": "只有单一因果关系或简单逻辑判断，缺乏深入分析。",
            "level_2": "有基础论证结构但分析较为表面。",
            "level_3": "包含多步骤推理，有一定分析深度。",
            "level_4": "多层逻辑推理和深入分析，涉及多方面考量。",
            "level_5": "需要跨学科综合判断的复杂推理和创新思考。",
            "optimization_advice": "请要求抽取结果体现逻辑推理链条，明确提取因果关系、对比分析、多因素影响等推理元素。"
        },
        "cleanliness": {
            "name": "清洁度",
            "level_1": "存在严重影响阅读流畅性的格式或内容问题。",
            "level_2": "有明显问题影响阅读，如格式混乱或无关内容。",
            "level_3": "有些问题但不严重影响阅读。",
            "level_4": "仅有微小瑕疵。",
            "level_5": "格式完美，内容纯净完整。",
            "optimization_advice": "请指定输出格式应规范化，要求去除无关字符、链接、广告等噪声，确保结构完整统一。"
        }
    }

    def generate_optimization_prompt(self,
                                     extraction_prompt: str,
                                     validation_results: Dict[str, RatingResult],
                                     original_goal: str,
                                     original_text_snippet: str = "") -> str:
        """
        基于验证结果生成精确的优化建议Prompt。

        Args:
            extraction_prompt: 原始抽取Prompt
            validation_results: 各维度评分结果
            original_goal: 用户原始目标
            original_text_snippet: 原始文本片段（用于上下文）
        """

        # 1. 分析问题和改进空间
        issues = self._analyze_specific_issues(validation_results)
        strengths = self._identify_strengths(validation_results)

        # 2. 生成针对性反馈
        detailed_feedback = self._generate_detailed_feedback(
            issues, strengths, validation_results
        )

        # 3. 构建优化Prompt
        optimization_prompt = self._build_refinement_prompt(
            original_prompt=extraction_prompt,
            original_goal=original_goal,
            detailed_feedback=detailed_feedback,
            text_context=original_text_snippet,
            scores=validation_results
        )

        return optimization_prompt

    def _analyze_specific_issues(self, results: Dict[str, RatingResult]) -> Dict[str, Dict]:
        """分析具体问题，基于分数级别"""
        issues = {}
        for dim, result in results.items():
            score = result.score
            if score < 3.0:  # 低分维度
                dim_info = self._dimension_descriptions.get(dim, {})
                issues[dim] = {
                    "score": score,
                    "level_desc": self._get_level_description(dim, score),
                    "specific_problem": self._identify_specific_problem(dim, score, result),
                    "optimization_hint": dim_info.get("optimization_advice", "")
                }
        return issues

    def _get_level_description(self, dimension: str, score: float) -> str:
        """根据分数获取级别描述"""
        dim_info = self._dimension_descriptions.get(dimension, {})

        if score <= 1.5:
            return dim_info.get("level_1", f"{score}/5: 严重不足")
        elif score <= 2.5:
            return dim_info.get("level_2", f"{score}/5: 明显不足")
        elif score <= 3.5:
            return dim_info.get("level_3", f"{score}/5: 中等水平")
        elif score <= 4.5:
            return dim_info.get("level_4", f"{score}/5: 良好")
        else:
            return dim_info.get("level_5", f"{score}/5: 优秀")

    def _identify_specific_problem(self, dimension: str, score: float, result: RatingResult) -> str:
        """识别具体问题"""
        problem_mapping = {
            "professionalism": {
                "low": ["内容过于浅显，缺乏专业术语", "未深入技术细节", "类似日常对话而非专业分析"],
                "medium": ["有一定专业性但深度不够", "关键概念解释不充分"],
                "high": ["专业内容表达准确", "技术细节充分"]
            },
            "readability": {
                "low": ["句子结构混乱", "标点使用不当", "术语堆砌影响理解"],
                "medium": ["部分句子冗长", "个别表达不够清晰"],
                "high": ["表达清晰流畅", "结构合理易懂"]
            },
            "reasoning": {
                "low": ["缺乏逻辑链条", "只有事实罗列没有分析", "结论缺乏支持"],
                "medium": ["有基本推理但不够深入", "论证过程不完整"],
                "high": ["逻辑推理清晰", "分析深入全面"]
            },
            "cleanliness": {
                "low": ["包含无关字符或格式噪声", "结构不完整", "有广告或链接残留"],
                "medium": ["有轻微格式问题", "部分内容不规整"],
                "high": ["格式规范统一", "内容纯净完整"]
            }
        }

        dim_problems = problem_mapping.get(dimension, {})
        if score < 2.5:
            problems = dim_problems.get("low", ["该维度评分较低"])
        elif score < 3.5:
            problems = dim_problems.get("medium", ["该维度有改进空间"])
        else:
            problems = dim_problems.get("high", ["该维度表现良好"])

        # 结合具体解释
        if result.explanation:
            return f"{problems[0]}（{result.explanation[:80]}...）"
        return problems[0]

    def _identify_strengths(self, results: Dict[str, RatingResult]) -> List[str]:
        """识别优势维度"""
        strengths = []
        for dim, result in results.items():
            if result.score >= 4.0:
                dim_name = self._dimension_descriptions.get(dim, {}).get("name", dim)
                strengths.append(f"{dim_name}表现良好（{result.score:.1f}/5）")
        return strengths

    def _generate_detailed_feedback(self, issues: Dict, strengths: List[str],
                                    results: Dict[str, RatingResult]) -> str:
        """生成详细反馈"""
        feedback_lines = ["# 抽取结果质量评估反馈"]

        # 整体评分摘要
        overall_score = sum(r.score for r in results.values()) / len(results) if results else 0
        feedback_lines.append(f"\n## 整体评分: {overall_score:.1f}/5")

        # 各维度详细评分
        feedback_lines.append("\n## 各维度评分详情:")
        for dim, result in results.items():
            dim_name = self._dimension_descriptions.get(dim, {}).get("name", dim)
            feedback_lines.append(f"- {dim_name}: {result.score:.1f}/5")
            if result.explanation:
                feedback_lines.append(f"  说明: {result.explanation[:100]}")

        # 主要问题
        if issues:
            feedback_lines.append("\n## 🚨 主要问题（需要优先改进）:")
            for dim, issue_info in issues.items():
                dim_name = self._dimension_descriptions.get(dim, {}).get("name", dim)
                feedback_lines.append(f"### {dim_name}（{issue_info['score']:.1f}/5）")
                feedback_lines.append(f"**问题描述**: {issue_info['level_desc']}")
                feedback_lines.append(f"**具体表现**: {issue_info['specific_problem']}")
                feedback_lines.append(f"**优化建议**: {issue_info['optimization_hint']}")

        # 表现良好维度
        if strengths:
            feedback_lines.append("\n## ✅ 表现良好的维度:")
            for strength in strengths:
                feedback_lines.append(f"- {strength}")

        # 综合改进建议
        if issues:
            feedback_lines.append("\n## 💡 综合改进方向:")
            issue_dims = list(issues.keys())
            if "readability" in issue_dims and "cleanliness" in issue_dims:
                feedback_lines.append("1. **优先解决格式和清晰度问题**：优化输出格式规范，确保内容清晰可读")
            if "professionalism" in issue_dims:
                feedback_lines.append("2. **增强专业深度**：确保关键专业概念和深度分析被准确提取")
            if "reasoning" in issue_dims:
                feedback_lines.append("3. **强化逻辑推理**：明确提取逻辑链条和论证过程")

        return "\n".join(feedback_lines)

    def _build_refinement_prompt(self, original_prompt: str, original_goal: str,
                                 detailed_feedback: str, text_context: str,
                                 scores: Dict[str, RatingResult]) -> str:
        """构建精炼Prompt"""
        # 各维度分数摘要
        score_summary = "，".join([
            f"{self._dimension_descriptions.get(dim, {}).get('name', dim)}:{res.score:.1f}"
            for dim, res in scores.items()
        ])

        refinement_template = """# Prompt优化任务

## 任务背景
你是一个专业的Prompt优化专家。现在需要对一个信息抽取任务的Prompt进行优化，以解决当前版本在特定维度上的质量问题。

## 原始信息
**用户目标**: {goal}

**原始文本特征**: {text_context}

**当前使用的抽取Prompt**:{prompt}

## 质量评估结果
**各维度得分**: {score_summary}

**详细评估反馈**:
{feedback}

## 优化要求
请基于以上评估反馈，对原始抽取Prompt进行优化。优化时需要：

1. **保持核心任务不变**：确保优化后的Prompt仍然能完成用户的原始目标
2. **针对性改进**：重点解决评估反馈中识别出的质量问题
3. **增强指导性**：让抽取指令更明确、更具体，减少歧义
4. **优化格式要求**：根据反馈调整输出格式的规范性要求
5. **平衡各维度**：在解决主要问题的同时，保持其他维度的表现

请输出优化后的完整抽取Prompt，不要添加任何额外的解释或说明。"""

        return refinement_template.format(
            goal=original_goal,
            text_context=text_context[:200] + "..." if len(text_context) > 200 else text_context,
            prompt=original_prompt,
            score_summary=score_summary,
            feedback=detailed_feedback
        )