# Week 1 Day 1 笔记 · Agent 是什么 + 模型 API 输入输出

日期：2026-10-20（提前启动）
材料：zero2Agent / learn-agent-basic 01-04
在线阅读（排版更好）：https://onefly.top/zero2Agent

---

## 阅读清单（约 1.5-2 小时）

| 篇 | 标题 | 读完要能回答 |
|---|---|---|
| 01 | [what-is-an-agent](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/01-what-is-an-agent) | Agent 的定义是什么？跟"调一次 LLM"的本质区别在哪？ |
| 02 | [workflow-vs-agent](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/02-workflow-vs-agent) | Workflow 和 Agent 的边界在哪？**面试必考**，要能举出各自适合/不适合的场景 |
| 03 | [core-components](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/03-core-components) | 一个 Agent 系统由哪几部分组成？各自解决什么问题？ |
| 04 | [why-agent-demos-break](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/04-why-agent-demos-break) | Demo 能跑、落地就崩的根因有哪些？**这篇最值钱**，面试聊"工程化"全靠它 |

## 动手（约 45 分钟）

1. 把 API key 填进 `.env`（参考 `.env.example`）
2. `uv run python week1/01_api_basics.py`
3. 逐行看打印出来的 REQUEST / RESPONSE JSON，不要跳

## 自检（答不上就回去看 JSON）

- [ ] `choices[i].message.role` 是什么值？为什么是这个值？ 
  - `role = assistant`，因为这条消息是模型生成的——对话里每条消息都要表明谁说的(user=用户 / assistant=模型 / system=指令)。Agent循环时要把这条append回messages
- [ ] `usage` 里 prompt_tokens / completion_tokens 分别怎么算出来的？
  - prompt_tokens 是你发出去的全部输入分词数（system + user 都算，所以加 system 后 10→29）；
  - completion_tokens 是模型生成的部分。两者分别计价。
- [ ] `finish_reason` 有哪几种？各自代表什么情况？
  - stop=正常说完；length=被 max_tokens 掐断；tool_calls=模型要求调工具；content_filter=被安全策略拦。
- [ ] system / user / assistant 三种 role 在请求里怎么排？模型只看最后一条吗？
  - system 放最前（设定行为），之后 user/assistant 按时间交替。模型看整个数组，不是只看最后一条——越靠后影响越大，但 system 的指令贯穿全程。
- [ ] 为什么 temperature=0 时两次调用仍可能不完全一致？
  - temperature=0 是贪心解码（每步选概率最高的 token），理论上确定，但服务端批处理、浮点非确定性、模型版本更新都会造成偶发差异。所以"完全可复现"不能只靠 temperature=0。

---

## 我的答案 / 笔记

（边读边写，用自己的话，不要抄原文）

### 01 什么是 Agent
Agent，一个由大模型驱动的、能根据状态决定下一步动作的任务执行系统。

**一句话：Agent = LLM + Context + Tools**

盲区：
> 但是判断一个系统是不是Agent，不能看他用了什么框架，也不能只看他是不是调用了工具。 
> 一些 Demo 只实现了 “LLM 调用工具” 就声称是 Agent。
> 如果一个系统：
> - 没有明确状态
> - 没有执行闭环
> - 没有结束条件
> - 无法根据结果调整下一步
> 
> 他不一定是一个完整的 Agent，更像是一个带工具调用的 LLM。

一个Agent，就是 LLM 围绕目标持续推进任务，会根据中间状态改变行为，一个闭环系统。

- Goal：目标
- State：状态
- Model：模型
- Tools：工具
- Memory：会话内或跨会话记忆
- Planner/ Policy：决策逻辑
- Evaluator / Guardrails ：评估与约束

### 02 Workflow vs Agent（面试必考）
**LLM APP** 
> 特点是：一次输入，一次输出。
> 
> 输入 --> LLM --> 输出
- 问答助手
- 摘要工具
- 翻译工具

