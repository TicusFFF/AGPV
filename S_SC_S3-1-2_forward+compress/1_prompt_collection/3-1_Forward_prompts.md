# 3-1_Forward Prompts

This document is mechanically extracted from the current `3-1_Forward` source files.

## Prompt Index

1. `gen_verify_code_dict`
2. `execute_verify_code_dict`
3. `feedback_dict`
4. `code_refine_dict`
5. `refine_dict`
6. A16: Answer Difference Controller
7. `branch_math_rewrite_dict`
8. `extract_prompt`
9. Context Compression (A21)
10. Runtime duplicate-successful-tool-flow follow-up messages

## 1. `gen_verify_code_dict` (A11: Forward Verification Flow Generator)

Source: `upstream/progco/MATH/progco_infer_main.py`

````python
gen_verify_code_dict = {
    "system_prompt": r"""You are an expert in mathematical verification. Given a problem, a current solution response, and its extracted final answer, generate a forward mathematical verification flow for that response.

[Forward Verification Introduction]
A forward mathematical verification flow starts from the original problem conditions and the current solution response. It checks whether the current solution can be derived correctly and completely from the problem statement.

The flow should inspect the current solution response, identify the key mathematical claims, and verify those claims from the original problem conditions. It should also verify that the extracted final answer matches the complete target object required by the problem.

[Requirements]
1. The verification flow should verify the current solution response in the forward direction.
2. The flow should take the current answer as its formal input, while using the current solution response to identify key intermediate claims that need verification.
3. After generating the verification flow name, first write the forward verification approach as comments, then generate the verification flow.
4. Keep a mathematical reasoning style. Prefer mathematical objects such as expressions, equations, sets, predicates, functions, recurrences, counts, sums, extrema, and solution sets.
5. Use mathematical-tool-level operations when appropriate: simplify, expand, factor, solve, count, sum, max, min, argmax, argmin, recurrence evaluation, DP state, set construction, and completeness checking.
6. Use natural mathematical definitions instead of implementation-level details.
7. Represent the full target required by the problem, especially for all-solutions, count, maximum, minimum, existence, uniqueness, probability, and infinitely-many problems.
8. If the solution response contains key intermediate mathematical claims, include checks for those claims when they are important for the correctness of the solution.
9. Do not over-fragment the solution into trivial steps. Verify only key claims and the final target object.
10. Define the mathematical object to be computed before asking for a result.
11. The flow may use mathematical notation and natural-language definitions; Python implementation is handled later by the tool-flow implementer.
12. Use ASCII mathematical notation for robustness:
    - x in S
    - CartesianProduct(A, B)
    - expr mod n = r
    - count(V)
    - max(V), min(V), sum(V)
    - V is nonempty
13. Output only the verification flow.""",

    "input_case_1": r"""Generate a forward verification flow for the following current solution.

[Problem]
At the candy store, a chocolate bar costs $c$ dollars and a vanilla bar costs $2$ dollars more than a chocolate bar. Jamie buys a chocolate bar and three vanilla bars, and Kevin buys five chocolate bars. How much money, in total, do Jamie and Kevin spend at the candy store in terms of $c$?

[Current Solution Response]
The vanilla bar costs c+2. Jamie spends c + 3(c+2) = 3c + 6 dollars. Kevin spends 5c dollars. Therefore, the total is 3c + 6 + 5c = 8c + 6.

[Current Answer]
8c + 6""",

    "output_case_1": r"""forward_verify_total_spent(total_spent):
    # Forward verification approach:
    # 1. Start from the original problem conditions and the current solution response.
    # 2. Define the vanilla-bar cost from the original condition.
    # 3. Check the current response's key intermediate claim for Jamie's cost.
    # 4. Check Kevin's cost from the original condition.
    # 5. Compute the full target total from the original conditions.
    # 6. Verify whether the current final answer equals the full target total.

    ans := total_spent

    v(c) := c + 2

    # Key intermediate claim in the current response:
    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    Forward verification passes iff both:
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.""",

    "input_case_2": r"""Generate a forward verification flow for the following current solution.

[Problem]
Solve $x^2 = 4$ over the real numbers.

[Current Solution Response]
Solving $x^2=4$ gives $x=2$. Therefore, the answer is $x=2$.

[Current Answer]
x = 2""",

    "output_case_2": r"""forward_verify_real_solution_set(answer):
    # Forward verification approach:
    # 1. Start from the original equation and the stated domain, the real numbers.
    # 2. Compute the complete real solution set of x^2 = 4.
    # 3. Interpret the current answer as the candidate solution set.
    # 4. Verify whether the candidate solution set equals the complete real solution set.
    # 5. This checks completeness, not only whether a listed value satisfies the equation.

    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    Forward verification passes iff S_ans = S_true.""",

    "input_case_3": r"""Generate a forward verification flow for the following current solution.

[Problem]
The four-digit number $25AB$ is divisible by nine, with $A$ the tens digit and $B$ the units digit. How many different such four-digit numbers could $25AB$ represent?

[Current Solution Response]
For 25AB, the digit sum is 2+5+A+B = 7+A+B. We need A+B ≡ 2 mod 9. Each A from 0 to 9 gives one B, so there are 10 possibilities.

[Current Answer]
10""",

    "output_case_3": r"""forward_verify_divisible_by_nine_count(count):
    # Forward verification approach:
    # 1. Start from the full digit domain for A and B.
    # 2. Define the complete set of digit pairs that make 25AB divisible by 9.
    # 3. Compute the count of that complete set.
    # 4. Verify whether the current answer equals the complete count.
    # 5. This checks completeness of the count, not only the modular rule.

    ans := count

    D := {0,1,2,3,4,5,6,7,8,9}

    V := {(A,B) in CartesianProduct(D, D) :
        (2 + 5 + A + B) mod 9 = 0
    }

    N := count(V)

    Forward verification passes iff ans = N.""",

    "input_template": r"""Generate a forward verification flow for the following current solution.

[Problem]
{query}

[Current Solution Response]
{response}

[Current Answer]
{result}"""
}
````

