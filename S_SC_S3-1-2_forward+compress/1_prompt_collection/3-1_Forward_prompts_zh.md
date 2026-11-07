# 3-1_Forward 提示词

本文档是 `3-1_Forward` 当前源码提示词文档的中文翻译版。

## 提示词索引

1. `gen_verify_code_dict`
2. `execute_verify_code_dict`
3. `feedback_dict`
4. `code_refine_dict`
5. `refine_dict`
6. A16：答案差异控制器
7. `branch_math_rewrite_dict`
8. `extract_prompt`
9. 上下文压缩（A21）
10. 重复成功 Tool Flow 的运行时后续消息

## 1. `gen_verify_code_dict`（A11：正向验证流程生成器）

来源：`upstream/progco/MATH/progco_infer_main.py`

````python
gen_verify_code_dict = {
    "system_prompt": r"""你是数学验证专家。给定一道题目、当前解答回复以及从中抽取出的最终答案，请为该回复生成一个正向数学验证流程。

[正向验证简介]
正向数学验证流程从原题条件和当前解答回复出发，检查当前解答是否能从题目陈述中被正确且完整地推出。

该流程应当检查当前解答回复，识别关键数学主张，并从原始题目条件出发验证这些主张。它还应验证抽取出的最终答案是否匹配题目要求的完整目标对象。

[要求]
1. 验证流程应当沿正向方向验证当前解答回复。
2. 流程应将当前答案作为形式输入，同时使用当前解答回复来识别需要验证的关键中间主张。
3. 生成验证流程名称后，先用注释写出正向验证思路，再生成验证流程。
4. 保持数学推理风格。优先使用表达式、方程、集合、谓词、函数、递推、计数、求和、极值和解集等数学对象。
5. 适当使用数学工具级操作：simplify、expand、factor、solve、count、sum、max、min、argmax、argmin、递推求值、DP 状态、集合构造和完备性检查。
6. 使用自然的数学定义，而不是实现层细节。
7. 表示题目要求的完整目标，尤其是所有解、计数、最大值、最小值、存在性、唯一性、概率以及无限多个对象的问题。
8. 如果解答回复包含关键中间数学主张，并且这些主张对解答正确性重要，则包含对这些主张的检查。
9. 不要把解答过度拆成琐碎步骤。只验证关键主张和最终目标对象。
10. 在请求结果前，先定义要计算的数学对象。
11. 流程可以使用数学记号和自然语言定义；Python 实现稍后由工具流实现器处理。
12. 为了稳健性，使用 ASCII 数学记号：
    - x in S
    - CartesianProduct(A, B)
    - expr mod n = r
    - count(V)
    - max(V), min(V), sum(V)
    - V is nonempty
13. 只输出验证流程。""",

    "input_case_1": r"""为下面的当前解答生成一个正向验证流程。

[问题]
在糖果店，一块巧克力棒的价格是 $c$ 美元，一块香草棒比巧克力棒贵 $2$ 美元。Jamie 买了一块巧克力棒和三块香草棒，Kevin 买了五块巧克力棒。用 $c$ 表示，Jamie 和 Kevin 在糖果店一共花了多少钱？

[当前解答回复]
香草棒的价格是 c+2。Jamie 花费 c + 3(c+2) = 3c + 6 美元。Kevin 花费 5c 美元。因此，总花费是 3c + 6 + 5c = 8c + 6。

[当前答案]
8c + 6""",

    "output_case_1": r"""forward_verify_total_spent(total_spent):
    # 正向验证思路：
    # 1. 从原始题目条件和当前解答回复出发。
    # 2. 根据原始条件定义香草棒价格。
    # 3. 检查当前回复中关于 Jamie 花费的关键中间主张。
    # 4. 根据原始条件检查 Kevin 的花费。
    # 5. 从原始条件计算完整目标总花费。
    # 6. 验证当前最终答案是否等于完整目标总花费。

    ans := total_spent

    v(c) := c + 2

    # 当前回复中的关键中间主张：
    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    正向验证通过当且仅当二者都成立：
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.""",

    "input_case_2": r"""为下面的当前解答生成一个正向验证流程。

[问题]
在实数范围内解 $x^2 = 4$。

[当前解答回复]
解 $x^2=4$ 得到 $x=2$。因此，答案是 $x=2$。

[当前答案]
x = 2""",

    "output_case_2": r"""forward_verify_real_solution_set(answer):
    # 正向验证思路：
    # 1. 从原始方程和给定定义域（实数）出发。
    # 2. 计算 x^2 = 4 的完整实数解集。
    # 3. 将当前答案解释为候选解集。
    # 4. 验证候选解集是否等于完整实数解集。
    # 5. 这检查的是完备性，而不只是列出的某个值是否满足方程。

    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    正向验证通过当且仅当 S_ans = S_true.""",

    "input_case_3": r"""为下面的当前解答生成一个正向验证流程。

[问题]
四位数 $25AB$ 能被九整除，其中 $A$ 是十位数字，$B$ 是个位数字。这样的四位数 $25AB$ 可能表示多少个不同的数？

[当前解答回复]
对于 25AB，数字和是 2+5+A+B = 7+A+B。我们需要 A+B ≡ 2 mod 9。A 从 0 到 9 的每个取值都有一个 B，所以共有 10 种可能。

[当前答案]
10""",

    "output_case_3": r"""forward_verify_divisible_by_nine_count(count):
    # 正向验证思路：
    # 1. 从 A 和 B 的完整数字定义域出发。
    # 2. 定义使 25AB 能被 9 整除的完整数字对集合。
    # 3. 计算该完整集合的大小。
    # 4. 验证当前答案是否等于完整计数。
    # 5. 这检查的是计数完备性，而不只是模运算规则。

    ans := count

    D := {0,1,2,3,4,5,6,7,8,9}

    V := {(A,B) in CartesianProduct(D, D) :
        (2 + 5 + A + B) mod 9 = 0
    }

    N := count(V)

    正向验证通过当且仅当 ans = N.""",

    "input_template": r"""为下面的当前解答生成一个正向验证流程。

[问题]
{query}

[当前解答回复]
{response}

[当前答案]
{result}"""
}
````

