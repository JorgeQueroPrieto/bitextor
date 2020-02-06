#!/usr/bin/env python3

#  This file is part of Bitextor.
#
#  Bitextor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bitextor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Bitextor.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import argparse
import base64
import string
import lzma
from external_processor import ExternalTextProcessor
from nltk.data import load

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/utils")
from utils.common import open_xz_or_gzip_or_plain


def extract_encoded_text(encoded, sent_tokeniser, word_tokeniser, morph_analyser):
    tokenized_segments = ""
    content = base64.b64decode(encoded).decode("utf-8").replace("\t", " ")
    if isinstance(sent_tokeniser, str):
        proc_sent = ExternalTextProcessor(sent_tokeniser.split())
        tokenized_segments = proc_sent.process(content).strip()
    else:
        tokenized_segments = "\n".join(sent_tokeniser.tokenize(content))

    tokenized_filtered = ""

    for sent in tokenized_segments.split("\n"):
        if sum([1 for m in sent if m in string.punctuation + string.digits]) < len(sent) // 2:
            tokenized_filtered += sent + "\n"

    proc_word = ExternalTextProcessor(word_tokeniser.split())
    tokenized_text = proc_word.process(tokenized_filtered)

    if morph_analyser:
        proc_morph = ExternalTextProcessor(morph_analyser.split())
        tokenized_text = proc_morph.process(tokenized_text)

    b64sentences = base64.b64encode(tokenized_filtered.encode("utf-8"))
    b64tokenized = base64.b64encode(tokenized_text.lower().encode("utf-8"))
    return b64sentences, b64tokenized


oparser = argparse.ArgumentParser(
    description="Tool that tokenizes (sentences, tokens and morphemes) plain text")
oparser.add_argument('--text', dest='text', help='Plain text file', required=True)
oparser.add_argument('--sentence-splitter', dest='splitter', required=True, help="Sentence splitter commands")
oparser.add_argument('--word-tokenizer', dest='tokenizer', required=True, help="Word tokenisation command")
oparser.add_argument('--morph-analyser', dest='lemmatizer', help="Morphological analyser command")
oparser.add_argument('--sentences-output', default="plain_sentences.xz", dest='sent_output', help="Path of the output file that will contain sentence splitted text")
oparser.add_argument('--tokenized-output', default="plain_tokenized.xz", dest='tok_output', help="Path of the output file that will contain sentence splitted and tokenized text")

options = oparser.parse_args()

sentence_splitter = None
if options.splitter.split()[0] == "sent_tokenize()":
    language = options.splitter.split()[1]
    try:
        sentence_splitter = load('tokenizers/punkt/{0}.pickle'.format(language))
    except:
        sentence_splitter = load('tokenizers/punkt/{0}.pickle'.format("english"))
else:
    sentence_splitter = options.splitter
                                                                                            
with open_xz_or_gzip_or_plain(options.text) as reader, lzma.open(options.sent_output, "w") as sent_writer, lzma.open(options.tok_output, "w") as tok_writer:
    for line in reader:
        encoded_text = line.strip()
        sentences, tokenized = extract_encoded_text(encoded_text, sentence_splitter, options.tokenizer, options.lemmatizer)
        if sentences and tokenized:
            sent_writer.write(sentences + b"\n")
            tok_writer.write(tokenized + b"\n")