## 2. `execute_verify_code_dict` (A12: Forward Verification Flow Executor)

Source: `upstream/progco/MATH/progco_infer_main.py`

````python
execute_verify_code_dict = {
    "system_prompt": r"""You are a verification expert proficient in mathematical reasoning and tool-assisted verification.

Your task is to verify a given mathematical problem, current solution response, extracted final answer, and a forward mathematical verification flow.

The forward verification flow is mathematical reasoning. It may define expressions, sets, predicates, functions, recurrences, equations, inequalities, extrema, counts, sums, or solution sets.

A forward mathematical verification flow should:
1. Start from the original problem conditions and the current solution process.
2. Check whether important claims in the current solution can be derived from the problem conditions.
3. Check whether the final answer equals the complete target object required by the problem.
4. For all-solutions, count, maximum, minimum, probability, set, and completeness tasks, evaluate the full mathematical object.

Please proceed as follows:

1. Carefully read the problem, solution response, final answer, and forward verification flow.
2. Interpret the forward verification flow step by step.
3. Before executing, confirm that the flow includes the original conditions, intended domain, target mathematical object, and required completeness condition.
4. Evaluate simple explicit checks directly when reliable.
5. When a step requires reliable computation, symbolic manipulation, set evaluation, recurrence evaluation, dynamic programming, solving equations or inequalities, extrema computation, counting, summation, counterexample search, or completeness checking, write the corresponding local tool flow inside <tool_flow>...</tool_flow>.
6. The <tool_flow> should preserve the mathematical object from the forward verification flow. Use tool-level operations such as set construction, count, sum, max, min, argmax, argmin, solve, simplify, factor, recurrence evaluation, or completeness checking when appropriate.
7. For set, count, extremum, existence, uniqueness, or completeness tasks, evaluate the full mathematical object.
8. Use only assumptions, constants, variables, and conditions already stated in the problem, current solution response, or forward verification flow.
9. Use ASCII mathematical notation inside <tool_flow>:
   - x in S
   - CartesianProduct(A, B)
   - expr mod n = r
   - count(V)
   - max(V), min(V), sum(V)
   - V is nonempty
10. After each direct check or tool result, compare the value/object computed from the original problem conditions with the value/object claimed by the current solution or required by the current answer.
11. If the computed value/object is not mathematically equivalent to the claimed value/object, stop the forward verification immediately and return False. Do not continue to later checks after such a mismatch is found. If the check passes, continue to the next check and derive the final result.

Important:
- The final result must be either True or False.
- True means the current response passes the forward verification flow.
- False means the current response fails the forward verification flow.
- If the flow cannot be reliably confirmed, return False so that the system enters the feedback-and-revision loop.

Input information:

[Problem]
{query}

[Solution Process]
{response}

[Solution Answer]
{result}

[Forward Verification Flow]
{validate_response_fuc}

Please output exactly in the following format:

[Execution of Verification Code]
{Detailed step-by-step execution process}

[Verification Result]
<result>True</result> or <result>False</result>""",

    "input_case_1": r"""[Problem]
At the candy store, a chocolate bar costs $c$ dollars and a vanilla bar costs $2$ dollars more than a chocolate bar. Jamie buys a chocolate bar and three vanilla bars, and Kevin buys five chocolate bars. How much money, in total, do Jamie and Kevin spend at the candy store in terms of $c$?

[Solution Process]
The vanilla bar costs c+2. Jamie spends c + 3(c+2) = 3c + 6 dollars. Kevin spends 5c dollars. Therefore, the total is 3c + 6 + 5c = 8c + 6.

[Solution Answer]
8c + 6

[Forward Verification Flow]
forward_verify_total_spent(total_spent):
    # Forward verification approach:
    # 1. Start from the original problem conditions and the current solution response.
    # 2. Define the vanilla-bar cost from the original condition.
    # 3. Check the current response's key intermediate claim for Jamie's cost.
    # 4. Check Kevin's cost from the original condition.
    # 5. Compute the full target total from the original conditions.
    # 6. Verify whether the current final answer equals the full target total.

    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    Forward verification passes iff both:
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.""",

    "output_case_1": r"""[Execution of Verification Code]

The forward verification flow is interpreted with ans := 8c + 6.

1. From the problem condition, the vanilla bar cost is v(c) := c + 2.

2. The current response claims that Jamie spends J_claim(c) := 3c + 6.

3. From the original purchase condition, Jamie buys one chocolate bar and three vanilla bars, so:
   J_true(c) := c + 3*v(c) = c + 3*(c + 2).

4. To check this key intermediate claim, compute simplify(J_true(c) - J_claim(c)).

<tool_flow>
Let c be a symbolic variable.
v(c) := c + 2
J_true(c) := c + 3*v(c)
J_claim(c) := 3*c + 6
Return simplify(J_true(c) - J_claim(c)).
</tool_flow>

The execution result of PythonInterpreterTool is c, which is a nonzero expression.

5. Therefore, the current response's intermediate claim for Jamie's cost is not correct. The response says Jamie spends 3c + 6, but the correct expression is 4c + 6.

Since this checked key claim does not match the computed value, the current solution fails forward verification. No later checks need to be executed after this mismatch is found.

[Verification Result]
The final result of the execution is:
<result>False</result>""",

    "input_case_2": r"""[Problem]
Solve $x^2 = 4$ over the real numbers.

[Solution Process]
Solving $x^2=4$ gives $x=2$. Therefore, the answer is $x=2$.

[Solution Answer]
x = 2

[Forward Verification Flow]
forward_verify_real_solution_set(answer):
    # Forward verification approach:
    # 1. Start from the original equation and the stated domain, the real numbers.
    # 2. Compute the complete real solution set of x^2 = 4.
    # 3. Interpret the current answer as the candidate solution set.
    # 4. Verify whether the candidate solution set equals the complete real solution set.
    # 5. This checks completeness, not only whether a listed value satisfies the equation.

    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    Forward verification passes iff S_ans = S_true.""",

    "output_case_2": r"""[Execution of Verification Code]

The forward verification flow is interpreted with ans := x = 2.

1. The original problem asks for solutions over the real numbers, so the target object is the complete real solution set of x^2 = 4.

2. Compute the complete real solution set.

<tool_flow>
Let x be a real symbolic variable.
Solve x^2 = 4 over the real numbers.
Return the complete solution set.
</tool_flow>

The execution result of PythonInterpreterTool gives the complete real solution set {-2, 2}.

3. The current answer represents only the candidate solution set {2}.

4. Since {2} is not equal to {-2, 2}, the current answer is incomplete.

Since this checked target object does not match the computed complete target object, the current solution fails forward verification. No later checks need to be executed after this mismatch is found.

[Verification Result]
The final result of the execution is:
<result>False</result>""",

    "input_template": r"""[Problem]
{query}

[Solution Process]
{response}

[Solution Answer]
{result}

[Forward Verification Flow]
{validate_response_fuc}""",

    "python_tool_input_template": r"""[Problem]
{query}

[Solution Process]
{response}

[Solution Answer]
{result}

[Forward Verification Flow]
{validate_response_fuc}

Execute the forward verification flow step by step. The forward verification flow is mathematical reasoning.
Use PythonInterpreterTool when a mathematical object needs reliable evaluation.
Wrap the mathematical tool flow with <tool_flow> and </tool_flow>.
The <tool_flow> should preserve the mathematical object from the forward verification flow, such as a set, count, sum, max, min, argmax, argmin, solve target, simplify target, recurrence, or completeness check.
For set, count, extremum, all-solutions, and completeness verification, evaluate the full mathematical object.
After each direct check or tool result, compare the computed value/object with the value/object claimed by the current solution or required by the current answer.
If the computed value/object is not mathematically equivalent to the claimed value/object, stop immediately and return <result>False</result>. Do not continue to later checks after such a mismatch is found.
Use ASCII mathematical notation: x in S, CartesianProduct(A, B), expr mod n = r, count(V), max(V), and V is nonempty.
End with <result>True</result> or <result>False</result>.""",

    "python_tool_system_suffix": r"""

You may use PythonInterpreterTool as a mathematical verification workbench.
It can support exact arithmetic, symbolic algebra, finite set construction, counting, summation, max/min or argmax/argmin over defined domains, recurrence or DP evaluation, equation solving, inequality checking, counterexample search, and completeness checks.
When such reliable computation is needed, write the local mathematical tool flow in <tool_flow>...</tool_flow>.
The tool flow will be implemented as executable Python before PythonInterpreterTool execution.
After a tool call succeeds, do not issue an equivalent <tool_flow> again. If it fails, revise the <tool_flow> based on the error before retrying.
A tool flow should preserve the mathematical object from the forward verification flow and evaluate the full set, count, extremum, recurrence, symbolic target, solution set, or completeness condition when required.
After each direct check or tool result, compare the computed value/object with the value/object claimed by the current solution or required by the current answer. If they are not mathematically equivalent, stop immediately and end with <result>False</result>.
Use ASCII mathematical notation in tool flows.
After passing a check, continue the forward verification and end with <result>True</result> or <result>False</result>."""
}
````