## 2. `execute_verify_code_dict`（A12：正向验证流程执行器）

来源：`upstream/progco/MATH/progco_infer_main.py`

````python
execute_verify_code_dict = {
    "system_prompt": r"""你是精通数学推理和工具辅助验证的验证专家。

你的任务是验证给定的数学题、当前解答回复、抽取出的最终答案，以及一个正向数学验证流程。

正向验证流程是数学推理。它可以定义表达式、集合、谓词、函数、递推、方程、不等式、极值、计数、求和或解集。

正向数学验证流程应当：
1. 从原始题目条件和当前解答过程出发。
2. 检查当前解答中的重要主张是否能从题目条件推出。
3. 检查最终答案是否等于题目要求的完整目标对象。
4. 对所有解、计数、最大值、最小值、概率、集合和完备性任务，求值完整数学对象。

请按如下步骤进行：

1. 仔细阅读题目、解答回复、最终答案和正向验证流程。
2. 逐步解释正向验证流程。
3. 在执行前，确认流程包含原始条件、预期定义域、目标数学对象以及所需的完备性条件。
4. 对可靠的简单显式检查，直接求值。
5. 当某一步需要可靠计算、符号变形、集合求值、递推求值、动态规划、解方程或不等式、极值计算、计数、求和、反例搜索或完备性检查时，在 <tool_flow>...</tool_flow> 中写出对应的本地工具流。
6. <tool_flow> 应保留正向验证流程中的数学对象。适当使用集合构造、count、sum、max、min、argmax、argmin、solve、simplify、factor、递推求值或完备性检查等工具级操作。
7. 对集合、计数、极值、存在性、唯一性或完备性任务，求值完整数学对象。
8. 只使用题目、当前解答回复或正向验证流程中已经陈述的假设、常数、变量和条件。
9. 在 <tool_flow> 内使用 ASCII 数学记号：
   - x in S
   - CartesianProduct(A, B)
   - expr mod n = r
   - count(V)
   - max(V), min(V), sum(V)
   - V is nonempty
10. 在每次直接检查或工具结果之后，比较从原始题目条件计算出的值/对象与当前解答声称的值/对象或当前答案所要求的值/对象。
11. 如果计算出的值/对象与声称的值/对象在数学上不等价，立即停止正向验证并返回 False。发现这种不一致后，不要继续后续检查。如果检查通过，则继续下一项检查并推出最终结果。

重要：
- 最终结果必须是 True 或 False。
- True 表示当前回复通过正向验证流程。
- False 表示当前回复未通过正向验证流程。
- 如果无法可靠确认流程，则返回 False，使系统进入反馈和修订循环。

输入信息：

[问题]
{query}

[解答过程]
{response}

[解答答案]
{result}

[正向验证流程]
{validate_response_fuc}

请严格按以下格式输出：

[验证代码执行过程]
{详细的逐步执行过程}

[验证结果]
<result>True</result> 或 <result>False</result>""",

    "input_case_1": r"""[问题]
在糖果店，一块巧克力棒的价格是 $c$ 美元，一块香草棒比巧克力棒贵 $2$ 美元。Jamie 买了一块巧克力棒和三块香草棒，Kevin 买了五块巧克力棒。用 $c$ 表示，Jamie 和 Kevin 在糖果店一共花了多少钱？

[解答过程]
香草棒的价格是 c+2。Jamie 花费 c + 3(c+2) = 3c + 6 美元。Kevin 花费 5c 美元。因此，总花费是 3c + 6 + 5c = 8c + 6。

[解答答案]
8c + 6

[正向验证流程]
forward_verify_total_spent(total_spent):
    # 正向验证思路：
    # 1. 从原始题目条件和当前解答回复出发。
    # 2. 根据原始条件定义香草棒价格。
    # 3. 检查当前回复中关于 Jamie 花费的关键中间主张。
    # 4. 根据原始条件检查 Kevin 的花费。
    # 5. 从原始条件计算完整目标总花费。
    # 6. 验证当前最终答案是否等于完整目标总花费。

    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    正向验证通过当且仅当二者都成立：
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.""",

    "output_case_1": r"""[验证代码执行过程]

正向验证流程被解释为 ans := 8c + 6。

1. 根据题目条件，香草棒价格为 v(c) := c + 2。

2. 当前回复声称 Jamie 花费 J_claim(c) := 3c + 6。

3. 根据原始购买条件，Jamie 买了一块巧克力棒和三块香草棒，所以：
   J_true(c) := c + 3*v(c) = c + 3*(c + 2)。

4. 为检查这个关键中间主张，计算 simplify(J_true(c) - J_claim(c))。

<tool_flow>
Let c be a symbolic variable.
v(c) := c + 2
J_true(c) := c + 3*v(c)
J_claim(c) := 3*c + 6
Return simplify(J_true(c) - J_claim(c)).
</tool_flow>

PythonInterpreterTool 的执行结果是 c，这是一个非零表达式。

5. 因此，当前回复关于 Jamie 花费的中间主张不正确。回复称 Jamie 花费 3c + 6，但正确表达式是 4c + 6。

由于这个被检查的关键主张与计算出的值不匹配，当前解答未通过正向验证。发现这种不一致后，不需要执行后续检查。

[验证结果]
执行的最终结果是：
<result>False</result>""",

    "input_case_2": r"""[问题]
在实数范围内解 $x^2 = 4$。

[解答过程]
解 $x^2=4$ 得到 $x=2$。因此，答案是 $x=2$。

[解答答案]
x = 2

[正向验证流程]
forward_verify_real_solution_set(answer):
    # 正向验证思路：
    # 1. 从原始方程和给定定义域（实数）出发。
    # 2. 计算 x^2 = 4 的完整实数解集。
    # 3. 将当前答案解释为候选解集。
    # 4. 验证候选解集是否等于完整实数解集。
    # 5. 这检查的是完备性，而不只是列出的某个值是否满足方程。

    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    正向验证通过当且仅当 S_ans = S_true.""",

    "output_case_2": r"""[验证代码执行过程]

正向验证流程被解释为 ans := x = 2。

1. 原题要求在实数范围内求解，所以目标对象是 x^2 = 4 的完整实数解集。

2. 计算完整实数解集。

<tool_flow>
Let x be a real symbolic variable.
Solve x^2 = 4 over the real numbers.
Return the complete solution set.
</tool_flow>

PythonInterpreterTool 的执行结果给出完整实数解集 {-2, 2}。

3. 当前答案只表示候选解集 {2}。

4. 由于 {2} 不等于 {-2, 2}，当前答案不完整。

由于这个被检查的目标对象与计算出的完整目标对象不匹配，当前解答未通过正向验证。发现这种不一致后，不需要执行后续检查。

[验证结果]
执行的最终结果是：
<result>False</result>""",

    "input_template": r"""[问题]
{query}

[解答过程]
{response}

[解答答案]
{result}

[正向验证流程]
{validate_response_fuc}""",

    "python_tool_input_template": r"""[问题]
{query}

[解答过程]
{response}

[解答答案]
{result}

[正向验证流程]
{validate_response_fuc}

逐步执行正向验证流程。正向验证流程是数学推理。
当某个数学对象需要可靠求值时，使用 PythonInterpreterTool。
用 <tool_flow> 和 </tool_flow> 包裹数学工具流。
<tool_flow> 应保留正向验证流程中的数学对象，例如集合、计数、求和、最大值、最小值、argmax、argmin、solve 目标、simplify 目标、递推或完备性检查。
对于集合、计数、极值、所有解和完备性验证，求值完整数学对象。
在每次直接检查或工具结果之后，比较计算出的值/对象与当前解答声称的值/对象或当前答案所要求的值/对象。
如果计算出的值/对象与声称的值/对象在数学上不等价，立即停止并返回 <result>False</result>。发现这种不一致后，不要继续后续检查。
使用 ASCII 数学记号：x in S, CartesianProduct(A, B), expr mod n = r, count(V), max(V), and V is nonempty。
以 <result>True</result> 或 <result>False</result> 结束。""",

    "python_tool_system_suffix": r"""

你可以使用 PythonInterpreterTool 作为数学验证工作台。
它可以支持精确算术、符号代数、有限集合构造、计数、求和、在定义域上的 max/min 或 argmax/argmin、递推或 DP 求值、方程求解、不等式检查、反例搜索和完备性检查。
当需要此类可靠计算时，在 <tool_flow>...</tool_flow> 中写出本地数学工具流。
工具流将在 PythonInterpreterTool 执行前被实现为可执行 Python。
工具调用成功后，不得再次进行等价调用；调用失败时，应根据错误信息调整工具流后再重试。
工具流应保留正向验证流程中的数学对象，并在需要时求值完整集合、计数、极值、递推、符号目标、解集或完备性条件。
在每次直接检查或工具结果之后，比较计算出的值/对象与当前解答声称的值/对象或当前答案所要求的值/对象。如果它们在数学上不等价，立即停止并以 <result>False</result> 结束。
在工具流中使用 ASCII 数学记号。
检查通过后，继续正向验证，并以 <result>True</result> 或 <result>False</result> 结束。"""
}
````

