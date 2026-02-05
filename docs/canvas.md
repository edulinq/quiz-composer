# Canvas-Specific Quiz Options

QuizComp supports several options that control how quizzes behave when uploaded to Canvas.
These options are defined under the `canvas` field in a quiz JSON file.

---

## Example

```json
{
  "canvas": {
    "practice": true,
    "published": false,
    "allowed_attempts": 1,
    "scoring_policy": "keep_highest",
    "show_correct_answers": true,
    "hide_results": null,
    "assignment_group_name": "Quizzes"
  }
}
