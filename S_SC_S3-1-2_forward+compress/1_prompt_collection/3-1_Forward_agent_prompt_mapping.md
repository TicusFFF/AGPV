# 3-1_Forward Agent / Prompt Mapping

This prompt collection is extracted from the current `3-1_Forward` source files.

## Agent Mapping

| Agent | Role                                | Prompt / Constant          | Source                                                 |
|-------|-------------------------------------|----------------------------|--------------------------------------------------------|
| A11   | Forward Verification Flow Generator | `gen_verify_code_dict`     | `upstream/progco/MATH/progco_infer_main.py`            |
| A12   | Forward Verification Flow Executor  | `execute_verify_code_dict` | `upstream/progco/MATH/progco_infer_main.py`            |
| A13   | Forward Failure Feedback Summarizer | `feedback_dict`            | `upstream/progco/MATH/progco_infer_main.py`            |
| A14   | Forward Verification Flow Refiner   | `code_refine_dict`         | `upstream/progco/MATH/progco_infer_main.py`            |
| A15   | Forward-Feedback Response Refiner   | `refine_dict`              | `upstream/progco/MATH/progco_infer_main.py`            |
| A16   | Answer Difference Controller        | `ProgCoAgent.inference`    | `upstream/progco/MATH/progco_infer_main.py`            |
| A17   | ToolFlow Implementer                | `branch_math_rewrite_dict` | `repro/scripts/math_hard_test_parallel_python_tool.py` |
| A8    | Answer Extractor                    | `extract_prompt`           | `upstream/progco/MATH/extract_answer.py`               |
| A21   | Context Compression Agent           | `context_compress.md` + `context_compress_user.md` | `mod_C0_compress/prompts/` |

## Notes

- A11 generates a forward verification flow from the problem, current solution response, and extracted answer.
- A12 executes the forward verification flow and returns the True/False verdict.
- A13 summarizes forward verification failures into feedback. Its explicit inputs are `q, y, a, V_f, r_f, R_f`.
- A14 refines the current forward verification flow `V_f` when the same-answer branch is triggered. In this branch, A14 uses the latest revised response `y'`, the revised answer `a'`, the previous forward verification flow `V_f`, and the failed execution record `R_f` to produce `V_f'`.
- A15 revises the response using forward verification feedback.
- A16 compares only the old answer `a` and the revised answer `a'`.
  If `a' != a`, the system updates `y,a` and regenerates a new forward verification flow through A11.
  If `a' == a`, the system updates `y` to the revised response `y'` and lets A14 refine the current `V_f` into `V_f'`.
- A17 implements `<tool_flow>` by compiling it into executable Python for the external Python interpreter.
- A21 compresses only the growing working context at `A12`, `A12.execute_content`, `A13.execute_content`, `A14`, `A14.verify_process`, and `A15`.
- A12 preserves the fixed system prompt, few-shot examples, problem, current solution, current answer, and current verification flow, and compresses only accumulated model-PythonTool history.
- A13 compresses only the failed execution record. A14 compresses only the previous verification process. A14 and A15 compress only accumulated tool-dialogue history.
- Fixed prompts, few-shot examples, the problem, the current solution, verification flows, and executable Python code are not compressed.
- Complete raw trajectories remain unchanged on disk; later model calls use only the latest compressed working context.
- The number A21 is documentation-only and does not appear in the compression agent's runtime prompt.