这种工具不负责多步执行。

**Workflow**
> 特点是：有固定的执行路径，并且这个路径是由开发者预先定义写死。
> 
> 可能不是一次输入一次输出，可能有多个步骤，可能有条件分支，有循环，但是这些步骤都是提前知道的。
> 
- 先检索，再总结，然后格式化输出
- 收到简历后，抽取信息、评分、写评价

**Agent**
> 特定是：系统会根据中间状态**自己决定**下一步做什么。
> 
> 也就是说，执行路径不是完全写死的，而是部分由系统在运行中决定。

对比 Workflow 和 Agent，他的分界线
在于下一步动作是开发者提前写死？还是由系统自己根据状态动态决定的？

很多场景其实不需要Agent：
> 很多需求其实要求是：
> - 输入稳定
> - 处理步骤固定
> - 分支数量有限
> - 结果格式明确
> 
> 这种场景，Workflow 往往更便宜、更稳定、更可控。
> 
> 而 Agent 弊大于利：
> 
> - 成本更高
> - 延迟更长
> - 行为更不稳定
> - 调试困难

所以并不是 Agent 就一定好，要根据任务看它是否需要“动态决策”。

Workflow 负责确定性流程，Agent 负责不确定环境下的动态推进。

实际工程中，两者往往是组合关系，而不是二选一。

例如，外层用 Workflow 控制主流程，某些节点内部再用 Agent

- 主流程：接受任务 --> 选择任务类型 --> 调用不同的模块
- 某个处理模块内部：用 Agent 做信息探索和多部分析


### 03 核心组件
1. Goal
2. State
3. Model
4. Tools
5. Memory
6. Planner / Policy
7. Evaluator / Guardrails

#### Goal
任务要解决的问题是什么？

输出应该长什么样？

任务什么时候算完成？

#### State
- 当前任务的输入
- 现在已经完成的步骤
- 已经获取的信息
- 中间分析结果
- 下一步待办
- 是否满足结束条件

#### Model
模型不是 Agent，它只是 Agent 中的一个核心组件，如果把所有能力都堆给模型提示词，系统会变得很脆弱。

Context 是模型能力的天花板，模型每一步决策的质量，取决于它当时能看到什么。这个“能看到什么”就是 Context。

Context 通常包含：系统指令、工具定义、用户输入、历史轨迹、检索到的外部资料、结构化状态。

所以 Agent 的能力天花板往往不是模型参数量，而是 **Context的组织质量**：

- 关键约束是否在 Context 中
- 历史信息是否被合理裁剪
- 检索结果是否相关
- 工具描述是否让模型能够正确选择

Context Engineering 比 Prompt Engineering 范围更大
——不只是写好提示词，而是设计整个信息供给策略。

#### Tools
工具解决的是模型本身办不到的事情
- 搜索
- 数据库查询
- API请求
- 文件读写
- 代码执行
- 外部系统操作 
- ...

而根据功能的不同，工具又可以分成三类：

| 类型  | 作用       | 举例 |
|-----|----------|----|
| 感知类 | 获取信息     | 搜索、数据库查询、文件读取、API 拉取   |
| 执行类 | 产生外部副作用  | 写入数据库、发送消息、创建资源、执行代码   |
| 协作类 |与其他 Agent 或人类交互|发送消息给另一个 Agent、请求人工审批 |
分类的目的是**不同类型的工具需要不同的安全策略。**

#### Planner / Policy
 
- 下一步是否需要工具
- 用哪个工具
- 是否需要继续收集信息
- 什么时候停止

#### Evaluator / Guardrails

- 检查输出格式是否正确
- 检查证据是否充足
- 检查结果是否越权
- 控制成本、延迟和工具调用次数
- 必要时人工接管

防止 Agent 一本正经的产生错误结论，
为了完成任务不惜成本和时间

### 04 为什么 demo 能跑、落地就崩

---

## 今天卡住的问题（明天/下次问我）

-