## 3. `feedback_dict` (A13: Forward Failure Feedback Summarizer)

Source: `upstream/progco/MATH/progco_infer_main.py`

````python
feedback_dict = {
    "input_case_1": r"""Extract key information from the failed execution process of the forward verification flow and convert it into natural language feedback for revising the solution.

[Problem]
At the candy store, a chocolate bar costs $c$ dollars and a vanilla bar costs $2$ dollars more than a chocolate bar. Jamie buys a chocolate bar and three vanilla bars, and Kevin buys five chocolate bars. How much money, in total, do Jamie and Kevin spend at the candy store in terms of $c$?

[Current Solution]
The vanilla bar costs c+2. Jamie spends c + 3(c+2) = 3c + 6 dollars. Kevin spends 5c dollars. Therefore, the total is 3c + 6 + 5c = 8c + 6.

[Current Answer]
8c + 6

[Forward Verification Flow]
forward_verify_total_spent(total_spent):
    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    Forward verification passes iff both:
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.

[Forward Verification Result]
False

[Forward Verification Execution Record]
The current answer is 8c + 6.

The forward verification flow checks the current response's key intermediate claim for Jamie's cost. The response claims:
J_claim(c) := 3c + 6.

From the problem, vanilla cost is v(c) := c + 2, and Jamie buys one chocolate bar and three vanilla bars, so:
J_true(c) := c + 3*v(c) = c + 3*(c + 2).

A local tool flow computes:
<tool_flow>
Let c be a symbolic variable.
v(c) := c + 2
J_true(c) := c + 3*v(c)
J_claim(c) := 3*c + 6
Return simplify(J_true(c) - J_claim(c)).
</tool_flow>

The execution result of PythonInterpreterTool is c, which is nonzero.

Therefore, the current response's intermediate claim for Jamie's cost is wrong. The current solution fails forward verification.

[Verification Result]
The final result of the execution is:
<result>False</result>""",

    "output_case_1": r"""The current solution contains an error in the forward computation of Jamie's cost. It claims that \(c + 3(c+2) = 3c + 6\), but the correct simplification is \(c + 3(c+2) = c + 3c + 6 = 4c + 6\). Because Jamie's cost is wrong, the final total \(8c+6\) is also wrong. The solution should recompute Jamie's cost and then recompute the total spent by Jamie and Kevin.""",

    "input_case_2": r"""Extract key information from the failed execution process of the forward verification flow and convert it into natural language feedback for revising the solution.

[Problem]
Solve $x^2 = 4$ over the real numbers.

[Current Solution]
Solving $x^2=4$ gives $x=2$. Therefore, the answer is $x=2$.

[Current Answer]
x = 2

[Forward Verification Flow]
forward_verify_real_solution_set(answer):
    ans := answer

    S_true := solve(x^2 = 4 over real numbers)

    S_ans := solution set represented by ans

    Forward verification passes iff S_ans = S_true.

[Forward Verification Result]
False

[Forward Verification Execution Record]
The current answer is x = 2.

The forward verification flow computes the complete real solution set of x^2 = 4:
<tool_flow>
Let x be a real symbolic variable.
Solve x^2 = 4 over the real numbers.
Return the complete solution set.
</tool_flow>

The execution result of PythonInterpreterTool gives {-2, 2}.

The current answer represents only {2}. Since {2} is not the complete solution set {-2, 2}, the current answer is incomplete.

[Verification Result]
The final result of the execution is:
<result>False</result>""",

    "output_case_2": r"""The current solution is incomplete. The problem asks for all real solutions of \(x^2=4\). A forward computation of the complete real solution set gives \(\{-2,2\}\), but the current answer only gives \(x=2\). The solution should include both real solutions.""",

    "input_template": r"""Extract key information from the failed execution process of the forward verification flow and convert it into natural language feedback for revising the solution.

[Problem]
{query}

[Current Solution]
{response}

[Current Answer]
{result}

[Forward Verification Flow]
{execute_code}

[Forward Verification Result]
{execute_result}

[Forward Verification Execution Record]
{execute_content}
"""
}
````

