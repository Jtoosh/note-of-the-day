# Design

Redesign: Move from `nltk` to `marko`.

Parse each md file into objects.

Generate snippets from each header, keep tract of headers in a breadcrumb trail.

How to do this?

```markdown
# Header 1
Text
## Header 2
More text
### Header 3
Even more text
### Header 3
Text
## Header 2
```
