import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, KFold, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression

import statsmodels.api as sm
from itertools import combinations
# ----------------------------------------------------------------------


# 1️⃣  LOAD & SPLIT  ----------------------------------------------------
df = pd.read_csv("disease_screening.csv")

X = df.drop(columns="disease")
y = df["disease"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)

# 2️⃣  FORWARD STEP-WISE SELECTION with BIC  ---------------------------
def bic(loglik, k, n):
    return -2 * loglik + k * np.log(n)

def forward_bic(X, y):
    """Return the indices of the variables chosen by forward-BIC."""
    n, p = X.shape
    remaining = list(range(p))
    selected  = []
    current_bic = np.inf

    while True:
        bic_candidates = []
        for j in remaining:
            cand = selected + [j]
            X_cand = sm.add_constant(X.iloc[:, cand])      # intercept + chosen vars
            model  = sm.MNLogit(y, X_cand).fit(method="newton", disp=False)
            bic_val = bic(model.llf, model.df_model + 1, n)   # +1 for intercept
            bic_candidates.append((bic_val, j, model))

        best_bic, best_j, best_model = min(bic_candidates, key=lambda t: t[0])

        if best_bic < current_bic:        # improvement? keep going
            current_bic = best_bic
            selected.append(best_j)
            remaining.remove(best_j)
        else:                             # stop
            break

    return selected, current_bic

idx_selected, final_bic = forward_bic(X_train, y_train)
vars_selected = X_train.columns[idx_selected].tolist()

print("BIC-selected variables:", vars_selected)
print("Final BIC on training set:", final_bic)

# 3️⃣  LASSO-PENALISED LOGISTIC REGRESSION (nested 5×5 CV) ------------
Cs = np.logspace(-3, 3, 15)          # 10⁻³ … 10³

inner_cv = KFold(n_splits=5, shuffle=True, random_state=1)
outer_cv = KFold(n_splits=5, shuffle=True, random_state=2)

# Standardise inside the pipeline -> no data leakage
pipe = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        penalty="l1",
        solver="saga",
        multi_class="multinomial",
        max_iter=2000,
        tol=1e-4,
    ),
)

search = GridSearchCV(
    estimator=pipe,
    param_grid={"logisticregression__C": Cs},
    cv=inner_cv,
    scoring="neg_log_loss",
    n_jobs=-1,
)

nested_scores = cross_val_score(search, X_train, y_train,
                                cv=outer_cv,
                                scoring="neg_log_loss",
                                n_jobs=-1)

print("Nested CV log-loss (mean  ±  std):",
      -nested_scores.mean(), "±", nested_scores.std())

# Fit once more on the full training data to obtain the single best C
search.fit(X_train, y_train)
best_C = search.best_params_["logisticregression__C"]
print("Optimal C selected by nested CV:", best_C)