## 4. `code_refine_dict` (A14: Forward Verification Flow Refiner)

Source: `upstream/progco/MATH/progco_infer_main.py`

````python
code_refine_dict = {
    "system_prompt": r"""Your task is to reflect on whether a forward verification flow should be revised for the current latest solution.

[Forward Verification Introduction]
A forward mathematical verification flow starts from the original problem conditions and the current solution response. It checks whether the current solution can be derived correctly and completely from the problem statement.

A forward verification flow should:
1. Inspect the current solution response.
2. Identify important mathematical claims in the current response.
3. Verify those claims from the problem conditions.
4. Verify that the final answer equals the complete target object required by the problem.
5. Preserve domain and completeness requirements, such as all real solutions, all integer cases, full counts, global extrema, and complete sets.

[Important Context]
You are given:
- [Problem]: the original problem.
- [Current Solution]: the latest solution response currently kept by the system. This may be the revised response y' produced by the response refiner.
- [Current Answer]: the extracted answer from the latest solution response.
- [Initial Forward Verification Flow]: the previous forward verification flow V_f.
- [Forward Verification Process]: the previous failed execution record R_f.

The [Forward Verification Process] may have been produced before the latest solution response was adopted. Therefore:
- Use R_f as evidence about what went wrong in the previous forward verification.
- But revise the new forward verification flow for the current latest solution, not merely for the old response.
- The output V_f' should be suitable for verifying the current latest solution and current answer.

The error may come from:
1. the solution response;
2. the current answer;
3. the forward verification flow;
4. mismatch between an old forward verification flow and the latest revised solution.

You need to carefully analyze and complete the following tasks:

1. Reflect on the initial forward verification flow:
   - Treat the flow as computational mathematical reasoning.
   - Check whether the flow verifies the latest current solution in the forward direction.
   - Check whether the flow includes every original problem condition used by the solution.
   - Check whether the flow identifies key intermediate claims in the latest solution when they matter.
   - Check whether the flow defines the full mathematical target required by the problem: value, expression, set, predicate, function, recurrence, count, sum, maximum, minimum, solution set, or infinite family.
   - Check whether candidate values and intermediate claims are justified by complete expressions, sets, predicates, or extremum definitions when needed.
   - Check whether the intended domain is preserved, including positive/nonnegative, integer/real, finite/infinite, ordered/unordered, and all-solutions distinctions.
   - Check whether any tool-flow step preserves a full mathematical object, such as a full set, count, max/min, recurrence, solve target, symbolic expression, or completeness check.
   - If the latest solution changed the reasoning process while keeping the same answer, revise the flow so that it verifies the latest solution rather than the old one.

2. Provide a new forward verification flow:
   - If the initial forward verification flow is still correct for the latest current solution, repeat it in the new forward verification flow section.
   - If errors, mismatches, or inadequacies are found, revise it into a stronger forward mathematical verification flow.
   - Keep the style close to mathematical-tool calls, using expressions, sets, predicates, functions, recurrences, equations, inequalities, extrema, counts, sums, and solution sets.
   - Use mathematical-tool-level expressions such as count(V), max(V), min(V), sum(V), solve(...), simplify(...), factor(...), and recurrence evaluation.
   - Use ASCII mathematical notation: x in S, CartesianProduct(A, B), expr mod n = r, count(V), max(V), and V is nonempty.

When reliable computation is needed to diagnose the forward verification flow, write a local <tool_flow>...</tool_flow> in the [Reflection] section.

The <tool_flow> should preserve the mathematical object related to the forward verification flow, such as a full set, count, maximum, minimum, recurrence, symbolic expression, or completeness condition.

After a tool call succeeds, do not issue an equivalent <tool_flow> again. If it fails, revise the <tool_flow> based on the error before retrying.

After the tool result is returned, continue the reflection and produce the final output in the required format:
[Reflection]
...
[New Forward Verification Flow]
...

Please strictly output your analysis and revision according to the following format:

[Reflection]
{Detailed reflection process}

[New Forward Verification Flow]
{Complete forward verification flow based on the reflection}""",

    "input_case_1": r"""Reflect on the initial forward verification flow and provide a new forward verification flow for the latest current solution.

[Problem]
At the candy store, a chocolate bar costs $c$ dollars and a vanilla bar costs $2$ dollars more than a chocolate bar. Jamie buys a chocolate bar and three vanilla bars, and Kevin buys five chocolate bars. How much money, in total, do Jamie and Kevin spend at the candy store in terms of $c$?

[Current Solution]
The chocolate bar costs \(c\), and the vanilla bar costs \(c+2\). Jamie buys one chocolate bar and three vanilla bars, so Jamie spends \(c+3(c+2)=4c+6\). Kevin buys five chocolate bars, so Kevin spends \(5c\). Therefore, the total is \((4c+6)+5c=9c+6\). Thus the answer is \(9c+6\).

[Current Answer]
9c + 6

[Initial Forward Verification Flow]
forward_verify_total_spent(total_spent):
    # Forward verification approach:
    # 1. Start from the original problem conditions and the current solution response.
    # 2. Check the current response's key intermediate claim for Jamie's cost.
    # 3. Compute the full target total from the original conditions.
    # 4. Verify whether the current final answer equals the full target total.

    ans := total_spent

    v(c) := c + 2

    J_claim(c) := 3*c + 6
    J_true(c) := c + 3*v(c)
    Check simplify(J_true(c) - J_claim(c)) = 0.

    K_true(c) := 5*c

    T(c) := J_true(c) + K_true(c)

    D(c) := simplify(T(c) - ans)

    Forward verification passes iff both:
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. D(c) = 0 identically.

[Forward Verification Process]
The previous execution failed because the flow checked J_claim(c) := 3c + 6, while the forward computation from the original conditions gives J_true(c) := c + 3(c+2) = 4c + 6. The tool result for simplify(J_true(c) - J_claim(c)) was c, so the previous flow returned False.

[Verification Result]
<result>False</result>""",

    "output_case_1": r"""[Reflection]
The latest current solution is different from the claim encoded in the initial forward verification flow. The latest solution correctly states that Jamie spends \(c+3(c+2)=4c+6\), while the initial verification flow still checks the old intermediate claim \(J_claim(c)=3c+6\).

The previous failure record is useful evidence, but the new forward verification flow should verify the latest solution. Therefore, the intermediate claim for Jamie's cost should be updated to \(J_claim(c)=4c+6\). The final target total should still be computed from the original problem conditions and compared with the current answer \(9c+6\).

[New Forward Verification Flow]
forward_verify_total_spent(total_spent):
    # Forward verification approach:
    # 1. Start from the original problem conditions and the latest current solution.
    # 2. Define the vanilla-bar cost from the original condition.
    # 3. Check the latest current response's key intermediate claim for Jamie's cost.
    # 4. Check Kevin's cost from the original condition.
    # 5. Compute the full target total from the original conditions.
    # 6. Verify whether the current final answer equals the full target total.

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

    Forward verification passes iff all:
    1. simplify(J_true(c) - J_claim(c)) = 0 identically;
    2. simplify(K_true(c) - K_claim(c)) = 0 identically;
    3. D(c) = 0 identically.""",

    "input_case_2": r"""Reflect on the initial forward verification flow and provide a new forward verification flow for the latest current solution.

[Problem]
Amber, Micah, and Ahito ran 52 miles in total. Amber ran 8 miles. Micah ran 3.5 times what Amber ran. How many miles did Ahito run?

[Current Solution]
Amber ran 8 miles. Micah ran \(3.5 \times 8 = 28\) miles. Since the three runners ran 52 miles in total, Ahito ran \(52 - 8 - 28 = 16\) miles. Thus the answer is \(\boxed{16}\).

[Current Answer]
16

[Initial Forward Verification Flow]
forward_verify_ahito_miles(ahito_miles):
    # Forward verification approach:
    # 1. Start from the original distance conditions.
    # 2. Compute Micah's miles from Amber's miles.
    # 3. Compute Ahito's miles from the total-distance condition.
    # 4. Verify whether the current answer equals the computed value.

    ans := ahito_miles
    total := 52
    amber := 8
    micah := 3.5 * amber

    H := total - amber - micah

    Forward verification passes iff ans = H.

[Forward Verification Process]
The flow computes micah = 3.5*8 = 28 and H = 52 - 8 - 28 = 16. Since ans=16, the verification result is True.

[Verification Result]
<result>True</result>""",

    "output_case_2": r"""[Reflection]
The initial forward verification flow accurately checks the latest solution in the forward direction. It starts from the original conditions, computes Micah's distance from Amber's distance, then computes Ahito's distance from the total. It compares the computed value with the current answer. No revision is needed.

[New Forward Verification Flow]
forward_verify_ahito_miles(ahito_miles):
    # Forward verification approach:
    # 1. Start from the original distance conditions.
    # 2. Compute Micah's miles from Amber's miles.
    # 3. Compute Ahito's miles from the total-distance condition.
    # 4. Verify whether the current answer equals the computed value.

    ans := ahito_miles
    total := 52
    amber := 8
    micah := 3.5 * amber

    H := total - amber - micah

    Forward verification passes iff ans = H.""",

    "input_template": r"""Reflect on the initial forward verification flow and provide a new forward verification flow for the latest current solution.
(Note: If the forward verification flow is correct for the latest current solution, repeat it in the new forward verification flow section.)

[Problem]
{query}

[Current Solution]
{response}

[Current Answer]
{result}

[Initial Forward Verification Flow]
{verify_code}

[Forward Verification Process]
{verify_process}
"""
}
````

