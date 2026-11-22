"""Cómo se escriben los números en las métricas: con formato argentino. Lo usan el wizard y las bibliotecas."""


# Escribe un número con formato argentino: 133812 → "133.812" y 21.1 → "21,1".
def number_es(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


# Pasa un número de 0 a 1 a porcentaje: 0.93 → "93%".
def percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{round(value * 100)}%"
