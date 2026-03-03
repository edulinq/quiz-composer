# Canvas Quiz Options

This document describes the Canvas-specific configuration options available when uploading quizzes.
Defaults and behavior described here correspond to the current Canvas uploader implementation.

## Configuration Specification

Canvas options are provided as a JSON object within the quiz configuration:

```json
{
    "title": "My Quiz",
    "description": "...",
    "canvas": {
        "practice": true,
        "published": false,
        "show_correct_answers": true,
        "allowed_attempts": 1,
        "scoring_policy": "keep_highest",
        "assignment_group_name": "Quizzes"
    },
    "groups": [...]
}
```

## Option Reference

| Option | Type | Default | Description |
|--------|------|---------|-------|
| `practice` | Boolean | `true` | `true` creates a practice quiz; `false` creates an assignment |
| `published` | Boolean | `false` | Controls whether the quiz is published upon upload |
| `show_correct_answers` | Boolean | `true` | Controls whether Canvas displays correct answers to students |
| `hide_results` | String or null | `null` | `null`, `"always"`, or `"until_after_last_attempt"` |
| `allowed_attempts` | Integer | `1` | Positive integer or `-1` for unlimited attempts |
| `scoring_policy` | String | `"keep_highest"` | `"keep_highest"` or `"keep_latest"`; applies when `allowed_attempts` > 1 |
| `assignment_group_name` | String | `"Quizzes"` | Assignment group in Canvas; queried by name |

## Option Behavior

### practice

Controls the quiz type in Canvas.
When `true`, creates a practice quiz.
When `false`, creates an assignment.

### published

Controls the initial publication state of the quiz.
When `false`, the quiz is uploaded but remains unpublished.
When `true`, the quiz is published immediately.

### show_correct_answers

Controls whether students see correct answers after quiz completion.
When `true`, Canvas displays which answers are correct.
When `false`, correct answers are not shown.

### hide_results

Controls when students can view quiz results.

- `null` — Students can view results at any time.
- `"always"` — Results are hidden from students.
- `"until_after_last_attempt"` — Results are hidden until the student exhausts all allowed attempts.

### allowed_attempts

Controls the number of times a student may attempt the quiz.

- Positive integer — Student may attempt up to that many times.
- `-1` — Unlimited attempts.

### scoring_policy

When `allowed_attempts` is greater than 1, determines which attempt's score Canvas records.

- `"keep_highest"` — Records the highest score across all attempts.
- `"keep_latest"` — Records the most recent attempt's score.

Has no effect when `allowed_attempts` is `1`.

### assignment_group_name

Specifies the assignment group in which the quiz will be placed.
The uploader queries Canvas for a group matching this name.
If no matching group is found, the uploader passes a null value to Canvas.

## Examples

### Practice Quiz with Unlimited Attempts

```json
{
    "title": "Practice Problem Set",
    "canvas": {
        "practice": true,
        "allowed_attempts": -1,
        "show_correct_answers": true
    }
}
```

### Published Graded Quiz with Single Attempt

```json
{
    "title": "Midterm Exam",
    "canvas": {
        "practice": false,
        "published": true,
        "allowed_attempts": 1,
        "show_correct_answers": false,
        "hide_results": "always",
        "assignment_group_name": "Exams"
    }
}
```

### Quiz Allowing Multiple Attempts

```json
{
    "title": "Chapter 2 Quiz",
    "canvas": {
        "practice": false,
        "published": true,
        "allowed_attempts": 3,
        "scoring_policy": "keep_highest",
        "show_correct_answers": true
    }
}
```