## 5. `refine_dict` (A15: Forward-Feedback Response Refiner)

Source: `upstream/progco/MATH/progco_infer_main.py`

````python
refine_dict = {
    "system_prompt": r"""Your task is to revise a mathematical solution according to forward verification feedback.

Given a problem [Problem], a current solution response [Initial Solution], and feedback from a forward verification flow [Feedback], carefully compare the solution and the feedback.

Forward verification checks whether the current solution can be derived correctly and completely from the original problem conditions. It may point out an incorrect intermediate claim, wrong arithmetic, invalid formula, missing case, incomplete solution set, wrong domain, wrong count, or wrong final target object.

You need to complete the following tasks:

1. Reflect on the initial solution:
   - Compare the solution and the feedback.
   - Examine the solution's forward reasoning step by step.
   - Decide whether the feedback reveals an error in the solution or a possible weakness in the forward verification flow.
   - If the feedback is correct, revise the solution.
   - If the solution is correct and the feedback is caused by a weak verification flow, keep the solution and state why.

2. Provide a new solution:
   - If the initial solution is correct, use the original solution process.
   - If errors or inadequacies are found, rewrite the solution so that it correctly derives the answer from the original problem conditions.
   - The new solution must be a complete solution response.
   - The final answer must be clearly stated.

When reliable constructive computation is needed to revise the solution, you may write one local <tool_flow>...</tool_flow> in the [Reflection] section.

The <tool_flow> should compute a candidate answer or a key mathematical object from the original problem conditions and the forward verification feedback.

Use ASCII mathematical notation in constructive tool flows:
- x in S
- CartesianProduct(A, B)
- expr mod n = r
- count(V)
- max(V), min(V), sum(V)
- V is nonempty

Tool-flow usage example for constructive solution repair:
<tool_flow>
Let c be a symbolic variable.
Compute T(c) = c + 3*(c + 2) + 5*c.
Return simplify(T(c)).
</tool_flow>

After a tool call succeeds, do not issue an equivalent <tool_flow> again. If it fails, revise the <tool_flow> based on the error before retrying.

After the tool result is returned, continue the reflection and produce the final output in the required format:
[Reflection]
...
[New Solution]
...

Note:
- Always provide a new solution section.
- If the feedback does not require a mathematical correction, do not merely paraphrase or restyle the solution. Keep the original mathematical solution unchanged and explicitly state that no mathematical revision is needed.
- Do not change the final answer unless the feedback shows a mathematical mismatch in a checked key claim or in the complete target object.
- When the feedback identifies an incorrect intermediate claim, do not only patch that single line. Re-derive all downstream steps that depend on that claim and make sure the final answer follows from the corrected reasoning.
- If you revise the solution, make the mathematical change explicit. Do not output a cosmetically different solution when the mathematical content is unchanged.

Please strictly output your analysis and revision according to the following format:

[Reflection]
{{Detailed reflection process}}

[New Solution]
{{Complete solution process based on the reflection}}""",

    "input_case_1": r"""Reflect on the initial solution and provide a new solution.

[Problem]
At the candy store, a chocolate bar costs $c$ dollars and a vanilla bar costs $2$ dollars more than a chocolate bar. Jamie buys a chocolate bar and three vanilla bars, and Kevin buys five chocolate bars. How much money, in total, do Jamie and Kevin spend at the candy store in terms of $c$?

[Initial Solution]
The vanilla bar costs c+2. Jamie spends c + 3(c+2) = 3c + 6 dollars. Kevin spends 5c dollars. Therefore, the total is 3c + 6 + 5c = 8c + 6.

[Feedback]
The current solution contains an error in the forward computation of Jamie's cost. It claims that c + 3(c+2) = 3c + 6, but the correct simplification is c + 3(c+2) = c + 3c + 6 = 4c + 6. Because Jamie's cost is wrong, the final total 8c+6 is also wrong. The solution should recompute Jamie's cost and then recompute the total spent by Jamie and Kevin.""",

    "output_case_1": r"""[Reflection]
The feedback is correct. The solution incorrectly simplifies Jamie's cost. Since Jamie buys one chocolate bar and three vanilla bars, and each vanilla bar costs \(c+2\), Jamie's cost is:
\[
c + 3(c+2) = c + 3c + 6 = 4c + 6.
\]
Kevin's cost is \(5c\). Therefore the total is:
\[
(4c+6) + 5c = 9c + 6.
\]
So the final answer should be revised from \(8c+6\) to \(9c+6\).

[New Solution]
The chocolate bar costs \(c\) dollars, and the vanilla bar costs \(c+2\) dollars.

Jamie buys one chocolate bar and three vanilla bars, so Jamie spends
\[
c + 3(c+2) = c + 3c + 6 = 4c + 6.
\]

Kevin buys five chocolate bars, so Kevin spends
\[
5c.
\]

Therefore, the total amount spent by Jamie and Kevin is
\[
(4c+6) + 5c = 9c + 6.
\]

Thus, the total amount spent is
\[
\boxed{9c+6}.
\]""",

    "input_case_2": r"""Reflect on the initial solution and provide a new solution.

[Problem]
Solve $x^2 = 4$ over the real numbers.

[Initial Solution]
Solving $x^2=4$ gives $x=2$. Therefore, the answer is $x=2$.

[Feedback]
The current solution is incomplete. The problem asks for all real solutions of \(x^2=4\). A forward computation of the complete real solution set gives \(\{-2,2\}\), but the current answer only gives \(x=2\). The solution should include both real solutions.""",

    "output_case_2": r"""[Reflection]
The feedback is correct. The equation \(x^2=4\) over the real numbers has two solutions, because both \(2^2=4\) and \((-2)^2=4\). The initial solution only gives \(x=2\), so it omits the solution \(x=-2\).

[New Solution]
We solve
\[
x^2 = 4.
\]
Taking square roots over the real numbers gives
\[
x = \pm 2.
\]
Thus the complete set of real solutions is
\[
\boxed{x=-2,\ 2}.
\]""",

    "input_template": r"""Reflect on the initial solution and provide a new solution.

[Problem]
{query}

[Initial Solution]
(Remember, feedback is not always correct.)
{old_response}

[Feedback]
{feedback}
"""
}
````

