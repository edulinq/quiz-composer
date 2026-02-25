# QuizComp Markdown Syntax

The Quiz Composer uses [Markdown](https://en.wikipedia.org/wiki/Markdown) for text fields (unless specified otherwise).
Specifically, we use the [CommonMark](https://commonmark.org/) standard (v0.31.2) for Markdown.
This means that most Markdown tutorials you encounter will usually work for the Quiz Composer.
You can stick to CommonMark references if you want to be fully safe,
but most simples cases are the same across all Markdown standards.

Below are some resources to reference or learn Markdown:
 - [CommonMark Reference](https://commonmark.org/help/)
 - [Markdown Guide](https://www.markdownguide.org/basic-syntax/)
 - [Github's Markdown Tutorial](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
 - [Cheatsheet for Github Flavored Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

Any variations from the CommonMark specification are listed in this document.

Table of Contents:
 - [Math](#math)
 - [Tables](#tables)
 - [HTML](#html)
 - [Blocks](#blocks)
 - [Comments](#comments)
 - [Placeholders](#placeholders)
 - [Style](#style)
 - [Anti-Recommendations](#anti-recommendations)
   - [Indented Code Blocks](#indented-code-blocks)

## Math

LaTeX-style math is supported in the Quiz Composer.
When rendering to a PDF, standard LaTeX equation rendering is used (along with the `amsmath` package).
When rendering to HTML, [KaTeX](https://katex.org/) is used.

Inline math can be used with a single dollar sign (`$`):
```
This text has some math $ f(x) = x_i + x^2 + \alpha $ right in the middle of it.
```

Math blocks can be used with two dollar signs (`$$`):
```
The following is an equation block:
$$
    f(x) = x_i + x^2 + \alpha
$$
```

## Tables

[Github-style tables](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables) are supported.
Note that these tables require a header row.

```
| Some | Header | Row |
|------|--------|-----|
| 1    | -2     | N/A |
| *a*  | **b**  | $x$ |
```

## Blocks

The Quiz Composer allows content to be separated into different logical blocks (usually for styling reasons).
This is done using the [Markdown container](https://ref.coddy.tech/markdown/markdown-custom-containers) extended syntax.

```
Text outside the block.

:::block

Text inside the block.

:::
```

See the [styling documentation on blocks](/docs/styling.md#blocks--style-blocks) for full details.

## HTML

HTML is generally ignored (and removed) within any Quiz Composer documents.
Any counterexamples are listed in this document.

## Comments

Comments may be inserted into your documents using [HTML comments](https://developer.mozilla.org/en-US/docs/Web/HTML/Comments).
Comment will not be output into a quiz,
and can be useful as notes to others who are working on the quiz.

```
<!--
Here is a comment
that goes over multiple lines.
-->

Some text. <!-- Here is a comment after text. -->

Some <!-- Here is a comment between text. --> text.
```

## Placeholders

Placeholders are used in some question types to indicate a "blank" that needs to be filled in.
Placeholders are implemented using an HTML `<placeholder>` tag with the name/identifier within the tag.
For example:

```
<placeholder>part1</placeholder>
```

## Style

The Quiz Composer has a [style system](/docs/styling.md)
for modifying a small number of styling options.
Style is specified using an HTML `<style>` tag with JSON inside:
```html
<style>
    {
        "font-size": 12
    }
</style>
```

See the [styling documentation](/docs/styling.md) for full details.

## Anti-Recommendations

Markdown (CommonMark) supports [many different features](https://spec.commonmark.org/0.31.2/).
Some of these we do not recommend using in the context of the Quiz Composer.
They will work, but are easy to get wrong or have unintended output.

### Indented Code Blocks

[Indented Code Blocks](https://spec.commonmark.org/0.31.2/#indented-code-blocks)
allow you to specify code blocks just by indenting your code:
```
    This is a code block because it is indented.
    More code.
```

Because of whitespace stripping that can happen at multiple places,
indented code blocks must not appear as the first or last pieces of text in a document.

Instead of indented code blocks, we recommend using the more standard code fences:
````
```
This is a code block because it is inside a fence of backticks.
```
````
