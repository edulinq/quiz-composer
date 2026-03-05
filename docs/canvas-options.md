# Canvas Quiz Options

Quiz behavior in Canvas is controlled through the `canvas` key.

Table of Contents:
 - [practice](#practice)
 - [published](#published)
 - [show_correct_answers](#show_correct_answers)
 - [hide_results](#hide_results)
 - [allowed_attempts](#allowed_attempts)
 - [scoring_policy](#scoring_policy)
 - [assignment_group_name](#assignment_group_name)
 - [Example](#example)

| Key | Default Value | Type | Description |
|-----|---------------|------|-------------|
| `practice` | `true` | Boolean | Ungraded (practice) or graded (assignment) |
| `published` | `false` | Boolean | Whether quiz is visible after upload |
| `show_correct_answers` | `true` | Boolean | Whether correct answers are shown |
| `hide_results` | `null` | String or null | When students can view results |
| `allowed_attempts` | `1` | Integer | Number of quiz attempts allowed |
| `scoring_policy` | `"keep_highest"` | String | Which attempt score is recorded |
| `assignment_group_name` | `"Quizzes"` | String | Assignment group for quiz placement |


## practice

When `true`, the quiz is ungraded for student practice (doesn't affect the gradebook).
When `false`, the quiz is graded (scores count toward the student's grade and appears as an assignment in Canvas).

## published

When `false`, the quiz is hidden from students after upload (publish it manually when ready).
When `true`, the quiz is immediately visible and available to students.

## show_correct_answers

When `true`, Canvas displays correct answers after students complete the quiz.
When `false`, correct answers are not revealed.

## hide_results

Controls when students can view their quiz results and score.

 - `null` (default) - Results visible immediately after completion
 - `"always"` - Results hidden from students permanently
 - `"until_after_last_attempt"` - Results hidden until all attempts are exhausted

## allowed_attempts

Controls how many times students can attempt the quiz.

 - Positive integer (default `1`) - That many attempts allowed
 - `-1` - Unlimited attempts
 - `0` or negative values other than `-1` - Invalid

## scoring_policy

When `allowed_attempts` is greater than 1, determines which attempt's score is recorded in the gradebook.

 - `"keep_highest"` - Records the best score across all attempts
 - `"keep_latest"` - Records the most recent attempt's score

This setting has no effect when `allowed_attempts` is `1`.

## assignment_group_name

Specifies the Canvas assignment group where the quiz will be placed.
Canvas searches for a group with this name. If not found, the quiz uses Canvas's default location.

## Example

```json
{
    "title": "Midterm Exam",
    "canvas": {
        "practice": false,
        "published": true,
        "allowed_attempts": 2,
        "scoring_policy": "keep_highest",
        "show_correct_answers": true,
        "hide_results": "until_after_last_attempt",
        "assignment_group_name": "Exams"
    },
    "groups": [...]
}
```

A graded quiz with two attempts (best score recorded), answers revealed after all attempts used, placed in the "Exams" assignment group.