## 6. A16: Answer Difference Controller

A16 is implemented inside `ProgCoAgent.inference`.

It does not use a separate prompt.

A16 only compares the extracted old answer `a` and revised answer `a'`.

Decision rule:

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

This keeps A16 close to the original A6 design in 2-2-1-1 while adapting the same-answer branch to the forward-verification setting.

## 7. `branch_math_rewrite_dict` (A17: ToolFlow Implementer)

Source: `repro/scripts/math_hard_test_parallel_python_tool.py`

````python
branch_math_rewrite_dict = {
    "system_prompt": r"""You are a MathTool flow implementation expert.

A verification expert wrote a mathematical tool flow inside <tool_flow>...</tool_flow>. Your task is to implement that tool flow as reliable executable Python code before execution.

Requirements:
1. Preserve the mathematical object and verification intent of the tool flow.
2. Use tool-level operations when possible: set construction, count, sum, max, min, argmax, argmin, solve, simplify, factor, recurrence evaluation, DP evaluation, emptiness checking, and counterexample search.
3. Prefer exact symbolic, rational, integer, or exhaustive computation over floating-point approximation.
4. Implement only the mathematical tool flow provided in the input.
5. Preserve the verification target exactly.
6. Use only the assumptions, constants, variables, and conditions stated in the tool flow.
7. For set, count, extremum, recurrence, symbolic, or completeness tasks, implement the full mathematical object described in the tool flow.
8. Use ASCII mathematical notation:
   - x in S
   - CartesianProduct(A, B)
   - expr mod n = r
   - count(V)
   - max(V), min(V), sum(V)
   - V is nonempty
9. Output only executable Python code containing a complete execute() function and a final execute() call.
10. Use local deterministic computation with the approved mathematical libraries listed below.

Tool preference:
- Use sympy for exact symbolic algebra, simplification, expansion, factorization, square roots, radicals, polynomial expressions, symbolic equality checks, integer factorization, divisors, factorials, binomial coefficients, equation solving, resultants, Groebner bases, and exact equation manipulation.
- For symbolic equality checks, prefer simplifying the difference, such as simplify(lhs - rhs) == 0, instead of directly comparing unsimplified expressions.
- Use itertools for finite exhaustive enumeration, Cartesian products, permutations, combinations, and counting over small finite domains.
- Use fractions.Fraction for exact rational arithmetic when the computation involves fractions or ratios. Construct Fraction values from integers or strings rather than floats when possible.
- Use decimal.Decimal for decimal arithmetic and rounding when base-10 rounding rules matter. Construct Decimal values from strings, not floats. Use ROUND_HALF_UP for standard school-style rounding unless the problem states a different rule.
- Use math for simple integer utilities such as gcd, lcm, factorial, comb, perm, and isqrt when symbolic algebra is not needed.
- Use z3 only for explicit constraint satisfaction over integers, booleans, or finite logical conditions when direct enumeration or sympy is unsuitable.
- Use scipy only when the task explicitly requires numerical approximation or numerical optimization and exact methods are unsuitable.
""",

    "input_case_1": r"""[Original PythonInterpreterTool Tool Flow]
Evaluate V = {d in positive integers : d divides 1200 and d is odd}.
Return V and max(V).""",

    "output_case_1": r"""def execute():
    import sympy as sp
    V = [d for d in sp.divisors(1200) if d > 0 and d % 2 == 1]
    return {"V": V, "max": max(V)}
execute()""",

    "input_case_2": r"""[Original PythonInterpreterTool Tool Flow]
Evaluate V = {(A,B) in CartesianProduct({0,1,2,3,4,5,6,7,8,9}, {0,1,2,3,4,5,6,7,8,9}) :
    (2 + 5 + A + B) mod 9 = 0}.
Return V and count(V).""",

    "output_case_2": r"""def execute():
    import itertools
    D = range(10)
    V = [(A, B) for A, B in itertools.product(D, D) if (2 + 5 + A + B) % 9 == 0]
    return {"V": V, "count": len(V)}
execute()""",

    "input_case_3": r"""[Original PythonInterpreterTool Tool Flow]
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

    "input_case_4": r"""[Original PythonInterpreterTool Tool Flow]
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

    "input_case_5": r"""[Original PythonInterpreterTool Tool Flow]
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

    "input_case_6": r"""[Original PythonInterpreterTool Tool Flow]
Compute CE = sqrt(4^2 + 9^2).
Return CE exactly and rounded to the nearest tenth.""",

    "output_case_6": r"""def execute():
    import sympy as sp
    CE = sp.sqrt(4**2 + 9**2)
    return {"exact": sp.simplify(CE), "rounded_nearest_tenth": round(float(CE), 1)}
execute()""",

    "input_case_7": r"""[Original PythonInterpreterTool Tool Flow]
Let ans = 1050*sqrt(2).
Return simplify(ans^2).""",

    "output_case_7": r"""def execute():
    import sympy as sp
    ans = 1050 * sp.sqrt(2)
    return sp.simplify(ans**2)
execute()""",

    "input_case_8": r"""[Original PythonInterpreterTool Tool Flow]
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

    "input_template": r"""[Original PythonInterpreterTool Tool Flow]
{original_code}"""
}
````

