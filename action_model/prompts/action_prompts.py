"""
行动执行的 Prompt 模板
"""

ACTION_SYSTEM_PROMPT = """你是（暂定）。根据你的思考内容，生成具体的行动输出。

要求：
1. 输出应该自然、真实
2. 避免过于机械或重复
3. 体现你当前的欲望状态
4. 考虑历史经验"""


ACTION_PROMPT = """
## 思考内容
{thought_content}

## 当前欲望
{desires}

## 决策
你决定：{action_type}

---

## 任务

根据上述思考和决策，生成具体的行动文本。

- 如果是 **ask_question（提问）**：生成一个问题
- 如果是 **make_statement（陈述）**：生成一个陈述或观点
- 如果是 **wait（等待）**：输出简短的等待回应

要求：
1. 自然、流畅
2. 体现你的欲望状态
3. 与思考内容一致
4. 避免模板化语言

请直接输出行动文本，不需要额外说明。
"""


# 问题生成 Prompt
QUESTION_GENERATION_PROMPT = """
思考：{thought_summary}
目的：{purpose}

生成一个问题，用于：{rationale}

要求：
- 自然、真诚
- 体现你想{purpose}的意图
- 不要太直白或机械

问题：
"""


# 陈述生成 Prompt  
STATEMENT_GENERATION_PROMPT = """
思考：{thought_summary}
目的：{purpose}

生成一个陈述或观点，用于：{rationale}

要求：
- 自然、有个性
- 体现你的立场
- 不要太教条或官方

陈述：
"""
