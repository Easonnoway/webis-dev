"""Validation manager for coordinating multiple raters."""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import json
from datetime import datetime

from .base import RaterRegistry, BaseRater, RatingResult
from .feedback_generator import FeedbackGenerator
from .raters import ProfessionalismRaterCN, ReadabilityRaterCN, ReasoningRaterCN, CleanlinessRaterCN


@dataclass
class ValidationResult:
    """完整的验证结果"""
    passed: bool
    overall_score: float
    rater_results: Dict[str, RatingResult]  # 各评分器结果
    feedback: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ValidationManager:
    """验证管理器：协调多个评分器，支持配置和扩展"""

    def __init__(self, llm=None, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.raters: Dict[str, BaseRater] = {}
        self.history: List[Dict] = []  # 用于自回归学习

        # 初始化评分器
        self._initialize_raters()

    def _initialize_raters(self):
        """根据配置初始化评分器"""
        # ========== 注册中文评分器 ==========
        RaterRegistry.register("professionalism_cn", ProfessionalismRaterCN)
        RaterRegistry.register("readability_cn", ReadabilityRaterCN)
        RaterRegistry.register("reasoning_cn", ReasoningRaterCN)
        RaterRegistry.register("cleanliness_cn", CleanlinessRaterCN)
        # 默认配置：只启用规则类评分器（适合日常业务）
        default_config = {
            "enabled_raters": ["readability_cn", "cleanliness_cn"],
            "weights": {  # 各评分器权重
                "readability": 0.5,
                "cleanliness": 0.5,
                "professionalism": 0.0,
                "reasoning": 0.0,
                "grammar": 0.0
            },
            "thresholds": {  # 各评分器通过阈值
                "readability": 3.0,
                "cleanliness": 3.0,
                "professionalism": 3.0,
                "reasoning": 3.0,
                "grammar": 3.0
            },
            "overall_threshold": 3.0,  # 综合通过阈值
            "mode": "default"  # default|all|custom
        }

        # 合并配置
        self.config = {**default_config, **self.config}

        # 根据模式确定启用的评分器
        if self.config["mode"] == "all":
            enabled = RaterRegistry.list_raters().keys()
        elif self.config["mode"] == "custom" and "custom_raters" in self.config:
            enabled = self.config["custom_raters"]
        else:
            enabled = self.config["enabled_raters"]

        # 创建评分器实例
        for rater_name in enabled:
            try:
                self.raters[rater_name] = RaterRegistry.create_rater(
                    rater_name, self.llm
                )
            except ValueError as e:
                print(f"警告：无法创建评分器 '{rater_name}': {e}")
                return -1

    def validate(self, text: str) -> ValidationResult:
        """执行验证"""
        rater_results = {}

        # 并行执行所有评分器
        for name, rater in self.raters.items():
            try:
                result = rater.rate(text)
                rater_results[name] = result
            except Exception as e:
                print(f"评分器 '{name}' 执行失败: {e}")
                rater_results[name] = RatingResult(
                    score=1.0,  # 失败给最低分
                    explanation=f"评分器执行失败: {str(e)[:50]}"
                )

        # 计算加权综合得分
        overall_score = self._calculate_overall_score(rater_results)

        # 检查是否通过
        passed = self._check_passing(rater_results, overall_score)

        # 生成反馈
        feedback = self._generate_feedback(rater_results, overall_score, passed)

        return ValidationResult(
            passed=passed,
            overall_score=overall_score,
            rater_results=rater_results,
            feedback=feedback,
            metadata={
                "enabled_raters": list(self.raters.keys()),
                "config": self.config
            }
        )

    def _calculate_overall_score(self, results: Dict[str, RatingResult]) -> float:
        """计算加权综合得分"""
        if not results:
            return 0.0

        total_weight = 0
        weighted_sum = 0

        for name, result in results.items():
            weight = self.config.get("weights", {}).get(name, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _check_passing(self, results: Dict[str, RatingResult], overall_score: float) -> bool:
        """检查是否通过验证"""
        # 检查综合阈值
        if overall_score < self.config.get("overall_threshold", 3.0):
            return False

        # 检查各评分器阈值
        thresholds = self.config.get("thresholds", {})
        for name, result in results.items():
            threshold = thresholds.get(name, 3.0)
            if result.score < threshold:
                return False

        return True

    def _generate_feedback(self, results: Dict[str, RatingResult],
                           overall_score: float, passed: bool) -> str:
        """生成反馈报告"""
        feedback_parts = []

        # 各维度得分
        for name, result in results.items():
            # 翻译名称
            name_cn = {
                "readability": "可读性",
                "cleanliness": "清洁度",
                "professionalism": "专业性",
                "reasoning": "推理性",
                "grammar": "语法"
            }.get(name, name)

            weight = self.config.get("weights", {}).get(name, 1.0)
            feedback_parts.append(f"{name_cn}: {result.score:.1f}/5 (权重:{weight:.1f})")
            if result.explanation:
                feedback_parts.append(f"  说明: {result.explanation}")

        # 综合信息
        feedback_parts.append(f"\n综合得分: {overall_score:.2f}/5")
        feedback_parts.append(f"通过阈值: {self.config.get('overall_threshold', 3.0)}/5")

        # 结论
        if passed:
            feedback_parts.append("\n✅ 验证通过！文本质量符合要求。")
        else:
            feedback_parts.append("\n❌ 验证未通过！建议优化文本质量。")


        return "\n".join(feedback_parts)


    def list_available_raters(self) -> Dict:
        """列出所有可用评分器"""
        return RaterRegistry.list_raters()


class EnhancedValidationManager(ValidationManager):
    """增强的验证管理器，支持自回归优化循环"""

    def __init__(self, llm=None, config=None):
        super().__init__(llm, config)
        self.feedback_gen = FeedbackGenerator()
        self.optimization_history = []  # 记录优化历史

    def run_validation_loop(self,
                            initial_prompt: str,
                            initial_result: str,
                            original_text: Union[str, List[str]],
                            original_goal: str,
                            max_retries: int = 3,
                            prompt_agent=None,
                            extraction_agent=None,
                            output_format=None
                            ) -> Dict:
        """
        执行完整的验证-优化循环。

        Args:
            initial_prompt: 初始抽取Prompt
            initial_result: 初始提取结果
            original_text: 原始文本
            original_goal: 用户原始目标
            max_retries: 最大优化重试次数
            prompt_agent: PromptBuilderAgent实例（用于重新生成Prompt）
            extract_agent: 用于重新提取文本
        """
        current_prompt = initial_prompt
        current_result = initial_result
        loop_history = []

        for attempt in range(max_retries):
            print(f"\n{'=' * 60}")
            print(f"自回归优化循环 - 第 {attempt + 1} 轮")
            print(f"{'=' * 60}")

            # 1. 验证当前结果
            validation_result = self.validate(current_result)
            loop_history.append({
                "attempt": attempt,
                "prompt": current_prompt[:200] + "..." if len(current_prompt) > 200 else current_prompt,
                "validation": validation_result
            })

            print(f"当前质量得分: {validation_result.overall_score:.2f}/5")
            print(f"是否通过: {'✅' if validation_result.passed else '❌'}")

            # 2. 如果通过或达到最大重试，结束循环
            if validation_result.passed or attempt == max_retries - 1:
                print(f"\n循环结束。最终状态: {'通过' if validation_result.passed else '未通过'}")
                return {
                    "final_result": current_result,
                    "final_prompt": current_prompt,
                    "passed": validation_result.passed,
                    "final_score": validation_result.overall_score,
                    "history": loop_history,
                    "optimization_count": attempt
                }

            # 3. 生成优化建议
            optimization_prompt = self.feedback_gen.generate_optimization_prompt(
                current_prompt,
                validation_result.rater_results,
                original_goal
            )

            if not optimization_prompt:
                print("未生成优化建议，循环终止。")
                break

            # 4. 使用prompt_agent重新生成抽取Prompt
            if prompt_agent:
                print("\n正在优化抽取Prompt...")
                try:
                    # 这里需要根据你的PromptBuilderAgent的实际接口调整
                    # 假设prompt_agent有一个refine方法
                    new_prompt = prompt_agent.refine(
                        original_prompt=current_prompt,
                        feedback=optimization_prompt
                    )
                    current_prompt = new_prompt
                    print("Prompt优化完成。")

                    # 记录优化历史
                    self.optimization_history.append({
                        "from_prompt": current_prompt,
                        "to_prompt": new_prompt,
                        "reason": validation_result.feedback,
                        "scores": {k: v.score for k, v in validation_result.rater_results.items()}
                    })

                except Exception as e:
                    print(f"Prompt优化失败: {e}")
                    # 如果prompt_agent没有refine方法，我们可以直接使用LLM优化
                    current_prompt = self._optimize_with_llm(optimization_prompt)
            else:
                # 直接使用LLM优化Prompt
                current_prompt = self._optimize_with_llm(optimization_prompt)

            print(f"\n优化后的Prompt:\n{current_prompt}...")

            # 5. 这里应该调用你的提取流程重新提取
            # 注意：在实际集成中，你需要在这里触发重新提取
            new_extraction = extraction_agent.extract(prompt=current_prompt, text=original_text, output_format=output_format)
            # print("提示：此处应触发重新提取流程。")
            # 下一轮 validate 期望字符串，因此这里保存为文本（JSON 时保存 raw 文本也可）
            current_result = new_extraction.raw if hasattr(new_extraction, "raw") else str(new_extraction)

        return {"final_result": current_result,
                "history": loop_history,
                'passed': validation_result.passed,
                }

    def _optimize_with_llm(self, optimization_prompt: str) -> str:
        """直接使用LLM优化Prompt（备选方案）"""
        if not self.llm:
            raise ValueError("LLM未初始化，无法优化Prompt")

        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "你是一名Prompt优化专家。请根据用户的要求优化原有的抽取Prompt。"),
            ("human", "{optimization_request}")
        ])

        chain = prompt_template | self.llm | StrOutputParser()
        return chain.invoke({"optimization_request": optimization_prompt})


# 快速使用函数
def create_validator(llm=None, config_file: Optional[str] = None,
                     config_dict: Optional[Dict] = None) -> ValidationManager:
    """创建验证管理器（支持配置文件）"""
    config = {}

    # 从文件加载配置
    if config_file:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"警告：无法加载配置文件 {config_file}: {e}")

    # 合并字典配置
    if config_dict:
        config = {**config, **config_dict}

    return ValidationManager(llm, config)