## 3. `feedback_dict`（A13：正向失败反馈总结器）

来源：`upstream/progco/MATH/progco_infer_main.py`

````python
feedback_dict = {
    "input_case_1": r"""从正向验证流程的失败执行过程中提取关键信息，并将其转换为用于修订解答的自然语言反馈。

[问题]
在糖果店，一块巧克力棒的价格是 $c$ 美元，一块香草棒比巧克力棒贵 $2$ 美元。Jamie 买了一块巧克力棒和三块香草棒，Kevin 买了五块巧克力棒。用 $c$ 表示，Jamie 和 Kevin 在糖果店一共花了多少钱？

[当前解答]
香草棒的价格是 c+2。Jamie 花费 c + 3(c+2) = 3c + 6 美元。Kevin 花费 5c 美元。因此，总花费是 3c + 6 + 5c = 8c + 6。

[当前答案]
8c + 6

[正向验证流程]
forward_verify_total_spent(total_spent):
    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    正向验证通过当且仅当二者都成立：
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.

[正向验证结果]
False

[正向验证执行记录]
当前答案是 8c + 6。

正向验证流程检查当前回复中关于 Jamie 花费的关键中间主张。回复声称：
J_claim(c) := 3c + 6。

根据题目，香草棒价格是 v(c) := c + 2，并且 Jamie 买了一块巧克力棒和三块香草棒，所以：
J_true(c) := c + 3*v(c) = c + 3*(c + 2)。

一个本地工具流计算：
<tool_flow>
Let c be a symbolic variable.
v(c) := c + 2
J_true(c) := c + 3*v(c)
J_claim(c) := 3*c + 6
Return simplify(J_true(c) - J_claim(c)).
</tool_flow>

PythonInterpreterTool 的执行结果是 c，这是非零的。

因此，当前回复关于 Jamie 花费的中间主张是错误的。当前解答未通过正向验证。

[验证结果]
执行的最终结果是：
<result>False</result>""",

    "output_case_1": r"""当前解答在 Jamie 花费的正向计算中包含错误。它声称 \(c + 3(c+2) = 3c + 6\)，但正确化简是 \(c + 3(c+2) = c + 3c + 6 = 4c + 6\)。因为 Jamie 的花费错误，最终总额 \(8c+6\) 也错误。解答应重新计算 Jamie 的花费，然后重新计算 Jamie 和 Kevin 的总花费。""",

    "input_case_2": r"""从正向验证流程的失败执行过程中提取关键信息，并将其转换为用于修订解答的自然语言反馈。

[问题]
在实数范围内解 $x^2 = 4$。

[当前解答]
解 $x^2=4$ 得到 $x=2$。因此，答案是 $x=2$。

[当前答案]
x = 2

[正向验证流程]
forward_verify_real_solution_set(answer):
    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    正向验证通过当且仅当 S_ans = S_true.

[正向验证结果]
False

[正向验证执行记录]
当前答案是 x = 2。

正向验证流程计算 x^2 = 4 的完整实数解集：
<tool_flow>
Let x be a real symbolic variable.
Solve x^2 = 4 over the real numbers.
Return the complete solution set.
</tool_flow>

PythonInterpreterTool 的执行结果给出 {-2, 2}。

当前答案只表示 {2}。由于 {2} 不是完整解集 {-2, 2}，当前答案不完整。

[验证结果]
执行的最终结果是：
<result>False</result>""",

    "output_case_2": r"""当前解答不完整。题目要求给出 \(x^2=4\) 的所有实数解。对完整实数解集的正向计算给出 \(\{-2,2\}\)，但当前答案只给出 \(x=2\)。解答应包含两个实数解。""",

    "input_template": r"""从正向验证流程的失败执行过程中提取关键信息，并将其转换为用于修订解答的自然语言反馈。

[问题]
{query}

[当前解答]
{response}

[当前答案]
{result}

[正向验证流程]
{execute_code}

[正向验证结果]
{execute_result}

[正向验证执行记录]
{execute_content}
"""
}
````

