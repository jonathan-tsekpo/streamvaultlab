import pandas as pd
t = "out/tables/"
acc = pd.read_csv(t + "id_account.csv")
print(acc[acc.outcome.str.contains("404")][["source_line", "raw_value"]])      # the 5 missing films

s = pd.read_csv(t + "sensitivity.csv")
print(s[(s.window == "all years") & (s.metric == "ratio_of_totals")]
      .groupby("franchise_min_on_list")["leader"].value_counts())                 # what flips the answer

f = pd.read_csv(t + "fact_films.csv")
one = f[f.collection_films_on_list == 1][["title", "release_year", "roi", "collection_name"]]
print(len(one), "films are the only one of their collection on the list"); print(one.to_string())