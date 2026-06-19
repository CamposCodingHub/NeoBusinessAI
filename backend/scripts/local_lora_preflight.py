"""Valida se o host suporta fine-tuning LoRA sem comprometer o sistema."""

import json
import shutil
import subprocess


def main():
    result = {
        "supported": False,
        "reason": "",
        "recommended_action": "",
    }
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        result["reason"] = "GPU NVIDIA e nvidia-smi nao encontrados."
    else:
        process = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        rows = [row.strip() for row in process.stdout.splitlines() if row.strip()]
        memory_mb = 0
        if rows:
            try:
                memory_mb = max(
                    int(row.rsplit(",", 1)[1].strip()) for row in rows
                )
            except (ValueError, IndexError):
                memory_mb = 0
        if memory_mb >= 16000:
            result["supported"] = True
            result["reason"] = "GPU compativel com QLoRA de modelos pequenos."
        else:
            result["reason"] = (
                f"VRAM detectada: {memory_mb} MB; minimo seguro: 16000 MB."
            )
    result["recommended_action"] = (
        "Continuar curadoria e exportacao do dataset. Nao iniciar treinamento "
        "de pesos neste host enquanto o preflight estiver bloqueado."
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["supported"] else 2)


if __name__ == "__main__":
    main()
