# Canvas Quiz Options

Quiz behavior in Canvas can be configured through the `canvas` key in the quiz JSON file.

Table of Contents:
 - [Options](#options)
   - [Quiz Type](#quiz-type)
   - [Published State](#published-state)
   - [Result Visibility](#result-visibility)
   - [Correct Answer Display](#correct-answer-display)
   - [Attempt Limit](#attempt-limit)
   - [Scoring Policy](#scoring-policy)
   - [Assignment Group](#assignment-group)
 - [Example](#example)

## Options

| Key                      | Type    | Default Value  | Allowed Values                                     | Notes                                           |
|--------------------------|---------|----------------|----------------------------------------------------|-------------------------------------------------|
| `practice`               | boolean | `true`         | {`true`, `false`}                                  | Whether the quiz is a practice (ungraded) quiz. |
| `published`              | boolean | `false`        | {`true`, `false`}                                  | Whether the quiz is visible to students.        |
| `hide_results`           | string  | `null`         | {`null`, `"always"`, `"until_after_last_attempt"`} | Controls result visibility after submission.    |
| `show_correct_answers`   | boolean | `true`         | {`true`, `false`}                                  | Whether correct answers are shown.              |
| `allowed_attempts`       | integer | `1`            | Positive integer or `-1`                           | How many times students can take the quiz.      |
| `scoring_policy`         | string  | `keep_highest` | {`"keep_highest"`, `"keep_latest"`}                | Which attempt score is recorded.                |
| `assignment_group_name`  | string  | `Quizzes`      | Any string                                         | Canvas assignment group for the quiz.           |

### Quiz Type

The `practice` key controls whether the quiz is a practice quiz.
When true, the quiz is ungraded and does not appear in the gradebook.
When false, the quiz is a graded assignment.

### Published State

The `published` key controls whether the quiz is visible to students after upload.
When false, the quiz is created as a draft that only staff can see.
When true, the quiz is immediately available to students.

### Result Visibility

The `hide_results` key controls when students can view their quiz results.
This key only accepts the following values:

 - `null` (default) -- Results are visible immediately after submission.
 - `"always"` -- Results are never shown to students.
 - `"until_after_last_attempt"` -- Results are hidden until the student has used all attempts.

### Correct Answer Display

The `show_correct_answers` key controls whether correct answers are revealed after submission.
When true, students can see which answers were correct.
When false, correct answers are not shown.

### Attempt Limit

The `allowed_attempts` key controls how many times a student can take the quiz.
The value must be a positive integer or `-1` for unlimited attempts.
Zero is not a valid value.

### Scoring Policy

The `scoring_policy` key determines which score is recorded when multiple attempts are allowed.

 - `"keep_highest"` -- The best score across all attempts is used.
 - `"keep_latest"` -- The most recent attempt score is used.

When only one attempt is allowed, this option has no practical effect.

### Assignment Group

The `assignment_group_name` key specifies which Canvas assignment group the quiz belongs to.
If the named group does not exist in the course, no assignment group ID is sent to Canvas.

## Example

A graded exam with three attempts where the best score is recorded.
Correct answers are shown only after the student has used all attempts.

```json
{
    "title": "Final Exam",
    "canvas": {
        "practice": false,
        "published": true,
        "hide_results": "until_after_last_attempt",
        "show_correct_answers": true,
        "allowed_attempts": 3,
        "scoring_policy": "keep_highest",
        "assignment_group_name": "Exams"
    },
    "groups": [...]
}
```
