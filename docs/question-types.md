# Quiz Composer Question Types

The Quiz Composer (QuizComp) supports several different types of questions

Table of Contents:
 - [Data Types](#data-types)
 - [Common Fields](#common-fields)
   - [Question Feedback](#question-feedback)
 - [Question Types](#question-types)
   - [Multiple Choice (MC)](#multiple-choice-mc)
   - [True-False (TF)](#true-false-tf)
   - [Multiple Drop-Downs (MDD)](#multiple-drop-downs-mdd)
   - [Multiple Answers (MA)](#multiple-answers-ma)
   - [Matching](#matching)
   - [Fill in the Blank (FITB)](#fill-in-the-blank-fitb)
   - [Fill in Multiple Blanks (FIMB)](#fill-in-multiple-blanks-fimb)
   - [Numeric](#numeric)
   - [Short Answer (SA)](#short-answer-sa)
   - [Essay](#essay)
   - [Text-Only](#text-only)
 - [Differences with Canvas](#differences-with-canvas)

## Data Types

Since the QuizComp config is based around [JSON](https://en.wikipedia.org/wiki/JSON),
most data types used by the QuizComp are [simple JSON types](https://en.wikipedia.org/wiki/JSON#Data_types)
(ints, floats, strings, booleans, arrays/lists, objects (dicts/maps), and nulls).

The only difference between vanilla JSON types and QuizComp types is around the handling of strings.
The QuizComp divides strings into two types: plain strings and parsed strings.

Plain strings are limited to alphanumeric characters, spaces, underscores, and dashes.
These strings will often be used as keys (e.g., in Canvas options)
or as identifiers in some output language (e.g., as an HTML class).
Therefore, the content in plain strings are very limited.

Parsed strings are text that will be parsed by the QuizComp parser
(see [the syntax documentation](/docs/syntax.md)),
and therefore must be valid syntax.
When using some output formats (like Canvas),
it may seem odd why some fields need to be parsed (like a question's title).
However, remember that some output formats (like TeX) will need to parse a question's title to produce valid TeX.

## Common Fields

Here are common fields that all question types share.
Some fields will be inherited from the group the question is located in,
if not set explicitly.

| Key               | Type          | Inherited? | Usage |
|-------------------|---------------|------------|-------|
| `question_type`   | Plain String  | false      | The type of the question. See the details for each question type below for the correct value of this field. |
| `prompt`          | Parsed String | false      | The prompt displayed for a question. All questions require a prompt. See [this additional description](/README.md#question-prompts). |
| `posints`         | Number        | true       | The max points available for the question. Defaults to 0. |
| `answers`         | -             | false      | The definition of the answer or possible answers for a question. Because of the diverse nature of questions, the answers value will look different for different question types. |
| `custom_header`   | Plain String  | true       | An alternate header for a question. An empty string for no header. |
| `skip_numbering`  | Boolean       | true       | Whether this question should skip incrementing the question number. |
| `shuffle_answers` | Boolean       | true       | Whether to shuffle the order of the choices for this question. The final value is the conjunction of values from the quiz, group, and question. |
| `hints`           | Object        | true       | Formatting hints passed the converter about this question. We will note any question type that specifically looks for hints. |
| `feedback`        | Object        | false      | Feedback to be given to the student upon completion of the question/quiz. Feedback can be on the question and answer level. Support for feedback can greatly vary between output modes. |

### Hints

Hints serve as additional information (usually about quiz layout or rendering) passed to different formats.
Each format is not guaranteed to honor hints,
but each [builtin templates](/docs/builtin-templates.md) will declare the subset of hints that they support.

Hint provided via the `hints` field in a group will also be inherited by each question in that group.
To ensure that only the first or last question in a group inherit specific hints, use the `hints_first` and `hints_last` fields, respectively.
This can be useful when using the `pagebreak_before` or `pagebreak_after` hints to add a page break before or after a group,
but not before or after each question in that group.

### Question Feedback

Many quiz platforms (like Canvas) allows feedback to be attached to questions and/or individual answers in a question.
There are five types of feedback that can be used:
 - Question-Level, General Feedback -- Attached to the question object. This feedback should be provided to the student after completion of the question, regardless of the outcome.
 - Question-Level, Correct Feedback -- Attached to the question object. This feedback should be provided to the student after **correctly** answering the question.
 - Question-Level, Incorrect Feedback -- Attached to the question object. This feedback should be provided to the student after **incorrectly** answering the question.
 - Answer-Level, General Feedback -- Attached to an answer object. This feedback should be provided to the student after choosing this answer.

Not all platforms support all types of feedback (or implement feedback as you may expect).
For example on matching questions, Canvas only uses feedback attached to left-hand values.
It is suggested that you explore how feedback is used in your desired platform before administering a quiz.

The text for all feedback should be a parsed string.

Question-level feedback should be either an object specifying each desired type of feedback ('general', 'correct', 'incorrect'),
or a string that will be interpreted as general feedback.

Answer-level feedback should always be a string.

The following example shows how all types of feedback can be attached to a multiple choice question:
```json
    "question_type": "multiple_choice",
    "prompt": "Pick the correct answer.",
    "feedback": {
        "general": "The student will always see this feedback.",
        "correct": "The student will see this feedback if they answer correctly.",
        "incorrect": "The student will see this feedback if they answer incorrectly."
    }
    "answers": [
        {
            "correct": true,
            "text": "Alice",
            "feedback": "You got the correct answer\\!"
        },
        {
            "correct": false,
            "text": "Bob",
            "feedback": "Sorry, it was not Bob."
        },
        {
            "correct": true,
            "text": "Claire",
            "feedback": "Sorry, Claire is not the correct answer."
        },
        {
            "correct": false,
            "text": "Doug"
        }
    ]
```

## Question Types

Below are details on all the QuizComp's supported question types.

The form of the `answers` value will change depending on the question type.
Question types will often have a "short" answer form for simple/common cases,
and a "long" form where any available options can be specified.
Internally, "short" forms will always be expanded to "extended" forms.
This document will tend to start with the short form,
and then show the extended form for more complex cases.
Because of the flexibility of JSON and the QuizComp configuration,
only a subset of the possible ways a configuration can be written will be shown.
However, this document will attempt to show a sufficient amount of example configurations.

### Multiple Choice (MC)

Question Type: `multiple_choice`

Multiple choice questions provide several different options (called distractors)
with a **single** correct option.
The QuizComp requires that there is exactly one correct choice,
but does not set any limit on the number of distractors (incorrect options).
Specific output formats may limit the maximum number of distractors.

Answers are formatted as an array of objects with the `correct` and `text` fields.
The value of the `correct` field must be a boolean indicating if this option is the correct answer.
The value of the `text` field is a parsed string.

Example Answers Definition:
```json
    "answers": [
        {"correct": true,  "text": "A"},
        {"correct": false, "text": "B"},
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

Feedback can be directly attached to each list item:
```json
    "answers": [
        {
            "correct": true,
            "text": "A",
            "feedback": "You got it\\!"
        },
        {
            "correct": false,
            "text": "B",
            "feedback": "Sorry, try again."
        },
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

### True-False (TF)

Question Type: `true_false`

True-False questions are like multiple choice questions that are limited to only two choices: "True" and "False".
The answers definition is just a single boolean indicating the correct answer.

Example Answers Definition:
```json
    "answers": true
```

The attach feedback, the long-form of the answers value needs to be used:
```json
    "answers": [
        {
            "correct": true,
            "text": "True",
            "feedback": "Right answer."
        },
        {
            "correct": false,
            "text": "False",
            "feedback": "Wrong answer."
        }
    ]
```

### Multiple Drop-Downs (MDD)

Question Type: `multiple_dropdowns`

Multiple Drop-Down questions are questions that contain one or more parts,
where each part is a multiple choice question.
In a digital medium, each part could be represented with a drop-down selection list.
The question prompt should contain a [placeholder](/docs/syntax.md#placeholders) for the location of each question part.
The answers definition then maps each placeholder to a multiple choice-style answers definition.

For example, a question may have the following prompt and answers definition:
```json
    "prompt": "<placeholder>part1</placeholder> and <placeholder>part2</placeholder> wait for no one.",
    "answers": {
        "part1": [
            {"correct": true,  "text": "Time"},
            {"correct": false, "text": "Busses"},
            {"correct": false, "text": "Cats"}
        ],
        "part2": [
            {"correct": true,  "text": "tides"},
            {"correct": false, "text": "death"},
            {"correct": false, "text": "dogs"}
        ]
    }
```

Feedback can be used in the same way as MC questions:
```json
    "prompt": "<placeholder>part1</placeholder> and <placeholder>part2</placeholder> wait for no one.",
    "answers": {
        "part1": [
            {
                "correct": true,
                "text": "Time",
                "feedback": "Correct\\!"
            },
            {"correct": false, "text": "Busses"},
            {"correct": false, "text": "Cats"}
        ],
        "part2": [
            {"correct": true,  "text": "tides"},
            {"correct": false, "text": "death"},
            {"correct": false, "text": "dogs"}
        ]
    }
```

### Multiple Answers (MA)

Question Type: `multiple_answers`

Multiple answer questions are questions where multiple (or no) choices can be selected.
They are specified the same as multiple choice questions,
except any number of the choices may be marked as correct.

Output mediums will typically style these choices differently that multiple choice questions.
A common convention is to use round radio buttons when a single choice is available,
and square checkboxes when multiple choices are available.

Example Answers Definition:
```json
    "answers": [
        {"correct": true,  "text": "A"},
        {"correct": true,  "text": "B"},
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

Feedback can be used in the same way as MC questions:
```json
    "answers": [
        {"correct": true,  "text": "A", "feedback": "Correct\\!"},
        {"correct": true,  "text": "B": "feedback": "Also correct."},
        {"correct": false, "text": "C"},
        {"correct": false, "text": "D"}
    ]
```

### Matching

Question Type: `matching`

Matching questions provide two lists: left and right.
Users are tasked with matching an item from the left list to an item from the right list.
The right list will be at least as large as the left list,
and may contain additional distractors (incorrect values that do not match anything in the left list).

The answers definition must contain a list of pairs of left and right items,
and an optional list of additional distractors.
All values are parsed strings.

Example Answers Definition:
```json
    "prompt": "Match the English word to it's Spanish equivalent.",
    "answers": {
        "matches": [
            ["one", "uno"],
            ["two", "dos"],
            ["three", "tres"]
        ],
        "distractors": [
            "cuatro",
            "cinco",
            "seis"
        ]
    }
```

The attach feedback, the long-form of the answers value needs to be used:
```json
    "prompt": "Match the English word to it's Spanish equivalent.",
    "answers": {
        "matches": [
            [
                "one",
                "uno"
            ],
            {
                "left": "two",
                "right": "dos"
            },
            {
                "left": {
                    "text": "three",
                    "feedback": "In French: 'trois'",
                }
                "right": "tres"
            }
        ],
        "distractors": [
            "cuatro",
            {
                "text": "cinco"
            },
            {
                "text": "seis",
                "feedback": "In French: 'six'"
            }
        ]
    }
```

### Fill in the Blank (FITB)

Question Type: `fill_in_the_blank`

Fill in the blank questions provide a single blank at the end of the question that the users is tasked with filling out.
These questions expect a finite textual answer.
Designing these questions can be tricky, since an exact answer is expected.
Stray spacing, capitalization, alternate spelling, phrasing, or bad handwriting can lead to incorrect automatic grading of these questions.
The semantics of how exactly answers are checked and case sensitivity is up to the output quiz medium (e.g. Canvas, GradeScope, etc).
It is recommended that you avoid FITB questions when possible.

Answers are defined as a list of possible correct answers.

Example Answers Definition:
```json
    "prompt": "How many cardinal directions are there?",
    "answers": ["4", "four", "Four", "FOUR"]
```

Feedback can be attached to each possible choice:
```json
    "prompt": "How many cardinal directions are there?",
    "answers": [
        {
            "text": "4",
            "feedback": "This is the preferred answer."
        },
        {
            "text": "four",
        }
        "Four",
        "FOUR"
    ]
```

### Fill in Multiple Blanks (FIMB)

Question Type: `fill_in_multiple_blanks`

Fill in multiple blank questions are an extension of FITB questions that allows for multiple blanks to occur anywhere in the prompt.
Like MDD questions, the question prompt should include a placeholder for each blank.
FIMB questions come with the same warnings as FITB questions (multiplied by the number of blanks).

Answers map each blank to a list of possible options.

Example Answers Definition:
```json
    "prompt": "Nothing can be said to be certain, except <placeholder>first</placeholder> and <placeholder>second</placeholder>.",
    "answers": {
        "first": ["death", "Death", "DEATH"],
        "second": ["taxes", "taxs", "Taxes", "Taxs," "TAXES", "TAXS"],
    }
```

Like FITB, feedback can be attached to each possible choice:
```json
    "prompt": "Nothing can be said to be certain, except <placeholder>first</placeholder> and <placeholder>second</placeholder>.",
    "answers": {
        "first": [
            "death",
            "Death",
            {
                "text": "DEATH",
                "feedback": "So dramatic."
            }
        ],
        "second": [
            {
                "text": "taxes"
            },
            {
                "text": "taxs",
                "feedback": "Not the preferred spelling."
            },
            "Taxes", "Taxs," "TAXES", "TAXS"],
    }
```

### Numeric

Question Type: `numerical`

Numeric questions are similar to FITB question,
but expect a single numerical answer.
Because a numerical answer is expected,
numeric questions are typically much less ambiguous than FITB questions.

The answers definition for numeric questions is a list of possible numeric ranges.
Matching any of these ranges indicates a correct answer.

Example Answers Definition:
```json
    "answers": [
        {"type": "exact", "value": 1.0, "margin": 0.01},
        {"type": "range", "min": 0.99, "max": 1.01},
        {"type": "precision", "value": 1.0, "precision": 2}
    ]
```

Feedback can be directly attached to each list item:
```json
    "answers": [
        {"type": "exact", "value": 1.0, "margin": 0.01, "feedback": "Good job\\!"},
        {"type": "range", "min": 0.99, "max": 1.01},
        {"type": "precision", "value": 1.0, "precision": 2}
    ]
```

### Short Answer (SA)

Question Type: `short_answer`

Short answer questions provide a text area for users to enter answers.
Answers are expected to be anywhere between a few words to a few sentences.

For most output formats, the answers definition will probably serve as rubric for manual graders.
The answers value can be any of the following:
 - `null`
 - empty string
 - string
 - empty list
 - list of strings

Any strings should be typed as parsed strings.

Example Answers Definition:
```json
    "answers": "The correct answer should make a coherent argument."
```

The attach feedback, the long-form of the answers value needs to be used:
```json
    "answers": [
        {
            "text": "The correct answer should make a coherent argument.",
            "feedback": "Your answer will be manually graded."
        }
    ]
```

### Essay

Question Type: `essay`

Essay questions are like short answer questions,
but allocate a much larger area for answers.
In a paper-based medium, an entire page should be reserved for an answer area.
See the documentation for [Short Answer (SA) questions](#short-answer-sa) for a description of the answers key.

### Text-Only

Question Type: `text_only`

Text-only questions provide a means of communicating information to the user in a structured manner.
The most common use for text-only questions is to provide a common description or information that can be used
in multiple subsequent questions, e.g., a table that can be referenced across multiple questions.

## Differences with Canvas

The QuizComp supports almost all the questions used in "classic" style Canvas quizzes.

The only text-input Canvas question type the Quiz Composer does not support are "Calculated" / "Formula" questions.
We feel that this question type is overly complex and error-prone.
Instead, we suggest that users use the "numeric" question type.

Canvas users should also note that the "Fill in the Blank" (FITB) question type,
also referred to as "Short Answer" (SA) in Canvas documentation, has been split from one Canvas question type
into two QuizComp question types: "Fill in the Blank" (FITB) and "Short Answer" (SA).
When creating Canvas quizzes, both these types map back to the FITB type.
For other quiz mediums, FITB questions generally expect the answer to be no more than a few words and reserve only a little space for the answer,
while SA questions generally reserve about a paragraph's worth of space for an answer.
