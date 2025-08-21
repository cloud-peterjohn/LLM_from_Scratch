import os
from collections import defaultdict
import regex as re

def train_bpe_tokenizer(
    input_path: str, max_vocab_size: int, special_tokens: list[str]
) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    """
    input_path: str Path to a text file with BPE tokenizer training data.
    max_vocab_size: int A positive integer that defines the maximum final vocabulary size (including the initial byte vocabulary, vocabulary items produced from merging, and any special tokens).
    special_tokens: list[str] A list of strings to add to the vocabulary. These special tokens do not otherwise affect BPE training. Your BPE training function should return the resulting vocabulary and merges:
    vocab: dict[int, bytes] The tokenizer vocabulary, a mapping from int (token ID in the vocabulary) to bytes (token bytes).
    merges: list[tuple[bytes, bytes]] A list of BPE merges produced from training. Each list item is a tuple of bytes (<token1>, <token2>), representing that <token1> was merged with <token2>. The merges should be ordered by order of creation.
    """
    # Initialize vocabulary: id -> bytes
    vocab = {i: bytes([i]) for i in range(256)}  # UTF-8: [0, 255] id -> bytes
    # Add special tokens to vocab
    for special_token in special_tokens:
        special_token_bytes = special_token.encode("utf-8")
        if special_token_bytes not in vocab.values():
            vocab[len(vocab)] = bytes(special_token_bytes)
        else:
            # already exists in vocab, skip
            continue

    # Read data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8")

    # Delete special tokens from data
    for special_token in special_tokens:
        text = text.replace(special_token, " ")
    # Pre-tokenization
    PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    pre_tokens = [m.group(0) for m in re.finditer(PAT, text)]
    tokens = [pt.encode("utf-8") for pt in pre_tokens]
    print(f'Initial vocabulary size: {len(vocab)}, Initial tokens: {len(tokens)}')

    # Train BPE
    merges_history = []  # list of (token1, token2)
    while len(vocab) < max_vocab_size:
        # No more pairs to merge
        if len(tokens) < 2:
            break
        # A Merge
        pairs_frequency = defaultdict(int)
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            # Record pair frequency
            pairs_frequency[pair] += 1
        # Most frequent pair
        best_pair = None
        max_freq = -1
        for pair, freq in pairs_frequency.items():
            if freq > max_freq or (freq == max_freq and pair > best_pair):
                best_pair = pair
                max_freq = freq
        # Merge the best pair
        merged_token = best_pair[0] + best_pair[1]
        # Add new token to vocab
        vocab[len(vocab)] = merged_token
        merges_history.append(best_pair)
        # Update tokens list
        new_tokens = []
        curr_idx = 0
        while curr_idx < len(tokens):
            if curr_idx == len(tokens) - 1:
                # Last token, just add it
                new_tokens.append(tokens[curr_idx])
                curr_idx += 1
            else:
                if (tokens[curr_idx] == best_pair[0]) and (
                    tokens[curr_idx + 1] == best_pair[1]
                ):
                    # merge
                    new_tokens.append(merged_token)
                    curr_idx += 2
                else:
                    new_tokens.append(tokens[curr_idx])
                    curr_idx += 1
        tokens = new_tokens
        print(f'>>> Training BPE: Merged {best_pair} -> {merged_token}, Vocab size: {len(vocab)} / {max_vocab_size}')
    print(f'Final vocabulary: {vocab}')
    return vocab, merges_history


if __name__ == "__main__":
    input_path = "HW1/data/TinyStoriesV2-GPT4-valid.txt"
    vocab_size = 300
    special_tokens = ["<|endoftext|>"]
    vocab, merges = train_bpe_tokenizer(input_path, vocab_size, special_tokens)
