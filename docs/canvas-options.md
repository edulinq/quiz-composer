# Canvas Quiz Options

Canvas is a learning management system (LMS) with its own quiz model.
The Quiz Composer uploads quizzes to Canvas, but you can customize how the quiz behaves in Canvas using the `canvas` configuration object.

Table of Contents:
 - [Configuration Basics](#configuration-basics)
 - [Quiz Type and Publishing](#quiz-type-and-publishing)
 - [Student Interactions](#student-interactions)
 - [Multiple Attempts](#multiple-attempts)
 - [Organization](#organization)

## Configuration Basics

Canvas options are specified in your quiz configuration using the `canvas` object.
Only the options you want to customize need to be included; the rest will use sensible defaults.

Here is an overview of all available options:

| Option | Type | Default |
|--------|------|---------|
| `practice` | Boolean | `true` |
| `published` | Boolean | `false` |
| `show_correct_answers` | Boolean | `true` |
| `hide_results` | String or null | `null` |
| `allowed_attempts` | Integer | `1` |
| `scoring_policy` | String | `"keep_highest"` |
| `assignment_group_name` | String | `"Quizzes"` |

## Quiz Type and Publishing

### Quiz Type (Practice vs Assignment)

The `practice` option controls whether your quiz appears as a practice quiz or a graded assignment in Canvas.

 - `practice: true` - Creates a practice quiz. Students can use this to study without affecting their grade. Practice quizzes do not contribute to the gradebook.
 - `practice: false` - Creates a graded assignment. Student scores will be recorded in the Canvas gradebook.

Choose `practice: true` for study materials, review sessions, or self-assessments where grades don't matter.
Choose `practice: false` when you want to grade students on their performance.

### Publishing

The `published` option determines whether the quiz is available to students immediately after you upload it.

 - `published: false` - The quiz is uploaded but remains hidden from students. You can review it and publish it manually later through Canvas.
 - `published: true` - The quiz is immediately visible to students and ready to take.

Most of the time, you'll want `published: false` so you can verify the quiz looks correct before students see it.

## Student Interactions

### Viewing Correct Answers

The `show_correct_answers` option controls whether students can see which answers are correct after they complete the quiz.

 - `show_correct_answers: true` - After completing the quiz, Canvas will highlight correct answers for the student.
 - `show_correct_answers: false` - Students cannot see which answers were correct.

Use `show_correct_answers: false` for high-stakes exams where you want to maintain answer security.
Use `show_correct_answers: true` for practice quizzes or assessments where students should learn from their mistakes.

### Hiding Results

The `hide_results` option allows you to prevent students from viewing their quiz results until a certain point.

This option accepts three values:

 - `null` - Students can view their results at any time after completing the quiz.
 - `"always"` - Results are completely hidden. Students will never see their score or feedback.
 - `"until_after_last_attempt"` - Results remain hidden until the student has exhausted all their allowed attempts.

The last option is useful when you allow multiple attempts and want to prevent students from learning their initial score before their final attempt.

## Multiple Attempts

### Number of Attempts

The `allowed_attempts` option controls how many times students can take the quiz.

 - Any positive integer - Students can attempt the quiz up to that many times.
 - `-1` - Students have unlimited attempts.
 - `1` (default) - Students get one chance only.

For practice quizzes, unlimited attempts (`-1`) works well.
For graded assessments, you might allow 2-3 attempts, or restrict to a single attempt for exams.

### Scoring Policy for Multiple Attempts

When students can take the quiz more than once, the `scoring_policy` option determines which attempt's score goes in the gradebook.

 - `"keep_highest"` - Canvas records the highest score across all attempts. This rewards students who improve over time.
 - `"keep_latest"` - Canvas records the most recent attempt's score. This is useful when the quiz itself changes between attempts.

The `scoring_policy` only matters when `allowed_attempts` is greater than 1.
If students only get one attempt, this setting has no effect.

## Organization

### Assignment Group

The `assignment_group_name` option allows you to place the quiz into a specific assignment group in Canvas.
Assignment groups are used to organize grades by category (for example, "Quizzes", "Exams", "Homework").

Canvas looks for an assignment group matching the name you specify.
If one exists, your quiz will be placed there.
If no matching group is found, the quiz will be placed in Canvas's default location.

## Examples

### Practice Quiz for Self-Assessment

This is perfect for study materials that students can use to practice without grades.

```json
{
    "title": "Chapter 2 Study Guide",
    "canvas": {
        "practice": true,
        "allowed_attempts": -1,
        "show_correct_answers": true
    }
}
```

In this setup, students can attempt the quiz unlimited times and immediately see the correct answers to learn from their mistakes.

### Graded Exam with Answer Security

This configuration is appropriate for high-stakes exams where you want to maintain answer security.

```json
{
    "title": "Midterm Exam",
    "canvas": {
        "practice": false,
        "published": false,
        "allowed_attempts": 1,
        "show_correct_answers": false,
        "hide_results": "always"
    }
}
```

The quiz is not automatically published, so you can review it before students see it.
Students get one attempt, cannot see correct answers, and cannot view their results (you can share results manually).

### Multiple-Attempt Quiz with Best Score

This works well for lower-stakes quizzes where you want to encourage students to study and try again.

```json
{
    "title": "Weekly Concept Check",
    "canvas": {
        "practice": false,
        "published": true,
        "allowed_attempts": 3,
        "scoring_policy": "keep_highest",
        "show_correct_answers": true,
        "assignment_group_name": "Quizzes"
    }
}
```

Students get three attempts, and their best score is recorded.
They can see correct answers to help them study between attempts.
The quiz is published immediately and placed in your "Quizzes" assignment group.
