# Canvas Quiz Options

Canvas-specific quiz options define how a quiz behaves when it is uploaded to **Canvas LMS**. 
The available options allow instructors to configure quiz behaviour,including grading policies,scoring methods and attempt limits.

> **Note**
> Canvas options allow instructors to customize quiz behaviour without modifying the quiz content itself.

---

## Quiz Options (Default Settings)

If an option is not specified, **default values** will be applied automatically.

| Option                  | Default Value  | Description                                                         |
| ----------------------- | -------------- |---------------------------------------------------------------------|
| `practice`              | `True`         | Creates the quiz as a practice quiz that does not affect the grade. |
| `published`             | `False`        | Determines whether the quiz is visible immediately after creation.  |
| `hide_results`          | `None`         | Controls when quiz results are visible to students.                 |
| `show_correct_answers`  | `True`         | Allows students to view correct answers after submission.           |
| `allowed_attempts`      | `1`            | Specifies the number of attempts a student can make.                |
| `scoring_policy`        | `keep_highest` | Determines how scores from multiple attempts are calculated.        |
| `assignment_group_name` | `Quizzes`      | The Canvas assignment group where the quiz will be placed.          |

---

## Allowed Values

Some options accept only specific values.

| Option                 | Allowed Values                               |
| ---------------------- | -------------------------------------------- |
| `practice`             | `True`, `False`                              |
| `published`            | `True`, `False`                              |
| `hide_results`         | `None`, `always`, `until_after_last_attempt` |
| `show_correct_answers` | `True`, `False`                              |
| `scoring_policy`       | `keep_highest`, `keep_latest`                |

---

## Question Feedback Mapping

Canvas supports different types of feedback that can be shown to students based on their answers.  
The Quiz Composer maps its feedback fields with appropriate Canvas API fields as shown below.

| Quiz Composer Field | Canvas API Field             | Description |
| ------------------- | ---------------------------- | ----------- |
| `general`           | `neutral_comments_html`      | Feedback shown regardless of correctness. |
| `correct`           | `correct_comments_html`      | Feedback shown when the student selects the correct answer. |
| `incorrect`         | `incorrect_comments_html`    | Feedback shown when the student selects an incorrect answer. |

---

## Validation Rules

The system validates Canvas quiz options before creating the quiz.

Key validation rules include:

- `allowed_attempts` must be a positive integer.  
- A value of `-1` indicates unlimited attempts.
- Options must match the predefined allowed values.
- If invalid values are provided, quiz creation will fail and an error message will be returned.

---

## Example Canvas Option Snippet

```json
"canvas": {
  "practice": true,
  "published": false,
  "hide_results": null,
  "show_correct_answers": true,
  "allowed_attempts": 1,
  "scoring_policy": "keep_highest",
  "assignment_group_name": "Quizzes"
}