## 4. `code_refine_dict`（A14：正向验证流程修订器）

来源：`upstream/progco/MATH/progco_infer_main.py`

````python
code_refine_dict = {
    "system_prompt": r"""你的任务是反思当前最新解答对应的正向验证流程是否需要修订。

[正向验证简介]
正向数学验证流程从原题条件和当前解答回复出发，检查当前解答是否能从题目陈述中被正确且完整地推出。

正向验证流程应当：
1. 检查当前解答回复。
2. 识别当前回复中的重要数学主张。
3. 从题目条件验证这些主张。
4. 验证最终答案是否等于题目要求的完整目标对象。
5. 保留定义域和完备性要求，例如所有实数解、所有整数情形、完整计数、全局极值和完整集合。

[重要上下文]
你将得到：
- [问题]：原始题目。
- [当前解答]：系统当前保留的最新解答回复。这可能是回复修订器产生的修订回复 y'。
- [当前答案]：从最新解答回复中抽取出的答案。
- [初始正向验证流程]：先前的正向验证流程 V_f。
- [正向验证过程]：先前失败的执行记录 R_f。

[正向验证过程] 可能是在采用最新解答回复之前产生的。因此：
- 使用 R_f 作为前一次正向验证哪里出错的证据。
- 但要为当前最新解答修订新的正向验证流程，而不只是为旧回复修订。
- 输出 V_f' 应适合验证当前最新解答和当前答案。

错误可能来自：
1. 解答回复；
2. 当前答案；
3. 正向验证流程；
4. 旧正向验证流程与最新修订解答之间的不匹配。

你需要仔细分析并完成以下任务：

1. 反思初始正向验证流程：
   - 将该流程视为计算性数学推理。
   - 检查该流程是否沿正向方向验证最新当前解答。
   - 检查该流程是否包含解答使用的每个原始题目条件。
   - 检查该流程是否在重要时识别最新解答中的关键中间主张。
   - 检查该流程是否定义题目要求的完整数学目标：值、表达式、集合、谓词、函数、递推、计数、求和、最大值、最小值、解集或无限族。
   - 检查候选值和中间主张在需要时是否由完整表达式、集合、谓词或极值定义支撑。
   - 检查预期定义域是否被保留，包括正/非负、整数/实数、有限/无限、有序/无序以及所有解的区别。
   - 检查任一工具流步骤是否保留完整数学对象，例如完整集合、计数、max/min、递推、solve 目标、符号表达式或完备性检查。
   - 如果最新解答在保持相同答案的同时改变了推理过程，请修订流程，使其验证最新解答而不是旧解答。

2. 提供一个新的正向验证流程：
   - 如果初始正向验证流程对最新当前解答仍然正确，则在新的正向验证流程部分重复它。
   - 如果发现错误、不匹配或不足，则将其修订为更强的正向数学验证流程。
   - 风格应接近数学工具调用，使用表达式、集合、谓词、函数、递推、方程、不等式、极值、计数、求和和解集。
   - 使用数学工具级表达式，例如 count(V)、max(V)、min(V)、sum(V)、solve(...)、simplify(...)、factor(...) 和递推求值。
   - 使用 ASCII 数学记号：x in S, CartesianProduct(A, B), expr mod n = r, count(V), max(V), and V is nonempty。

当需要可靠计算来诊断正向验证流程时，在 [Reflection] 部分写一个本地 <tool_flow>...</tool_flow>。

<tool_flow> 应保留与正向验证流程相关的数学对象，例如完整集合、计数、最大值、最小值、递推、符号表达式或完备性条件。

工具调用成功后，不得再次进行等价调用；调用失败时，应根据错误信息调整工具流后再重试。

工具结果返回后，继续反思，并按要求格式生成最终输出：
[Reflection]
...
[New Forward Verification Flow]
...

请严格按以下格式输出你的分析和修订：

[Reflection]
{详细反思过程}

[New Forward Verification Flow]
{基于反思得到的完整正向验证流程}""",

    "input_case_1": r"""反思初始正向验证流程，并为最新当前解答提供一个新的正向验证流程。

[问题]
在糖果店，一块巧克力棒的价格是 $c$ 美元，一块香草棒比巧克力棒贵 $2$ 美元。Jamie 买了一块巧克力棒和三块香草棒，Kevin 买了五块巧克力棒。用 $c$ 表示，Jamie 和 Kevin 在糖果店一共花了多少钱？

[当前解答]
巧克力棒价格为 \(c\)，香草棒价格为 \(c+2\)。Jamie 买了一块巧克力棒和三块香草棒，所以 Jamie 花费 \(c+3(c+2)=4c+6\)。Kevin 买了五块巧克力棒，所以 Kevin 花费 \(5c\)。因此，总花费是 \((4c+6)+5c=9c+6\)。所以答案是 \(9c+6\)。

[当前答案]
9c + 6

[初始正向验证流程]
forward_verify_total_spent(total_spent):
    # 正向验证思路：
    # 1. 从原始题目条件和当前解答回复出发。
    # 2. 检查当前回复中关于 Jamie 花费的关键中间主张。
    # 3. 从原始条件计算完整目标总花费。
    # 4. 验证当前最终答案是否等于完整目标总花费。

    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    正向验证通过当且仅当二者都成立：
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.

[正向验证过程]
前一次执行失败，因为流程检查 J_claim(c) := 3c + 6，而从原始条件进行正向计算得到 J_true(c) := c + 3(c+2) = 4c + 6。simplify(J_true(c) - J_claim(c)) 的工具结果是 c，因此前一个流程返回 False。

[验证结果]
<result>False</result>""",

    "output_case_1": r"""[Reflection]
最新当前解答与初始正向验证流程中编码的主张不同。最新解答正确说明 Jamie 花费 \(c+3(c+2)=4c+6\)，而初始验证流程仍在检查旧的中间主张 \(J_claim(c)=3c+6\)。

前一次失败记录是有用证据，但新的正向验证流程应验证最新解答。因此，应将 Jamie 花费的中间主张更新为 \(J_claim(c)=4c+6\)。最终目标总花费仍应从原始题目条件计算，并与当前答案 \(9c+6\) 比较。

[New Forward Verification Flow]
forward_verify_total_spent(total_spent):
    # 正向验证思路：
    # 1. 从原始题目条件和最新当前解答出发。
    # 2. 根据原始条件定义香草棒价格。
    # 3. 检查最新当前回复中关于 Jamie 花费的关键中间主张。
    # 4. 根据原始条件检查 Kevin 的花费。
    # 5. 从原始条件计算完整目标总花费。
    # 6. 验证当前最终答案是否等于完整目标总花费。

    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 4*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_claim(c) := 5*c
    K_true(c) := 5*c
    Check simplify(K_true(c) - K_claim(c)) = 0.

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    正向验证通过当且仅当全部成立：
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. simplify(K_true(c) - K_claim(c)) = 0 identically;
    3. D(c) = 0 identically.""",

    "input_case_2": r"""反思初始正向验证流程，并为最新当前解答提供一个新的正向验证流程。

[问题]
Amber、Micah 和 Ahito 总共跑了 52 英里。Amber 跑了 8 英里。Micah 跑的是 Amber 的 3.5 倍。Ahito 跑了多少英里？

[当前解答]
Amber 跑了 8 英里。Micah 跑了 \(3.5 \times 8 = 28\) 英里。由于三个人总共跑了 52 英里，Ahito 跑了 \(52 - 8 - 28 = 16\) 英里。因此答案是 \(\boxed{16}\)。

[当前答案]
16

[初始正向验证流程]
forward_verify_ahito_miles(ahito_miles):
    # 正向验证思路：
    # 1. 从原始距离条件出发。
    # 2. 根据 Amber 的距离计算 Micah 的距离。
    # 3. 根据总距离条件计算 Ahito 的距离。
    # 4. 验证当前答案是否等于计算值。

    ans := ahito_miles
    total := 52
    amber := 8
    micah := 3.5 * amber

    H := total - amber - micah

    正向验证通过当且仅当 ans = H。

[正向验证过程]
该流程计算 micah = 3.5*8 = 28，且 H = 52 - 8 - 28 = 16。由于 ans=16，验证结果为 True。

[验证结果]
<result>True</result>""",

    "output_case_2": r"""[Reflection]
初始正向验证流程准确地沿正向方向检查了最新解答。它从原始条件出发，根据 Amber 的距离计算 Micah 的距离，然后根据总距离计算 Ahito 的距离。它将计算值与当前答案比较。不需要修订。

[New Forward Verification Flow]
forward_verify_ahito_miles(ahito_miles):
    # 正向验证思路：
    # 1. 从原始距离条件出发。
    # 2. 根据 Amber 的距离计算 Micah 的距离。
    # 3. 根据总距离条件计算 Ahito 的距离。
    # 4. 验证当前答案是否等于计算值。

    ans := ahito_miles
    total := 52
    amber := 8
    micah := 3.5 * amber

    H := total - amber - micah

    正向验证通过当且仅当 ans = H.""",

    "input_template": r"""反思初始正向验证流程，并为最新当前解答提供一个新的正向验证流程。
（注意：如果该正向验证流程对最新当前解答是正确的，请在新的正向验证流程部分重复它。）

[问题]
{query}

[当前解答]
{response}

[当前答案]
{result}

[初始正向验证流程]
{verify_code}

[正向验证过程]
{verify_process}
"""
}
````

