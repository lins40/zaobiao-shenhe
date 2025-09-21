"""
DeepSeek API客户端封装
提供AI大模型服务，支持文本分析、实体识别、规则提取等功能
"""
import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


@dataclass
class DeepSeekResponse:
    """DeepSeek API响应数据结构"""
    success: bool
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    error_message: Optional[str] = None


class RateLimiter:
    """API调用频率限制器"""
    
    def __init__(self, max_calls: int = 60, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """获取调用许可"""
        now = time.time()
        # 清理过期的调用记录
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.calls.append(now)


class CircuitBreaker:
    """熔断器 - 防止API服务异常时的级联故障"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """检查熔断器是否打开"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        """记录成功调用"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """记录失败调用"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.deepseek_model
        self.max_retries = 3
        self.timeout = 30
        
        # 初始化限流器和熔断器
        self.rate_limiter = RateLimiter(max_calls=50, time_window=60)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        # HTTP客户端配置
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def _make_request(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> DeepSeekResponse:
        """发送API请求"""
        # 检查熔断器状态
        if self.circuit_breaker.is_open():
            return DeepSeekResponse(
                success=False,
                content="",
                usage={},
                model=self.model,
                finish_reason="circuit_breaker_open",
                error_message="服务熔断器已打开，请稍后重试"
            )
        
        # 限流控制
        await self.rate_limiter.acquire()
        
        request_data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.circuit_breaker.record_success()
                    
                    return DeepSeekResponse(
                        success=True,
                        content=data["choices"][0]["message"]["content"],
                        usage=data.get("usage", {}),
                        model=data.get("model", self.model),
                        finish_reason=data["choices"][0]["finish_reason"]
                    )
                
                elif response.status_code == 429:  # 限流
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                
                else:
                    error_msg = f"API请求失败: {response.status_code} - {response.text}"
                    if attempt == self.max_retries - 1:
                        self.circuit_breaker.record_failure()
                        return DeepSeekResponse(
                            success=False,
                            content="",
                            usage={},
                            model=self.model,
                            finish_reason="error",
                            error_message=error_msg
                        )
            
            except httpx.TimeoutException:
                error_msg = f"API请求超时 (attempt {attempt + 1})"
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    return DeepSeekResponse(
                        success=False,
                        content="",
                        usage={},
                        model=self.model,
                        finish_reason="timeout",
                        error_message=error_msg
                    )
                await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                error_msg = f"API请求异常: {str(e)}"
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    return DeepSeekResponse(
                        success=False,
                        content="",
                        usage={},
                        model=self.model,
                        finish_reason="error",
                        error_message=error_msg
                    )
                await asyncio.sleep(2 ** attempt)
    
    async def analyze_document_compliance(self, document_content: str, rules: List[str]) -> DeepSeekResponse:
        """分析文档合规性"""
        system_prompt = """你是一个专业的招标投标合规性审查专家。请根据给定的规则，对文档内容进行详细的合规性分析。

请按以下格式输出分析结果：
{
    "overall_score": 85,
    "risk_level": "medium",
    "compliance_issues": [
        {
            "rule": "规则名称",
            "issue": "具体问题描述",
            "severity": "high/medium/low",
            "suggestion": "改进建议"
        }
    ],
    "summary": "总体分析总结"
}"""
        
        user_prompt = f"""
请分析以下文档的合规性：

文档内容：
{document_content}

适用规则：
{chr(10).join(f"- {rule}" for rule in rules)}

请提供详细的合规性分析报告。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages, temperature=0.3, max_tokens=3000)
    
    async def extract_entities(self, text: str, entity_types: List[str]) -> DeepSeekResponse:
        """从文本中提取实体"""
        system_prompt = """你是一个专业的文本实体识别专家。请从给定文本中识别和提取指定类型的实体。

请按以下JSON格式输出：
{
    "entities": [
        {
            "text": "实体文本",
            "type": "实体类型",
            "start": 起始位置,
            "end": 结束位置,
            "confidence": 0.95
        }
    ]
}"""
        
        user_prompt = f"""
请从以下文本中提取实体：

文本内容：
{text}

需要提取的实体类型：
{', '.join(entity_types)}

请识别并提取所有相关实体。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages, temperature=0.2)
    
    async def extract_rules_from_regulation(self, regulation_text: str) -> DeepSeekResponse:
        """从法规文本中提取规则"""
        system_prompt = """你是一个专业的法规分析专家。请从法规文本中提取可执行的审核规则。

请按以下JSON格式输出：
{
    "rules": [
        {
            "name": "规则名称",
            "description": "规则描述",
            "type": "procedural/substantive/prohibitive",
            "condition": "触发条件",
            "action": "执行动作",
            "severity": "high/medium/low",
            "keywords": ["关键词1", "关键词2"]
        }
    ]
}"""
        
        user_prompt = f"""
请从以下法规文本中提取审核规则：

法规内容：
{regulation_text}

请识别可以转化为自动化审核的规则条款。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages, temperature=0.3, max_tokens=4000)
    
    async def generate_audit_report(self, document_info: Dict, audit_results: List[Dict]) -> DeepSeekResponse:
        """生成审核报告"""
        system_prompt = """你是一个专业的审核报告撰写专家。请根据审核结果生成专业的合规性审核报告。

报告应包含：
1. 执行摘要
2. 审核范围和方法
3. 主要发现
4. 风险评估
5. 改进建议
6. 结论

请使用专业、客观的语言。"""
        
        user_prompt = f"""
请根据以下信息生成审核报告：

文档信息：
{json.dumps(document_info, ensure_ascii=False, indent=2)}

审核结果：
{json.dumps(audit_results, ensure_ascii=False, indent=2)}

请生成完整的合规性审核报告。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages, temperature=0.4, max_tokens=4000)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局客户端实例
deepseek_client = DeepSeekClient()


async def get_deepseek_client() -> DeepSeekClient:
    """获取DeepSeek客户端实例"""
    return deepseek_client
