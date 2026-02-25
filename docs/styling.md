# Styling

Styling can be used in the QuizComp to change the visual appearance of content.
If you want to change the location or flow of information,
then you are looking for [template hints](/docs/builtin-templates.md).

Styling in the Quiz Composer is done via *style blocks* where specific options can be set.
Style blocks are specified with HTML `<style>` tags.
The content inside the `<style>` tags must be a JSON object.
However, the opening and closing braces of the JSON object may also be omitted.
(Note the this is different than the traditional CSS that would usually be inside an HTML `<style>` tag.

For example, the following style block will set the font size.
```
<style>
    "font-size": 12
</style>
```

The alternative, full version:
```
<style>
    {
        "font-size": 12
    }
</style>
```

By default, a style block will apply to all content in the document,
even if that content appears before or after the style block.
To set styling information for a subset of your document,
see the [Blocks & Style Blocks](#blocks--style-blocks) section.

The styling functionality provided is intended to be simple and cover some common use cases.
If you have styling needs that are not covered here,
then you can achieve you desired style by editing the output of the QuizComp or by using a custom template.

Table of Contents:
 - [FAQ](#faq)
   - [How do I left/center/right align something](#faq-align)
   - [How do I resize an image?](#faq-resize-image)
 - [Style Options](#style-options)
   - [Alignment](#alignment)
   - [Font Size](#font-size)
   - [Image Width](#image-width)
   - [Tables](#tables)
     - [Cell Size](#cell-size)
     - [Table Borders](#table-borders)
 - [Blocks & Style Blocks](#blocks--style-blocks)
   - [Overriding Style](#overriding-style)
   - [Clearing Style](#clearing-style)
   - [Nesting Blocks](#nesting-blocks)

## FAQ

The FAQ should be the first place to check for styling questions.

<a name="faq-align"></a>
### How do I left/center/right align something?

You can align something (image, table, text, etc) using the [alignment](#alignment) style options.
For non-text things (images, tables, containers, etc) you can use the `content-align` option,
and for text alignment, you can use the `text-align` option.

Both options support the following values: {`left`, `center`, `right`}.

For example, by default the following will get you a non-aligned image:
```
![Great Dane](../tests/data/great-dane.jpg)
```

![Non-Aligned Image](/docs/resources/default-image.png)

To center align this image, you can do:
```
<style>
    "content-align": "center"
</style>

![Great Dane](../tests/data/great-dane.jpg)
```

![Center Aligned Image](/docs/resources/center-image.png)

To center align a table, but right align the text inside the table, you can do:
```
<style>
    "content-align": "center",
    "text-align": "right"
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Center Aligned Table, Right Aligned Text](/docs/resources/center-right-table.png)

See the [alignment documentation](#alignment) for more information.

<a name="faq-resize-image"></a>
### How do I resize an image?

The size of an image can be controlled using the `image-width` value.
Only the width of an image can be explicitly set,
the aspect ratio of the image will be preserved.
Image width is provided as a proportion of the image container's width.

For example, you can start with the following image:
```
![Great Dane](../tests/data/great-dane.jpg)
```

![Default Image](/docs/resources/default-image.png)

To make this image 50% smaller, you can use:
```
<style>
    "image-width": 0.5
</style>

![Great Dane](../tests/data/great-dane.jpg)
```

![Smaller Image](/docs/resources/smaller-image.png)

See the [`image-width` documentation](#image-width) for more information.

## Style Options

This section cover all the known style options
and details on their semantics.
For all options, `null` is always an allowed value,
and indicates that the default behavior should be used.

### Alignment

| Key             | Type   | Default Value | Allowed Values              | Notes |
|-----------------|--------|---------------|-----------------------------|-------|
| `content-align` | string | `null`        | {`left`, `center`, `right`} | Default alignment depends on output format. |
| `text-align`    | string | `null`        | {`left`, `center`, `right`} | Default alignment depends on output format. |

Alignment determines where on the horizontal axis content will appear:
`left`, `center`, or `right`.
Objects are split into two groups for the purposes of alignment:
non-text (content) and text.
Non-text (content) objects (images, tables, containers, etc) are aligned using the `content-align` key,
while text is aligned using the `text-align` key.

When not specified, the output format/converter determines alignment.

For example, to center align a table but right align the text inside the table:
```
<style>
    "content-align": "center",
    "text-align": "right"
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Center Aligned Table, Right Aligned Text](/docs/resources/center-right-table.png)

*Warning*: Alignment does not work well within TeX documents.
In TeX, content alignment will also affect text and text alignment will not work within normal paragraphs.

### Font Size

| Key         | Type  | Default Value | Allowed Values  | Notes |
|-------------|-------|---------------|-----------------|-------|
| `font-size` | float | `null`        | (0.0, infinity] | Size in points. |

`font-size` can be used to set the font size **in points** ([typographic points](https://en.wikipedia.org/wiki/Point_(typography)).
Fractional point sizes (e.g. 12.5) are allowed,
but the exact support depends on the output format.

For example, a 12 point font can be set with:
```
<style>
    "font-size": 12
</style>
```

### Image Width

| Key           | Type  | Default Value | Allowed Values  | Notes |
|---------------|-------|---------------|-----------------|-------|
| `image-width` | float | 1.0           | (0.0, 1.0]      | Width relative to container. |

`image-width` can be used to set the width of an image.
The width is given as **a proportion** of the image's parent container's width.
This will typically mean the width of the page.
So `0.5` will set the image size to half of it's container.
Values above 1.0 are allowed, but the behavior is undefined.

Use the full width:
```
<style>
    "image-width": 1.0
</style>
```

![Default Image](/docs/resources/default-image.png)

Use half the available width:
```
<style>
    "image-width": 0.5
</style>
```

![Smaller Image](/docs/resources/smaller-image.png)

### Tables

| Key                  | Type    | Default Value | Allowed Values    | Notes |
|----------------------|---------|---------------|-------------------|-------|
| `table-head-bold`    | boolean | `true`        | {`true`, `false`} | Bold table headers. |
| `table-head-rule`    | boolean | `true`        | {`true`, `false`} | Insert a rule (line) after the header row. |
| `table-cell-height`  | float   | `1.5`         | [1.0, infinity]   | In [em](https://en.wikipedia.org/wiki/Em_(typography)). Set the vertical size in a cell. |
| `table-cell-width`   | float   | `1.5`         | [1.0, infinity]   | In [em](https://en.wikipedia.org/wiki/Em_(typography)). Set the horizontal size in a cell. |
| `table-border-table` | boolean | `false`       | {`true`, `false`} | Sets the border *around* the table. |
| `table-border-cells` | boolean | `false`       | {`true`, `false`} | Sets the border *inside* the table (around each cell). |

Some basic options to control the look of tables are provided.

#### Cell Size

The size of cells can be set using the `table-cell-height` and `table-cell-width` options.
These options take a value no smaller than 1.0 in [em units](https://en.wikipedia.org/wiki/Em_(typography)).
Note that exact table size computations depend on the output format
and typically are the maximum of all the cells in a column/row.

To demonstrate, start with the following table:
```
<style>
    "text-align": "center"
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Default Table](/docs/resources/table-default.png)

The text alignment is not necessary, but makes the example easier to see.

To make a very tight table, you can use 1.0:
```
<style>
    "text-align": "center",
    "table-cell-height": 1.0,
    "table-cell-width": 1.0
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Tight Table](/docs/resources/table-tight.png)

To make a very spacious table, you can use something larger (like 2.0):
```
<style>
    "text-align": "center",
    "table-cell-height": 2.0,
    "table-cell-width": 2.0
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Loose Table](/docs/resources/table-loose.png)

#### Table Borders

There are two options that control border for tables:
`table-border-table` and `table-border-cells`.
Both are off (`false`) by default.
`table-border-table` controls borders *around* the table itself,
while `table-border-cells` controls the borders *inside* the table (and around each cell).
Note that any cell border that overlaps with the border of the actual table
(e.g., the top border of the first row) is controlled by `table-border-table` and **not** `table-border-cells`.

To get a table with full borders, use:
```
<style>
    "table-border-table": true,
    "table-border-cells": true
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Table Full Border](/docs/resources/table-border-full.png)

To get a table that only has dividers/borders between cells and not around the table itself, use:
```
<style>
    "table-border-table": false,
    "table-border-cells": true
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Table Inner Border](/docs/resources/table-border-inner.png)

To get a table that only has an outer border, user:
```
<style>
    "table-border-table": true,
    "table-border-cells": false
</style>

| ID | Value |
|----|-------|
| 1  | 1.23  |
| 45 | 6.7   |
```

![Table Outer Border](/docs/resources/table-border-outer.png)

## Blocks & Style Blocks

A styling rule applies within the *block* it was declared in,
and all children of that block.
By default, any QuizComp document starts out in a default block (called the "root" block).

Further blocks can be explicitly defined by surrounding content with the `:::block` and `:::` notation
(using the [Markdown container](https://ref.coddy.tech/markdown/markdown-custom-containers) extended syntax).
These values should appear on their own lines.

For example, here we have the root block with a single child block:
```
Root Block

:::block

Child Block

:::

Still Root Block
```

A styling option set in the root block will apply to all children (and descendants).
```
<style>
    "font-size": 13
</style>

Root Block, will use 13pt font.

:::block

Child Block, will also use 13pt font.

:::
```

However, style defined in a child block will not apply to any parents, ancestors, or siblings.
```
Root Block, will use the default font size.

:::block

<style>
    "font-size": 13
</style>


Child Block, will use 13pt font.

:::
```

### Overriding Style

If the same styling rule is defined in a child block,
the value defined in the child will override the parent's value.

```
<style>
    "font-size": 13
</style>

Root Block, will use 13pt font.

:::block

<style>
    "font-size": 24
</style>


Child Block, will use 24pt font.

:::
```

### Clearing Style

To clear an option set by a parent block
(and therefore use the default style),
an option can be set to the `null` value.

```
<style>
    "font-size": 13
</style>

Root Block, will use 13pt font.

:::block

<style>
    "font-size": null
</style>


Child Block, will use the default font size.

:::
```

### Nesting Blocks

Blocks can be nested within one another.
To do so, parent and child blocks must use a different number of colons
(with the beginning and ending markers for a block having the same number).
You can use anywhere from 3 - 10 colons for marking a block.
The outer block **must** have more colons than any inner blocks.

```
This text is in the root (implicit) block.

::::block

This text is inside the outter block (with four colons).

:::block

This text is inside the inner block (with three colons).

:::

::::
```
