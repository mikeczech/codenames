# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.7.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% jupyter={"outputs_hidden": true}
# !python -m spacy download en_core_web_lg

# %%
# %load_ext lab_black

# %%
import spacy
import numpy as np
from tqdm.notebook import tqdm

from itertools import combinations

# %%
nlp = spacy.load("en_core_web_lg")

# %%
nlp.meta["vectors"]

# %%
india = nlp.vocab.strings["india"]
germany = nlp.vocab.strings["germany"]
apple = nlp.vocab.strings["apple"]

# %%
nlp.vocab[india].similarity(nlp.vocab[germany])

# %%
nlp.vocab[india].similarity(nlp.vocab[apple])


# %%
def similarity(word_a, word_b):
    word_a = nlp.vocab.strings[word_a]
    word_ab = nlp.vocab.strings[word_b]
    return nlp.vocab[word_a].similarity(nlp.vocab[word_b])


# %%
red_words = [
    "arm",
    "stick",
    "organ",
    "field",
    "piano",
    "agent",
    "leprechaun",
    "swing",
    "india",
]

blue_words = [
    "roulette",
    "stock",
    "dinosaur",
    "embassy",
    "hole",
    "turkey",
    "fire",
    "shakespeare",
]

neutral_words = ["jack", "point", "laser", "lemon", "unicorn", "pyramid", "figure"]
assassin_words = ["hollywood"]

vocab = list(nlp.vocab.strings)
len(vocab)

# %%
[(w, w in vocab) for w in red_words]

# %%
X = np.array([[similarity(w_a, w) for w in vocab] for w_a in red_words])
X.shape

# %%
np.save("x.npy", X)

# %%
# !ls

# %%
X.shape


# %%
def is_valid(suggested_word):
    suggested_word = suggested_word.lower()
    for w in all_words:
        w = w.lower()
        if (suggested_word in w) or (w in suggested_word):
            return False
    return True


def produce_clues(words, max_num_words=4):
    N = len(words)
    clues = {}
    for l in tqdm(list(range(1, max_num_words + 1))):
        for c in tqdm(list(combinations(range(N), l))):
            inds = X[np.array(c)].mean(axis=0).argsort()[::-1][:35]
            avg_sims = np.sort(X[np.array(c)].mean(axis=0))[::-1][:35]

            for i, avg_sim in zip(inds, avg_sims):
                if is_valid(vocab[i]):
                    clues[tuple([words[j] for j in c])] = (
                        vocab[i].lower(),
                        avg_sim,
                    )
                    break

    return clues


# %%
produce_clues(red_words)

# %%
