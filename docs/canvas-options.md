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

| Key                      | Default Value | Type    | Description                                       |
|--------------------------|---------------|---------|---------------------------------------------------|
| `practice`               | true          | boolean | Whether the quiz is a practice (ungraded) quiz.   |
| `published`              | false         | boolean | Whether the quiz is visible to students.          |
| `hide_results`           | null          | string  | When students can view their results.             |
| `show_correct_answers`   | true          | boolean | Whether correct answers are shown.                |
| `allowed_attempts`       | 1             | integer | How many times students can take the quiz.        |
| `scoring_policy`         | keep_highest  | string  | Which attempt score is recorded.                  |
| `assignment_group_name`  | Quizzes       | string  | Canvas assignment group for the quiz.             |

### Quiz Type

The `practice` key controls whether the quiz is a practice quiz.
When true, the quiz is ungraded and does not appear in the gradebook.
When false, the quiz is a graded assignment.

### Published State

The `published` key controls whether the quiz is visible to students after upload.
When false, the quiz is created as a draft that only instructors can see.
When true, the quiz is immediately available to students.

### Result Visibility

The `hide_results` key controls when students can view their quiz results.

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

A graded exam with three attempts where the best score is recorded.
Correct answers are shown only after the student has used all attempts.