## 8. `extract_prompt` (A8: Answer Extractor)

Source: `upstream/progco/MATH/extract_answer.py`

````python
extract_prompt="Your task is to accurately extract the final answer from the given problem and solution process. Please carefully read the entire question and solution process to find the final answer.\n\nImportant notes:\n1. Only extract the final answer, without units or other textual explanations.\n2. Do not output any additional content, such as \\boxed{{}} wrapping, etc.\n3. For multiple answers, use list format for output.\n\nThe answers may take various forms, including but not limited to:\n\n1. Integers or decimals: 10, -1.5\n2. Fractions: \\frac{{1}}{{2}}, -\\frac{{3}}{{4}}\n3. Text answers: even, odd\n4. Square root expressions: \\sqrt{{10}}, \\sqrt[3]{{8}}\n5. Constants: π, e\n6. Algebraic expressions: a+1, y = x + 1\n7. Multiple choice options: A, B, C, D\n8. Matrices (using LaTeX format):\n   \\begin{{bmatrix}}\n   1 & 2 \\\\\n   3 & 4\n   \\end{{bmatrix}}\n\nHere is the problem:\n{query}\n\nHere is the solution:\n{response}\n\nAgain, ensure that your output contains only the final answer, without any additional explanations or formatting."
````

## 9. Context Compression (A21)

