# Quiz Composer

A tool for generating quizzes from a standard, text-based definition.
Quizzes can be taken from the standard definition and converted into:
 - PDFs
 - Canvas Quizzes (Uploaded to Canvas)
 - GradeScope Quizzes
   - Both GradeScope-Compatible PDFs and Uploaded to GradeScope
 - HTML Forms
 - [QTI Zip Files](https://en.wikipedia.org/wiki/QTI)

Sample quizzes that demonstrate all question types are available
[in the CSE Cracks course](https://github.com/eriq-augustine/cse-cracks-course/tree/main/quizzes).
Additionally, you can see examples of good questions by looking at the [test cases for this project](tests/questions/good).

Documentation Table of Contents:
 - [Installation / Requirements](#installation--requirements)
   - [Python](#python)
   - [PDF Files](#pdf-files)
   - [Math Equations in HTML](#math-equations-in-html)
   - [Canvas Uploading](#canvas-uploading)
   - [GradeScope Uploading](#gradescope-uploading)
 - [Usage](#usage)
   - [Parsing a Specific Quiz](#parsing-a-specific-quiz)
     - [Outputting a JSON Quiz](#outputting-a-json-quiz)
     - [Outputting a TeX Quiz](#outputting-a-tex-quiz)
     - [Outputting an HTML Quiz](#outputting-an-html-quiz)
     - [Outputting a QTI Quiz](#outputting-a-qti-quiz)
   - [Parsing a Specific Question](#parsing-a-specific-question)
   - [Parsing a Specific File](#parsing-a-specific-file)
   - [Uploading a Quiz to Canvas](#uploading-a-quiz-to-canvas)
   - [Uploading a Quiz to GradeScope](#uploading-a-quiz-to-gradescope)
 - [Quiz Format](#quiz-format)
   - [Answer Shuffling](#answer-shuffling)
   - [Question Selection from Groups](#question-selection-from-groups)
   - [Question Prompts](#question-prompts)
   - [Quiz Descriptions](#quiz-descriptions)
 - [Question Types](/docs/question-types.md)
 - [QuizComp Markdown Syntax](/docs/syntax.md)
 - [Builtin Templates and Hints](/docs/builtin-templates.md)
 - [Styling](/docs/styling.md)

## Installation / Requirements

### Python

This project requires [Python](https://www.python.org/) >= 3.9.

The project can be installed from PyPi with:
```
pip3 install edq-quizcomp
```

Standard Python requirements are listed in `pyproject.toml`.
The project and Python dependencies can be installed from source with:
```
pip3 install .
```

### PDF Files

#### Local Compilation

To compile PDF files, the `pdflatex` program is used.
`pdflatex` comes installed with most standard [LaTeX](https://en.wikipedia.org/wiki/LaTeX) packages.

By default, your [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) will be searched for `pdflatex`.
To specify the path to your `pdflatex` binary, you can use the `--pdflatex-bin-path` flag.

#### Docker Compilation

The QuizComp can compile PDFs using [Docker](https://www.docker.com/) with the `--pdflatex-use-docker` flag.
The Docker image used for compilation is [ghcr.io/edulinq/pdflatex-docker](https://github.com/edulinq/pdflatex-docker/pkgs/container/pdflatex-docker) (see the [repository here](https://github.com/edulinq/pdflatex-docker) for more details).
This image includes `pdflatex` and most [standard LaTeX packages](https://packages.ubuntu.com/jammy/texlive-latex-extra) for generating PDFs.
Ensure Docker is running and accessible by the current user (typically via the Docker daemon).
The basic usage is as follows:
```
python3 -m quizcomp.cli.pdf.create <path to JSON file> --pdflatex-use-docker
```

### Math Equations in HTML

To output equations in HTML documents (which includes Canvas), [KaTeX](https://katex.org) is required.
KaTeX is distributed as a NodeJS package, and this project requires that KaTeX is accessible via `npx` (which typically requires it to be installed via `npm`).
Once NodeJS and NPM are installed, you can just install KaTeX normally:
```
npm install katex
```

By default, your [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) will be searched for `npm` and `npx`.
To specify the directory where they both live, you can use the `--nodejs-bin-dir` flag.

### Canvas Uploading

To upload quizzes to Canvas, you will need three things:
 - The Canvas Base URL
   - The base URL for the Canvas instance you are using.
   - Ex: `https://canvas.ucsc.edu`
 - The Canvas Course ID
   - The numeric ID for the course you want to upload the quiz under.
   - You can find this by going to the main page for your course (or almost any page related to your course), and looking at the url.
   - Ex: For `https://canvas.ucsc.edu/courses/12345`, the course ID is `12345`.
 - A Canvas Access Token
   - A token is specific for each user, and that user should the have ability to make quizzes for your specific course.
   - To get a new token, go to your account settings ("Account" -> "Settings"), and under "Approved Integrations" click "+ New Access Token".

### GradeScope Uploading

To upload quizzes to GradeScope, you will need three things:
 - A GradeScope Instructor Account
   - Technically, any account capable of creating assignments should be sufficient.
 - A GradeScope Account Password
   - If you normally log into GradeScope through an organization account (like via a university email), then you will just need to create a GradeScope password.
     This can be done via the [password reset page](https://www.gradescope.com/reset_password), which in this case will allow you to create a new password.
 - A GradeScope Course ID

## Usage

This project has executable modules in the `quizcomp.cli` package.
All executable modules have their own help/usage accessible with the `-h` / `--help` option.

### Parsing a Specific Quiz

To parse an entire specific quiz, you can use the `quizcomp.cli.parse-quiz` module.
This is useful if you want to check if a quiz properly parses.
The basic usage is as follows:
```
python3 -m quizcomp.cli.parse.quiz <path to quiz JSON file>
```

This command will output the fully parsed quiz in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
Parsing a quiz is particularly useful in CI to ensure that all course quizzes are properly maintained.

The `--key` flag can be used to generate an answer key instead of a normal quiz.
Not all formats support answer keys.

#### Outputting a JSON Quiz

To output a JSON quiz to a file called `quiz.json`, you can use the following command:
```
python3 -m quizcomp.cli.parse.quiz <path to quiz JSON file> --format json > quiz.json
```

A JSON representation of a parsed quiz (which is different from a standard quiz definition) can be useful for debugging.
If debugging, the `--flatten-groups` flag can be useful (which will include all questions from all groups in the output quiz).

#### Outputting a TeX Quiz

To output a TeX quiz to a file called `quiz.tex`, you can use the following command:
```
python3 -m quizcomp.cli.parse.quiz <path to quiz JSON file> --format tex > quiz.tex
```

You can then compile or edit the TeX file as you see fit.

#### Outputting an HTML Quiz

To output a HTML quiz to a file called `quiz.html`, you can use the following command:
```
python3 -m quizcomp.cli.parse.quiz <path to quiz JSON file> --format html > quiz.html
```

All question in an HTML quiz are grouped together into a single HTML form.

#### Outputting a QTI Quiz

You can use the same `quizcomp.cli.parse.quiz` command to view the core QTI file for a quiz:
```
python3 -m quizcomp.cli.parse.quiz <path to quiz JSON file> --format qti > quiz.qti.xml
```

However you will instead probably want a fill QTI zip archive,
which is the common form used to upload to other platforms (like Canvas).
To generate a full QTI zip archive, use the `quizcomp.cli.qti.create` command:
```
python3 -m quizcomp.cli.qti.create ~/code/cse-cracks-course/quizzes/regex/quiz.json --canvas
```

The `--canvas` flag enables Canvas-specific tweaks required when uploading a QTI file to Canvas.

### Parsing a Specific Question

To parse a specific quiz question, you can use the `quizcomp.cli.parse.question` module.
This is useful if you want to check if a question properly parses.
The basic usage is as follows:
```
python3 -m quizcomp.cli.parse.question <path to question JSON file>
```

This command will output the fully parsed question in the JSON format,
and will exit with a non-zero status if the parse failed.

You can use the same `--format` options used in `quizcomp.cli.parse.quiz` to change the output format of the question.
The question will be placed in a "dummy" quiz, so the output should be fully stand-alone.

### Parsing a Specific File

To parse a specific file, you can use the `quizcomp.cli.parse.file` module.
This is useful if you want to check if/how a specific document parses.
The basic usage is as follows:
```
python3 -m quizcomp.cli.parse.file <path to file> --format html
```

This command will output the fully parsed file in for format controlled by the `--format` option,
and will exit with a non-zero status if the parse failed.
This can be used to parse prompt markdown files.

### Uploading a Quiz to Canvas

To upload a quiz to Canvas, the `quizcomp.cli.canvas.upload` module can be used.
The basic usage is as follows:
```
python3 -m quizcomp.cli.canvas.upload <path to quiz JSON file> --course <canvas course id> --token <canvas access token>
```

If an existing quiz with the same name is found, then nothing will be uploaded unless the `--force` flag is given..

### Creating a PDF Quiz

To create a PDF version of a quiz, `quizcomp.cli.pdf.create` module can be used.
The basic usage is as follows:
```
python3 -m quizcomp.cli.pdf.create <path to quiz JSON file>
```

Some additional options that may be useful:
 - `--outdir <dir>` -- Choose where the output (TeX, PDF, etc) will be written to.
 - `--variants <X>` -- Create X variants (alternate versions) if the quiz. X may be in [1, 26].

### Uploading a Quiz to GradeScope

To upload a quiz to GradeScope, the `quizcomp.cli.gradescope.upload` module can be used.
The basic usage is as follows:
```
python3 -m quizcomp.cli.gradescope.upload <path to quiz JSON file> --course <course id> --user <username> --pass <password>
```

Since GradeScope uses passwords instead of tokens, take extra caution about your password appearing in config files or command histories.
All the same options for creating PDFs (`quizcomp.cli.pdf.create`) can be used.

## Quiz Format

Below are some common fields used in the **quiz** JSON configuration.

| Key                     | Type           | Required? | Default      | Description |
|-------------------------|----------------|-----------|--------------|-------------|
| `title`                 | Plain String   | true      |              | The title of the quiz. |
| `course_title`          | Plain String   | false     | empty string | The title of the course for this quiz. |
| `term_title`            | Plain String   | false     | empty string | The title of the term this quiz is given in. |
| `description`           | Parsed String  | true      |              | The description of the quiz. May also be [provided in MD file](#quiz-descriptions). |
| `date`                  | Plain String   | false     | today        | An [ISO 8601](https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat) date string. |
| `time_limit_mins`       | Integer        | false     | null/None    | The time limit of the quiz, null/None for no limit. |
| `shuffle_answers`       | Boolean        | false     | true         | Whether to shuffle question answers/choices, see [Answer Shuffling](#answer-shuffling). |
| `pick_with_replacement` | Boolean        | false     | true         | Whether to select questions from groups with replacement, see [Question Selection from Groups](#question-selection-from-groups). |
| `version`               | Plain String   | false     | current git commit hash | The title of the quiz. |
| `groups`                | Object         | true      |              | The question groups. |


Below are some common fields used in the **group** JSON configuration.
The `Inherited?` column indicates values that will be inherited by questions within the group.

| Key                     | Type           | Required? | Default      | Inherited? | Description |
|-------------------------|----------------|-----------|--------------|------------|-------------|
| `name`                  | Plain String   | true      |              | true       | The name of the question group. |
| `pick_count`            | Integer        | false     | 1            | false      | The number of questions to randomly pick from this group, see [Question Selection from Groups](#question-selection-from-groups). |
| `points`                | Number         | false     | 10           | true       | The number of points each question from this group is worth. |
| `shuffle_answers`       | Boolean        | false     | true         | true       | Whether to shuffle question answers/choices, see [Answer Shuffling](#answer-shuffling). |
| `pick_with_replacement` | Boolean        | false     | true         | false      | Whether to select questions from groups with replacement, see [Question Selection from Groups](#question-selection-from-groups). |
| `custom_header`         | Plain String   | true      | null/None    | true       | An alternate header for a question. An empty string for no header. |
| `skip_numbering`        | Boolean        | true      | false        | true       | Whether this question should skip incrementing the question number. |
| `hints`                 | Object         | true      | empty object | true       | Formatting hints passed the converter about the questions in this group. |
| `hints_first`           | Object         | true      | empty object | true*      | Hints inherited only by the first question in this group. |
| `hints_last`            | Object         | true      | empty object | true*      | Hints inherited only by the last question in this group. |
| `questions`             | Plain String   | true      |              | false      | The questions in the group. |

### Answer Shuffling

By default, answers/choices for each question will be shuffled.
This behavior can be controlled with the `shuffle_answers` option that appears at the quiz, group, and question level.
To know if a question's answers will be shuffled, take the conjunction of `shuffle_answers` values for that question's
config, group, and quiz (with the default value being `true`).

### Question Selection from Groups

When selecting answers from a question group,
the `pick_count` field of a group is used to determine how many questions for choose from each group
(with the default being 1).
By default, questions are chosen [with replacement](https://en.wikipedia.org/wiki/Sampling_(statistics)#Replacement_of_selected_units),
with respects to different variants.
This means that when variants are created, they could have randomly chosen the same questions from a group.
The `pick_with_replacement` field of a question/group can be used to override this behavior
(using the same conjunction semantics see in [Answer Shuffling](#answer-shuffling)).
If you choose to pick questions without replacement (`pick_with_replacement`: false`),
then you have to ensure you have enough questions in the group to distribute amongst all variants.
If you do not have enough questions, then a warning will be output and some questions will be chosen with replacment.

### Question Prompts

Question prompts can be provided in two ways:
 - In a "prompt" field in the `question.json`.
 - In a file adjacent to the `question.json` file called `prompt.md`.

Putting the prompt directly in the JSON can be convenient for questions with short or simple prompts.
But for larger prompts that may involve things like tables and images,
having a whole file just for the prompt is generally recommended.

**WARNING**: Remember that in JSON backslashes will need to be escaped.
So prompts written in JSON will need to escape backslashes
(which then in-turn may be used to escape characters in QuizComp markdown).

For example, in markdown you may have a prompt like:
```
This is a cool\-ish question.
```

In JSON this would need to be:
```
"prompt": "This is a cool\\-ish question."
```

### Quiz Descriptions

Like question prompts, quiz descriptions can either be specified in the quiz's JSON file,
or in an adjacent file with the same base filename as the quiz's JSON file but with the `md` extension.

For example, the description could be in the `my_quiz.json` file:
```
"description": "Look at my awesome quiz\\!"
```

Or, it can be in the `my_quiz.md` file in the same directory as `my_quiz.json`:
```
Look at my awesome quiz\!
```
