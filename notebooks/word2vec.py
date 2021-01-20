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
# %load_ext autoreload
# %autoreload 2

# %%
import spacy
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm
from itertools import chain
from itertools import combinations

np.random.seed(0)

# %%
from codenames.game import read_wordlist_csv
from codenames.game import Game

# %%
wordlist = read_wordlist_csv("../data/codenames_wordlist.csv")

# %%
Game.create_from(wordlist)

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
codenames_wordlist = (
    pd.read_csv("../data/codenames_wordlist.csv", header=None)
    .unstack()
    .reset_index(drop=True)
    .dropna()
)
codenames_wordlist.shape

# %%
red_index = np.random.choice(codenames_wordlist.index, size=9, replace=False)
blue_index = np.random.choice(
    codenames_wordlist.drop(red_index).index, size=9, replace=False
)
neutral_index = np.random.choice(
    codenames_wordlist.drop(red_index).index.drop(blue_index), size=9, replace=False
)
assassin_index = np.random.choice(
    codenames_wordlist.drop(red_index).index.drop(blue_index).drop(neutral_index),
    size=1,
    replace=False,
)

# %%
red_words = codenames_wordlist.iloc[red_index].values
blue_words = codenames_wordlist.iloc[blue_index].values
neutral_words = codenames_wordlist.iloc[neutral_index].values
assassin_words = codenames_wordlist.iloc[assassin_index].values

# %%
all_words = np.concatenate([red_words, blue_words, neutral_words, assassin_words])
all_words

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
similarities = np.array(
    [[similarity(w_a, w) for w in vocab] for w_a in tqdm(df_all_words.word.values)]
)
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
    selection_len_col = []
    score_col = []
    for selection_len in tqdm(range(1, max_num_words + 1), total=max_num_words):

        for selection in tqdm(list(combinations(word_index, selection_len))):
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
                    selection_len_col.append(selection_len)
                    score_col.append(score)
                    break

    return (
        pd.DataFrame(
            {
                "selection": selection_col,
                "suggestion": suggestion_col,
                "selection_len": selection_len_col,
                "score": score_col,
            }
        )
        .sort_values(by="score", ascending=False)
        .reset_index(drop=True)
    )


# %%
df_clues = produce_clues("blue", df_all_words, similarities)

# %%
df_clues[df_clues.score > 0.5].head(20)

# %%