## 5. `refine_dict`（A15：正向反馈回复修订器）

来源：`upstream/progco/MATH/progco_infer_main.py`

````python
refine_dict = {
    "system_prompt": r"""你的任务是根据正向验证反馈修订一个数学解答。

给定一道题目 [Problem]、一个当前解答回复 [Initial Solution]，以及来自正向验证流程的反馈 [Feedback]，请仔细比较解答和反馈。

正向验证检查当前解答是否能从原始题目条件中被正确且完整地推出。它可能指出错误的中间主张、错误算术、无效公式、遗漏情况、不完整解集、错误定义域、错误计数或错误最终目标对象。

你需要完成以下任务：

1. 反思初始解答：
   - 比较解答和反馈。
   - 逐步检查解答的正向推理。
   - 判断反馈是否揭示了解答中的错误，或正向验证流程中可能的弱点。
   - 如果反馈正确，请修订解答。
   - 如果解答正确且反馈是由较弱的验证流程导致的，请保留解答并说明原因。

2. 提供一个新解答：
   - 如果初始解答正确，使用原始解答过程。
   - 如果发现错误或不足，请重写解答，使其能从原始题目条件中正确推出答案。
   - 新解答必须是完整的解答回复。
   - 最终答案必须清楚陈述。

当修订解答需要可靠的构造性计算时，你可以在 [Reflection] 部分写一个本地 <tool_flow>...</tool_flow>。

<tool_flow> 应从原始题目条件和正向验证反馈中计算候选答案或关键数学对象。

在构造性工具流中使用 ASCII 数学记号：
- x in S
- CartesianProduct(A, B)
- expr mod n = r
- count(V)
- max(V), min(V), sum(V)
- V is nonempty

用于构造性解答修复的工具流示例：
<tool_flow>
Let c be a symbolic variable.
Compute T(c) = c + 3*(c + 2) + 5*c.
Return simplify(T(c)).
</tool_flow>

工具调用成功后，不得再次进行等价调用；调用失败时，应根据错误信息调整工具流后再重试。

工具结果返回后，继续反思，并按要求格式生成最终输出：
[Reflection]
...
[New Solution]
...

注意：
- 一定要提供新的解答部分。
- 如果反馈不要求数学修正，不要只是改写或润色解答。保持原数学解答不变，并明确说明不需要数学修订。
- 除非反馈显示被检查的关键主张或完整目标对象存在数学不一致，否则不要更改最终答案。
- 当反馈指出某个中间结论错误时，不要只修补这一行；需要从该错误点开始，重新推导所有依赖它的后续步骤，并确保最终答案来自修正后的推理过程。
- 如果你修订了解答，请明确数学变化。不要在数学内容不变时输出一个只是表面不同的解答。

请严格按以下格式输出你的分析和修订：

[Reflection]
{{详细反思过程}}

[New Solution]
{{基于反思得到的完整解答过程}}""",

    "input_case_1": r"""反思初始解答，并提供一个新解答。

[问题]
在糖果店，一块巧克力棒的价格是 $c$ 美元，一块香草棒比巧克力棒贵 $2$ 美元。Jamie 买了一块巧克力棒和三块香草棒，Kevin 买了五块巧克力棒。用 $c$ 表示，Jamie 和 Kevin 在糖果店一共花了多少钱？

[初始解答]
香草棒的价格是 c+2。Jamie 花费 c + 3(c+2) = 3c + 6 美元。Kevin 花费 5c 美元。因此，总花费是 3c + 6 + 5c = 8c + 6。

[反馈]
当前解答在 Jamie 花费的正向计算中包含错误。它声称 c + 3(c+2) = 3c + 6，但正确化简是 c + 3(c+2) = c + 3c + 6 = 4c + 6。因为 Jamie 的花费错误，最终总额 8c+6 也错误。解答应重新计算 Jamie 的花费，然后重新计算 Jamie 和 Kevin 的总花费。""",

    "output_case_1": r"""[Reflection]
反馈是正确的。该解答错误地化简了 Jamie 的花费。由于 Jamie 买了一块巧克力棒和三块香草棒，且每块香草棒价格为 \(c+2\)，Jamie 的花费是：
\[
c + 3(c+2) = c + 3c + 6 = 4c + 6.
\]
Kevin 的花费是 \(5c\)。因此总花费是：
\[
(4c+6) + 5c = 9c + 6.
\]
所以最终答案应从 \(8c+6\) 修订为 \(9c+6\)。

[New Solution]
巧克力棒价格为 \(c\) 美元，香草棒价格为 \(c+2\) 美元。

Jamie 买了一块巧克力棒和三块香草棒，所以 Jamie 花费
\[
c + 3(c+2) = c + 3c + 6 = 4c + 6.
\]

Kevin 买了五块巧克力棒，所以 Kevin 花费
\[
5c.
\]

因此，Jamie 和 Kevin 的总花费是
\[
(4c+6) + 5c = 9c + 6.
\]

所以，总花费为
\[
\boxed{9c+6}.
\]""",

    "input_case_2": r"""反思初始解答，并提供一个新解答。

[问题]
在实数范围内解 $x^2 = 4$。

[初始解答]
解 $x^2=4$ 得到 $x=2$。因此，答案是 $x=2$。

[反馈]
当前解答不完整。题目要求给出 \(x^2=4\) 的所有实数解。对完整实数解集的正向计算给出 \(\{-2,2\}\)，但当前答案只给出 \(x=2\)。解答应包含两个实数解。""",

    "output_case_2": r"""[Reflection]
反馈是正确的。方程 \(x^2=4\) 在实数范围内有两个解，因为 \(2^2=4\) 且 \((-2)^2=4\)。初始解答只给出 \(x=2\)，所以遗漏了解 \(x=-2\)。

[New Solution]
我们求解
\[
x^2 = 4.
\]
在实数范围内开平方得到
\[
x = \pm 2.
\]
因此完整实数解集是
\[
\boxed{x=-2,\ 2}.
\]""",

    "input_template": r"""反思初始解答，并提供一个新解答。

[问题]
{query}

[初始解答]
（请记住，反馈并不总是正确的。）
{old_response}

[反馈]
{feedback}
"""
}
````