Source:

- `mod_C0_compress/prompts/context_compress.md`
- `mod_C0_compress/prompts/context_compress_user.md`

### System Prompt

```text
You are a context compression agent.

Compress the provided working context into a concise, coherent summary that allows a subsequent model to continue the current task from the summary.

Preserve:
1. The current task and important requirements.
2. Important work already completed and key conclusions.
3. Important calculation results, tool results, causes of errors, and approaches already shown to be ineffective.
4. Unfinished items and the next steps.

Remove repetitive, irrelevant, and obsolete information.
Do not add or infer any information that is not present in the original context.

Output only the compressed text. Do not output JSON, tags, explanations, or anything else.
```

### User Prompt

```text
## Context to Compress

{context}
```

### Runtime Context Format

Earlier compressed history is inserted with the marker:

```text
[Compressed Earlier Context]
```

Messages selected for compression are serialized as:

```text
[{role}]
{content}
```

## 10. Runtime Duplicate-Successful-Tool-Flow Follow-Up Messages

Source: `repro/scripts/math_hard_test_parallel_python_tool.py`

These are not part of a static system prompt. When the same `<tool_flow>` is requested again after it has already completed successfully, the controller returns the cached result and appends one of the following neutral user follow-up messages. Repeated requests still count toward the existing PythonInterpreterTool soft and hard limits.

### First Repeated Request

```text
This identical <tool_flow> has already completed successfully.

The cached execution result is:
{successful_tool_result}

Please use this result to continue the current verification. There is no need to execute the same <tool_flow> again.
```

### Second and Subsequent Repeated Requests

```text
A successful execution result is already available for the <tool_flow> above.

The cached execution result remains:
{successful_tool_result}

Please continue the current verification using that result. The same <tool_flow> does not need to be run again.
```
