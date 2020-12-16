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
# !python -m spacy download en_core_web_md`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````

# %%
# %load_ext lab_black

# %%
import spacy
import numpy as np
from tqdm.notebook import tqdm

from itertools import combinations

# %%
with open("../data/words_alpha.txt") as f:
    words = f.readlines()
words = [w.strip() for w in words]

# %%
len(words)

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
list(combinations(red_words, 2))


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

all_words = red_words + blue_words + neutral_words + assassin_words

# %%
X = np.array([[similarity(w_a, w) for w in words] for w_a in all_words])

# %%
X.shape


# %%
def is_valid(suggested_word):
    for w in all_words:
        if (suggested_word in w) or (w in suggested_word):
            return False
    return True


def produce_clue(red_words, blue_words, neutral_words, assassin_words):
    N = len(red_words)
    word = None
    best_c = None
    max_avg_sim = -np.inf

    for l in range(2, 3):
        for c in combinations(range(N), l):
            inds = X[np.array(c)].mean(axis=0).argsort()[::-1][:15]
            avg_sims = np.sort(X[np.array(c)].mean(axis=0))[::-1][:15]
            i, avg_sim = [
                (i, avg_sim) for i, avg_sim in zip(inds, avg_sims) if is_valid(words[i])
            ][0]
            if avg_sim > max_avg_sim:
                word = words[i]
                max_avg_sim = avg_sim
                best_c = c

    return word, [red_words[i] for i in best_c]


# %%
red_words

# %%
produce_clue(blue_words, red_words, neutral_words, assassin_words)

# %%
while len(red_words) > 0:
    word, combination = produce_clue(red_words, blue_words, neutral_words, assassin_words)
    print((word, combination))
    for c in combination:
        red_words.remove(c)

# %%