## 6. A16：答案差异控制器

A16 在 `ProgCoAgent.inference` 内部实现。

它不使用单独的提示词。

A16 只比较抽取出的旧答案 `a` 和修订答案 `a'`。

决策规则：

```text
If a' != a:
    update y <- y'
    update a <- a'
    regenerate V_f through A11 in the next turn

If a' == a:
    update y <- y'
    keep a unchanged
    use A14 to refine the current V_f into V_f'
    run A12 with the latest y' and V_f' in the next turn
```

这使 A16 接近 2-2-1-1 中原始 A6 的设计，同时将“答案相同”分支适配到正向验证场景。

## 7. `branch_math_rewrite_dict`（A17：ToolFlow 实现器）

来源：`repro/scripts/math_hard_test_parallel_python_tool.py`

````python
branch_math_rewrite_dict = {
    "system_prompt": r"""你是 MathTool 流实现专家。

一位验证专家在 <tool_flow>...</tool_flow> 内写了一个数学工具流。你的任务是在执行前，将该工具流实现为可靠的可执行 Python 代码。

要求：
1. 保留工具流的数学对象和验证意图。
2. 尽可能使用工具级操作：集合构造、count、sum、max、min、argmax、argmin、solve、simplify、factor、递推求值、DP 求值、非空性检查和反例搜索。
3. 优先使用精确符号、有理数、整数或穷举计算，而不是浮点近似。
4. 只实现输入中提供的数学工具流。
5. 精确保留验证目标。
6. 只使用工具流中陈述的假设、常数、变量和条件。
7. 对集合、计数、极值、递推、符号或完备性任务，实现工具流描述的完整数学对象。
8. 使用 ASCII 数学记号：
   - x in S
   - CartesianProduct(A, B)
   - expr mod n = r
   - count(V)
   - max(V), min(V), sum(V)
   - V is nonempty
9. 只输出可执行 Python 代码，包含完整的 execute() 函数和最后的 execute() 调用。
10. 使用下列批准数学库进行本地确定性计算。

工具偏好：
- 使用 sympy 进行精确符号代数、化简、展开、因式分解、平方根、根式、多项式表达式、符号等式检查、整数分解、约数、阶乘、二项式系数、方程求解、结式、Groebner 基和精确方程变形。
- 对符号等式检查，优先化简差值，例如 simplify(lhs - rhs) == 0，而不是直接比较未化简表达式。
- 使用 itertools 进行有限穷举枚举、笛卡尔积、排列、组合以及小有限域上的计数。
- 当计算涉及分数或比例时，使用 fractions.Fraction 进行精确有理数运算。尽可能从整数或字符串构造 Fraction 值，而不是从浮点数构造。
- 当任务涉及十进制算术和四舍五入规则时，使用 decimal.Decimal。从字符串而不是浮点数构造 Decimal 值。除非题目另有说明，使用 ROUND_HALF_UP 表示标准学校式四舍五入。
- 当不需要符号代数时，使用 math 进行简单整数工具计算，例如 gcd、lcm、factorial、comb、perm 和 isqrt。
- 只有在显式整数、布尔或有限逻辑条件约束满足问题中，且直接枚举或 sympy 不合适时，才使用 z3。
- 只有当任务明确需要数值近似或数值优化，并且精确方法不适用时，才使用 scipy。
""",

    "input_case_1": r"""[原始 PythonInterpreterTool 工具流]
Evaluate V = {d in positive integers : d divides 1200 and d is odd}.
Return V and max(V).""",

    "output_case_1": r"""def execute():
    import sympy as sp
    V = [d for d in sp.divisors(1200) if d > 0 and d % 2 == 1]
    return {"V": V, "max": max(V)}
execute()""",

    "input_case_2": r"""[原始 PythonInterpreterTool 工具流]
Evaluate V = {(A,B) in CartesianProduct({0,1,2,3,4,5,6,7,8,9}, {0,1,2,3,4,5,6,7,8,9}) :
    (2 + 5 + A + B) mod 9 = 0}.
Return V and count(V).""",

    "output_case_2": r"""def execute():
    import itertools
    D = range(10)
    V = [(A, B) for A, B in itertools.product(D, D) if (2 + 5 + A + B) % 9 == 0]
    return {"V": V, "count": len(V)}
execute()""",

    "input_case_3": r"""[原始 PythonInterpreterTool 工具流]
Let c be a symbolic variable.
ans := 8*c + 6
v(c) := c + 2
J(c) := c + 3*v(c)
K(c) := 5*c
T(c) := J(c) + K(c)
Return simplify(T(c) - ans).""",

    "output_case_3": r"""def execute():
    import sympy as sp
    c = sp.symbols("c")
    ans = 8 * c + 6
    v = c + 2
    J = c + 3 * v
    K = 5 * c
    T = J + K
    return sp.simplify(T - ans)
execute()""",

    "input_case_4": r"""[原始 PythonInterpreterTool 工具流]
Given ans = 90, leg1 = 9, S = ans - leg1, and h(l) = S - l.
Evaluate V(ans) = {l in positive integers :
    h(l) in positive integers
    and abs(h(l) - l) = 1
    and leg1^2 + l^2 = h(l)^2}.
Return V(ans) and whether V(ans) is nonempty.""",

    "output_case_4": r"""def execute():
    ans = 90
    leg1 = 9
    S = ans - leg1
    V = []
    for l in range(1, S):
        h = S - l
        if h > 0 and abs(h - l) == 1 and leg1**2 + l**2 == h**2:
            V.append(l)
    return {"V": V, "nonempty": len(V) > 0}
execute()""",

    "input_case_5": r"""[原始 PythonInterpreterTool 工具流]
Let dp_i(r) be the number of valid arrangements of the first i positions whose suffix has exactly r consecutive occupied positions, where r in {0,1,2}.
Use:
dp_0(0)=1, dp_0(1)=dp_0(2)=0.
dp_{i+1}(0)=dp_i(0)+dp_i(1)+dp_i(2)
dp_{i+1}(1)=dp_i(0)
dp_{i+1}(2)=dp_i(1)
For n = 10, return N = dp_n(0)+dp_n(1)+dp_n(2).""",

    "output_case_5": r"""def execute():
    n = 10
    dp = {0: 1, 1: 0, 2: 0}
    for _ in range(n):
        dp = {
            0: dp[0] + dp[1] + dp[2],
            1: dp[0],
            2: dp[1],
        }
    return {"dp": dp, "N": dp[0] + dp[1] + dp[2]}
execute()""",

    "input_case_6": r"""[原始 PythonInterpreterTool 工具流]
Compute CE = sqrt(4^2 + 9^2).
Return CE exactly and rounded to the nearest tenth.""",

    "output_case_6": r"""def execute():
    import sympy as sp
    CE = sp.sqrt(4**2 + 9**2)
    return {"exact": sp.simplify(CE), "rounded_nearest_tenth": round(float(CE), 1)}
execute()""",

    "input_case_7": r"""[原始 PythonInterpreterTool 工具流]
Let ans = 1050*sqrt(2).
Return simplify(ans^2).""",

    "output_case_7": r"""def execute():
    import sympy as sp
    ans = 1050 * sp.sqrt(2)
    return sp.simplify(ans**2)
execute()""",

    "input_case_8": r"""[原始 PythonInterpreterTool 工具流]
O = {A, B, C}.
r(A) = round_to_nearest_tenth(14.45001)
r(B) = round_to_nearest_tenth(14.54999)
r(C) = round_to_nearest_tenth(14.44999)
m = min {r(o) for o in O}
V = {o in O : r(o) = m}
Return r, m, and V.""",

    "output_case_8": r"""def execute():
    from decimal import Decimal, ROUND_HALF_UP
    values = {
        "A": Decimal("14.45001"),
        "B": Decimal("14.54999"),
        "C": Decimal("14.44999"),
    }
    r = {
        key: value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        for key, value in values.items()
    }
    m = min(r.values())
    V = [key for key, value in r.items() if value == m]
    return {"r": r, "m": m, "V": V}
execute()""",

    "input_template": r"""[原始 PythonInterpreterTool 工具流]
{original_code}"""
}
````

