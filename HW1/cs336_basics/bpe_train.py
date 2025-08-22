import os
import time
import regex as re
from typing import BinaryIO
from multiprocessing import Pool
from collections import defaultdict


def find_chunk_boundaries(
    file: BinaryIO,
    desired_num_chunks: int,
    split_special_token: bytes,
) -> list[int]:
    """
    Chunk the file into parts that can be counted independently.
    May return fewer chunks if the boundaries end up overlapping.
    """
    assert isinstance(
        split_special_token, bytes
    ), "Must represent special token as a bytestring"

    # Get total file size in bytes
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    chunk_size = file_size // desired_num_chunks

    # Initial guesses for chunk boundary locations, uniformly spaced
    # Chunks start on previous index, don't include last index
    chunk_boundaries = [i * chunk_size for i in range(desired_num_chunks + 1)]
    chunk_boundaries[-1] = file_size

    mini_chunk_size = 4096  # Read ahead by 4k bytes at a time

    for bi in range(1, len(chunk_boundaries) - 1):
        initial_position = chunk_boundaries[bi]
        file.seek(initial_position)  # Start at boundary guess
        while True:
            mini_chunk = file.read(mini_chunk_size)  # Read a mini chunk

            # If EOF, this boundary should be at the end of the file
            if mini_chunk == b"":
                chunk_boundaries[bi] = file_size
                break

            # Find the special token in the mini chunk
            found_at = mini_chunk.find(split_special_token)
            if found_at != -1:
                chunk_boundaries[bi] = initial_position + found_at
                break
            initial_position += mini_chunk_size

    # Make sure all boundaries are unique, but might be fewer than desired_num_chunks
    return sorted(set(chunk_boundaries))


def pre_tokenize_chunk(chunk, special_tokens):
    PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    # Remove special tokens in chunk
    for special_token in special_tokens:
        chunk = chunk.replace(special_token, "")
    # Pre-tokenization
    pre_tokens = [m.group(0) for m in re.finditer(PAT, chunk)]
    return [pt.encode("utf-8") for pt in pre_tokens]


def train_bpe_tokenizer(
    input_path: str,
    max_vocab_size: int,
    special_tokens: list[str],
    num_processes: int = 8,
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

    # Pre-tokenization
    pre_tokenization_start = time.time()
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, "rb") as f:
        # Chunk boundaries
        boundaries = find_chunk_boundaries(
            f, num_processes, special_tokens[0].encode("utf-8")
        )
        chunk_texts = []
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            # Read chunk data
            f.seek(start)  # Move file pointer to start of current chunk
            chunk = f.read(end - start).decode("utf-8", errors="ignore")
            chunk_texts.append(chunk)
        # Pre-tokenize chunks in parallel
        with Pool(processes=num_processes) as pool:
            results = pool.starmap(
                pre_tokenize_chunk, [(chunk, special_tokens) for chunk in chunk_texts]
            )
        tokens = []
        for chunk_tokens in results:
            tokens.extend(chunk_tokens)
    pre_tokenization_end = time.time()
    print(
        f"Pre-tokenization took {pre_tokenization_end - pre_tokenization_start:.2f} seconds"
    )
    print(f"Initial vocabulary size: {len(vocab)}, Initial tokens: {len(tokens)}")

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
        print(
            f">>> Training BPE: Merged {best_pair} -> {merged_token}, Vocab size: {len(vocab)} / {max_vocab_size}"
        )
    print(f"Final vocabulary: {vocab.values()}")
    return vocab, merges_history


def test():
    input_path = "HW1/data/TinyStoriesV2-GPT4-valid.txt"
    vocab_size = 300
    special_tokens = ["<|endoftext|>"]
    vocab, merges = train_bpe_tokenizer(input_path, vocab_size, special_tokens)
