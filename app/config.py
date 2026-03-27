from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

PLANES_FILE = DATA_DIR / "base_maestra_planes.csv"

REQUIRED_COLUMNS = [
    "isapre",
    "codigo",
    "nombre_plan",
    "clinica_preferente",
    "precio_pesos",
    "valor_plan_uf",
    "ges_uf",
    "costo_total_uf",
    "ambulatorio_num",
    "hospitalario_num",
    "tope_anual_uf",
    "estado",
]

BUDGET_PENALTY_FACTOR = 0.30
MATERNITY_BONUS_HOSP = 0.05
MATERNITY_BONUS_TOPE = 0.03