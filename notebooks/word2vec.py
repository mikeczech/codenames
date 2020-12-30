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

# %%
# !python -m spacy download en_core_web_lg

# %%
# %load_ext lab_black

# %%
import spacy
import numpy as np
import pandas as pd
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
len(all_words)

# %%
df_all_words = pd.DataFrame(
    {
        "word": all_words,
        "color": ["red"] * len(red_words)
        + ["blue"] * len(blue_words)
        + ["neutral"] * len(neutral_words)
        + ["assassin"] * len(assassin_words),
    }
)

df_all_words

# %%
vocab = list(nlp.vocab.strings)
len(vocab)

# %%
similarities = np.array([[similarity(w_a, w) for w in vocab] for w_a in words])
similarities.shape

# %%
np.save("similarities.npy", similarities)


# %%
def similarity(word_a, word_b):
    word_a = nlp.vocab.strings[word_a]
    word_b = nlp.vocab.strings[word_b]
    return nlp.vocab[word_a].similarity(nlp.vocab[word_b])


def is_valid(suggested_word):
    for w in words:
        w = w.lower()
        if (suggested_word in w) or (w in suggested_word):
            return False
    return True


def produce_clues(
    color, df_all_words, similarities, max_num_words=4, max_suggestions=35
):
    word_index = df_all_words[df_all_words.color == color].index

    selection_col = []
    suggestion_col = []
    hint_len_col = []
    score_col = []
    for hint_len in tqdm(range(1, max_num_words + 1), total=max_num_words):
        
        for selection in tqdm(list(combinations(word_index, hint_len))):
            selection = np.array(selection)
            agg_similarities = similarities[selection].mean(axis=0)
            
            suggestion_indices = agg_similarities.argsort()[::-1][:max_suggestions]
            suggestion_scores = agg_similarities[suggestion_indices]
            for index, score in zip(suggestion_indices, suggestion_scores):
                suggested_word = vocab[index].lower()
                if is_valid(suggested_word):
                    selection_words = tuple([words[j] for j in selection])
                    selection_col.append(selection_words)
                    suggestion_col.append(suggested_word)
                    hint_len_col.append(hint_len)
                    score_col.append(score)
                    break

    return (
        pd.DataFrame(
            {
                "selection": selection_col,
                "suggestion": suggestion_col,
                "hint_len": hint_len_col,
                "score": score_col,
            }
        )
        .sort_values(by="score", ascending=False)
        .reset_index(drop=True)
    )


# %%
df_clues = produce_clues("red", df_all_words, similarities)

# %%
df_clues.sort_values(by="score", ascending=False).head(20)

# %%