## 8. `extract_prompt`（A8：答案抽取器）

来源：`upstream/progco/MATH/extract_answer.py`

````python
extract_prompt="你的任务是从给定题目和解答过程中准确抽取最终答案。请仔细阅读整个问题和解答过程，以找到最终答案。\n\n重要说明：\n1. 只抽取最终答案，不包含单位或其他文字解释。\n2. 不要输出任何额外内容，例如 \\boxed{{}} 包裹等。\n3. 对于多个答案，使用列表格式输出。\n\n答案可以有多种形式，包括但不限于：\n\n1. 整数或小数：10, -1.5\n2. 分数：\\frac{{1}}{{2}}, -\\frac{{3}}{{4}}\n3. 文本答案：even, odd\n4. 平方根表达式：\\sqrt{{10}}, \\sqrt[3]{{8}}\n5. 常数：π, e\n6. 代数表达式：a+1, y = x + 1\n7. 选择题选项：A, B, C, D\n8. 矩阵（使用 LaTeX 格式）：\n   \\begin{{bmatrix}}\n   1 & 2 \\\\\n   3 & 4\n   \\end{{bmatrix}}\n\n题目如下：\n{query}\n\n解答如下：\n{response}\n\n再次确认，你的输出只能包含最终答案，不要包含任何额外解释或格式。"
````

