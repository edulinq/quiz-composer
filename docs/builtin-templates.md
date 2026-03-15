# Quiz Composer Builtin Templates

The Quiz Composer comes with builtin templates for HTML and TeX.
For the most part, you can just use them without any additional knowledge.
However if you wish to tinker with them,
this document contains useful details.

Table of Contents:
 - [TeX](#tex)
   - [Hints](#hints)
    - [Multiple Choice (MC)](#multiple-choice-mc)
    - [True-False (TF)](#true-false-tf)
    - [Multiple Drop-Downs (MDD)](#multiple-drop-downs-mdd)
    - [Multiple Answers (MA)](#multiple-answers-ma)
    - [Fill in the Blank (FITB)](#fill-in-the-blank-fitb)
    - [Fill in Multiple Blanks (FIMB)](#fill-in-multiple-blanks-fimb)
    - [Numeric](#numeric)
    - [Short Answer (SA)](#short-answer-sa)
    - [Essay](#essay)

## TeX

### Hints

Hints are suggestions to the layout engine on how to display a quiz or question.
Hints can be very powerful, but can also be fragile.
When using hints, you override the default (and safe) behavior of a template.
You are encouraged to look at how a hint is used inside of a template before using it.

Hints generally control the layout and flow of content.
If you are looking to control the rendering or style of content,
then you want to [styling documentation](/docs/styling.md).

Here are hints general to all question types:

| Key                | Default Value | Type    | Description                             |
|--------------------|---------------|---------|-----------------------------------------|
| `pagebreak_before` | false         | boolean | Place a pagebreak before this question. |
| `pagebreak_after`  | false         | boolean | Place a pagebreak after this question.  |

#### Multiple Choice (MC)

| Key        | Default Value      | Type    | Description                              |
|------------|--------------------|---------|------------------------------------------|
| `inline`   | false              | boolean | Try to put the choices on the same line. |
| `nocenter` | false              | boolean | Disable centering of the choices.        |
| `width`    | 0.80 (0.15 inline) | float   | The width of the text areas (as a percentage of the text width). |

#### True-False (TF)

| Key        | Default Value      | Type    | Description                              |
|------------|--------------------|---------|------------------------------------------|
| `inline`   | false              | boolean | Try to put the choices on the same line. |
| `nocenter` | false              | boolean | Disable centering of the choices.        |
| `width`    | 0.80 (0.15 inline) | float   | The width of the text areas (as a percentage of the text width). |

#### Multiple Drop-Downs (MDD)

| Key        | Default Value      | Type    | Description                              |
|------------|--------------------|---------|------------------------------------------|
| `inline`   | false              | boolean | Try to put the choices on the same line. |
| `nocenter` | false              | boolean | Disable centering of the choices.        |
| `width`    | 0.80 (0.15 inline) | float   | The width of the text areas (as a percentage of the text width). |

#### Multiple Answers (MA)

| Key        | Default Value      | Type    | Description                              |
|------------|--------------------|---------|------------------------------------------|
| `inline`   | false              | boolean | Try to put the choices on the same line. |
| `nocenter` | false              | boolean | Disable centering of the choices.        |
| `width`    | 0.80 (0.15 inline) | float   | The width of the text areas (as a percentage of the text width). |

#### Fill in the Blank (FITB)

| Key        | Default Value | Type    | Description                        |
|------------|---------------|---------|------------------------------------|
| `height`   | 4em           | string  | The height of the text box.        |
| `nocenter` | false         | boolean | Disable centering of the text box. |
| `width`    | 1.0           | float   | The width of the text box (as a percentage of the text width). |

#### Fill in Multiple Blanks (FIMB)

| Key        | Default Value      | Type    | Description                                 |
|------------|--------------------|---------|---------------------------------------------|
| `inline`   | false              | boolean | Try to put the text boxes on the same line. |
| `height`   | 4em                | string  | The height of the text boxes.               |
| `nocenter` | false              | boolean | Disable centering of the text boxes.        |
| `width`    | 0.95 (0.13 inline) | float   | The width of the text boxes (as a percentage of the text width). |

#### Numeric

| Key        | Default Value | Type    | Description                        |
|------------|---------------|---------|------------------------------------|
| `height`   | 4em           | string  | The height of the text box.        |
| `nocenter` | false         | boolean | Disable centering of the text box. |
| `width`    | 1.0           | float   | The width of the text box (as a percentage of the text width). |

#### Short Answer (SA)

| Key        | Default Value | Type    | Description                        |
|------------|---------------|---------|------------------------------------|
| `height`   | 4em           | string  | The height of the text box.        |
| `nocenter` | false         | boolean | Disable centering of the text box. |
| `width`    | 1.0           | float   | The width of the text box (as a percentage of the text width). |

#### Essay

| Key        | Default Value | Type    | Description                        |
|------------|---------------|---------|------------------------------------|
| `nocenter` | false         | boolean | Disable centering of the text box. |
| `width`    | 1.0           | float   | The width of the text box (as a percentage of the text width). |
