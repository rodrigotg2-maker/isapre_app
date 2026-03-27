import pandas as pd

from config import (
    BUDGET_PENALTY_FACTOR,
    MATERNITY_BONUS_HOSP,
    MATERNITY_BONUS_TOPE,
)


def min_max_norm(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)


def normalize_weights(weights_dict):
    total = sum(weights_dict.values())
    if total == 0:
        return {k: 0 for k in weights_dict.keys()}
    return {k: v / total for k, v in weights_dict.items()}


def calculate_score(df, weights, budget=None, maternity=False):
    df = df.copy()

    # Normalización
    df["precio_norm"] = 1 - min_max_norm(df["precio_pesos"])
    df["hospitalario_norm"] = min_max_norm(df["hospitalario_num"])
    df["ambulatorio_norm"] = min_max_norm(df["ambulatorio_num"])
    df["tope_norm"] = min_max_norm(df["tope_anual_uf"])

    # Pesos normalizados
    weights = normalize_weights(weights)

    # Aportes al score
    df["aporte_precio"] = weights["precio"] * df["precio_norm"]
    df["aporte_hospitalario"] = weights["hospitalario"] * df["hospitalario_norm"]
    df["aporte_ambulatorio"] = weights["ambulatorio"] * df["ambulatorio_norm"]
    df["aporte_tope"] = weights["tope_anual"] * df["tope_norm"]

    # Score base
    df["score_base"] = (
        df["aporte_precio"] +
        df["aporte_hospitalario"] +
        df["aporte_ambulatorio"] +
        df["aporte_tope"]
    )

    # Penalización por presupuesto
    df["penalizacion_presupuesto"] = 0.0
    if budget is not None and budget > 0:
        exceso = (df["precio_pesos"] - budget) / budget
        exceso = exceso.clip(lower=0)
        penalizacion = exceso.clip(upper=BUDGET_PENALTY_FACTOR)
        df["penalizacion_presupuesto"] = penalizacion

    # Bonus maternidad
    df["bonus_maternidad"] = 0.0
    if maternity:
        df["bonus_maternidad"] = (
            MATERNITY_BONUS_HOSP * df["hospitalario_norm"] +
            MATERNITY_BONUS_TOPE * df["tope_norm"]
        )

    # Score final
    df["score"] = (
        df["score_base"]
        - df["penalizacion_presupuesto"]
        + df["bonus_maternidad"]
    )

    # Ranking
    df = df.sort_values(by="score", ascending=False).reset_index(drop=True)

    return df