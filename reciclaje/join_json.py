"""
merge_jsons.py
Script genérico para fusionar dos archivos JSON de cursos por una clave común.
Adaptado al proyecto ULPGC ↔ LUT.

Uso:
    python merge_jsons.py ulpgc_courses.json emparejamientos.json --key code
    python merge_jsons.py lut_courses.json otro.json --key id --output resultado.json
"""
import argparse
import json
from pathlib import Path
from rich.console import Console

console = Console()


def load_json(file_path: Path) -> list[dict]:
    """Carga datos desde un archivo JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"No se encuentra {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{file_path} no contiene una lista JSON")
    return data


def clean_key(key: str) -> str:
    """Elimina espacios al inicio/final de una clave (problema conocido en ulpgc_courses.json)."""
    return key.strip() if isinstance(key, str) else key


def clean_entry(entry: dict) -> dict:
    """Limpia espacios en claves y valores string de un diccionario."""
    return {clean_key(k): (v.strip() if isinstance(v, str) else v) for k, v in entry.items()}


def merge_jsons(
    json1: list[dict],
    json2: list[dict],
    common_key: str = "code",
    clean: bool = True,
) -> list[dict]:
    """Fusiona dos listas JSON usando una clave común.
    
    - Si la clave existe en ambos, los campos del segundo sobrescriben los del primero.
    - Si la clave solo existe en uno, se incluye tal cual.
    - Si `clean=True`, se eliminan espacios en claves y valores string.
    """
    merged_data: dict[str, dict] = {}
    order: list[str] = []  # Mantiene el orden de aparición

    # 1. Añadir todas las entradas del primer JSON
    for entry in json1:
        entry = clean_entry(entry) if clean else entry
        key_value = entry.get(common_key)
        if key_value is None:
            console.print(f"[yellow]Aviso:[/yellow] Entrada sin clave '{common_key}' en archivo 1, se omite.")
            continue
        key_value = str(key_value).strip()
        if key_value not in merged_data:
            order.append(key_value)
        merged_data[key_value] = entry

    # 2. Actualizar con datos del segundo JSON
    added_new = 0
    updated = 0
    for entry in json2:
        entry = clean_entry(entry) if clean else entry
        key_value = entry.get(common_key)
        if key_value is None:
            console.print(f"[yellow]Aviso:[/yellow] Entrada sin clave '{common_key}' en archivo 2, se omite.")
            continue
        key_value = str(key_value).strip()
        if key_value in merged_data:
            merged_data[key_value].update(entry)
            updated += 1
        else:
            merged_data[key_value] = entry
            order.append(key_value)
            added_new += 1

    console.print(f"[green]✓[/green] Actualizadas: {updated} | Nuevas añadidas: {added_new}")
    return [merged_data[k] for k in order]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fusiona dos archivos JSON de cursos por una clave común."
    )
    parser.add_argument("file1", type=Path, help="Primer archivo JSON (base)")
    parser.add_argument("file2", type=Path, help="Segundo archivo JSON (se superpone al primero)")
    parser.add_argument(
        "--key", "-k",
        default="code",
        help="Clave común para el merge (default: 'code')",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Archivo de salida (default: merged_<file1>)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="No limpiar espacios en claves y valores",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    console.print(f"[cyan]Cargando {args.file1}...[/cyan]")
    data1 = load_json(args.file1)
    console.print(f"  → {len(data1)} entradas")

    console.print(f"[cyan]Cargando {args.file2}...[/cyan]")
    data2 = load_json(args.file2)
    console.print(f"  → {len(data2)} entradas")

    console.print(f"[cyan]Fusionando por clave '{args.key}'...[/cyan]")
    merged = merge_jsons(data1, data2, common_key=args.key, clean=not args.no_clean)
    console.print(f"  → {len(merged)} entradas finales")

    output_path = args.output or Path(f"merged_{args.file1.name}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    console.print(f"[bold green]✓ Guardado en {output_path}[/bold green]")


if __name__ == "__main__":
    main()