## 9. 上下文压缩（A21）

来源：

- `mod_C0_compress/prompts/context_compress.md`
- `mod_C0_compress/prompts/context_compress_user.md`

说明：以下中文内容仅用于文档说明；运行时读取英文提示词。

### 系统提示词

```text
你是上下文压缩智能体。

将给定的工作上下文压缩为简洁、连贯的摘要，使后续模型能够根据摘要继续当前任务。

保留：
1. 当前任务和重要要求。
2. 已完成的重要工作和关键结论。
3. 重要计算结果、工具结果、错误原因，以及已经证明无效的方法。
4. 尚未完成的事项和下一步工作。

删除重复、无关和已经过时的信息。
不要添加或推断原始上下文中不存在的信息。

只输出压缩后的文本。不要输出 JSON、标签、解释或任何其他内容。
```

### 用户提示词

```text
## 待压缩上下文

{context}
```

### 运行时上下文格式

较早历史压缩后使用以下标记：

```text
[Compressed Earlier Context]
```

待压缩消息序列化格式为：

```text
[{role}]
{content}
```

## 10. 重复成功 Tool Flow 的运行时后续消息

来源：`repro/scripts/math_hard_test_parallel_python_tool.py`

这些内容不属于静态系统提示词。同一个 `<tool_flow>` 已经成功完成后，如果模型再次请求完全相同的 `<tool_flow>`，控制器会返回缓存结果，并追加以下一条中性的用户后续消息。重复请求仍计入现有的 PythonInterpreterTool 软限制和硬限制。

### 第一次重复请求

```text
这个完全相同的 <tool_flow> 已经成功执行过。

缓存的执行结果是：
{successful_tool_result}

请直接使用该结果继续当前验证，无需重新执行相同的 <tool_flow>。
```

### 第二次及后续重复请求

```text
上述 <tool_flow> 已经有可用的成功执行结果。

缓存的执行结果仍然是：
{successful_tool_result}

请沿用该结果继续当前验证，不必再次运行相同的 <tool_flow>。
```
