# Canvas-Specific Quiz Options

Quiz Composer supports several options that control how quizzes are uploaded
and behave in Canvas. These options are provided under the `canvas` field
in a quiz JSON file.

All options documented here are derived directly from the Canvas uploader
implementation.

---

## Canvas Options

### practice
- **Type:** boolean
- **Default:** `true`
- **Allowed values:** `true`, `false`
- **Behavior:**
  - When `true`, the quiz is uploaded as a Canvas *practice quiz*
    (`quiz_type = practice_quiz`).
  - When `false`, the quiz is uploaded as a standard graded assignment
    (`quiz_type = assignment`).

---

### published
- **Type:** boolean
- **Default:** `false`
- **Allowed values:** `true`, `false`
- **Behavior:**
  - Controls whether the quiz is immediately published and visible to students
    after upload.

---

### allowed_attempts
- **Type:** integer
- **Default:** `1`
- **Allowed values:**
  - Any positive integer
  - `-1` (unlimited attempts)
- **Validation rules:**
  - Values must be coercible to an integer
  - `0` and values less than `-1` are rejected
- **Behavior:**
  - Passed directly to Canvas as the allowed attempt count for the quiz.

---

### show_correct_answers
- **Type:** boolean
- **Default:** `true`
- **Allowed values:** `true`, `false`
- **Behavior:**
  - Controls whether Canvas displays correct answers to students after
    quiz submission.

---

### hide_results
- **Type:** string or null
- **Default:** `null`
- **Allowed values:**
  - `null`
  - `"always"`
  - `"until_after_last_attempt"`
- **Behavior:**
  - Controls when quiz results are hidden from students according to
    Canvas result visibility rules.

---

### scoring_policy
- **Type:** string
- **Default:** `"keep_highest"`
- **Allowed values:**
  - `"keep_highest"`
  - `"keep_latest"`
- **Behavior:**
  - Determines how Canvas scores multiple quiz attempts.

---

### assignment_group_name
- **Type:** string
- **Default:** `"Quizzes"`
- **Behavior:**
  - Specifies the Canvas assignment group under which the quiz is created.
  - If the assignment group does not exist, the quiz is created without
    an assignment group association.
