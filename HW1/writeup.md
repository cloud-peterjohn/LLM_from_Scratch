# Assignment 1
---

## Problem (unicode1): Understanding Unicode
- (a) What Unicode character does chr(0) return?
空字符，返回'\x00'
- (b) How does this character’s string representation (__repr__()) differ from its printed representation?
chr(0).__repr__()返回"'\\x00'"，是返回字符串，而打印的print(chr(0))什么也不显示，因为它仅仅是空字符
- (c) What happens when this character occurs in text?
当它出现在字符串内部，会被保留为\x00，但在打印时同样不会显示任何内容