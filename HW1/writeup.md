# Assignment 1
---

## Problem (unicode1): Understanding Unicode
- (a) What Unicode character does chr(0) return?
    空字符，返回'\x00'
- (b) How does this character’s string representation (__repr__()) differ from its printed representation?
    chr(0).__repr__()返回"'\\x00'"，是返回字符串，而打印的print(chr(0))什么也不显示，因为它仅仅是空字符
- (c) What happens when this character occurs in text?
    当它出现在字符串内部，会被保留为\x00，但在打印时同样不会显示任何内容

## Problem (unicode2): Unicode Encodings
- (a) What are some reasons to prefer training our tokenizer on UTF-8 encoded bytes, rather than UTF-16 or UTF-32? It may be helpful to compare the output of these encodings for various input strings.
    同一个字符串“”，使用UTF-8编码为b'hello! \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf!'，使用UTF-16编码为b'\xff\xfeh\x00e\x00l\x00l\x00o\x00!\x00 \x00S0\x930k0a0o0!\x00'，使用UTF-32编码为b'\xff\xfe\x00\x00h\x00\x00\x00e\x00\x00\x00l\x00\x00\x00l\x00\x00\x00o\x00\x00\x00!\x00\x00\x00 \x00\x00\x00S0\x00\x00\x930\x00\x00k0\x00\x00a0\x00\x00o0\x00\x00!\x00\x00\x00'。因此，UTF-8编码更节省空间。
- (b) Consider the following (incorrect) function, which is intended to decode a UTF-8 byte string into a Unicode string. Why is this function incorrect? Provide an example of an input byte string that yields incorrect results.
    ```python
    def decode_utf8_bytes_to_str_wrong(bytestring: bytes):
        return "".join([bytes([b]).decode("utf-8") for b in bytestring])
    >>> decode_utf8_bytes_to_str_wrong("hello".encode("utf-8"))
    'hello'
    ```
    代码将每个bytes单独进行解码，然而实际上可能多个bytes对应于一个字符，所以出现了错误。例如，"你".encode("utf-8")编码为三个字节b'\xe4\xbd\xa0'，逐字节解码时报错UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe4 in position 0: unexpected end of data
- (c) Give a two byte sequence that does not decode to any Unicode character(s).
    ```python
    >>> print(b'\xbd\xa0'.decode("utf-8"))
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbd in position 0: invalid start byte
    ```

