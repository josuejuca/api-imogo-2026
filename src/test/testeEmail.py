import asyncio
from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.sendMail import QuadracredEmailData, send_quadracred_email


def test_send_quadracred_email():
    required_vars = [
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_FROM",
        "MAIL_PORT",
        "MAIL_SERVER",
    ]
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        print(
            "Missing MAIL_* settings in .env or environment: "
            + ", ".join(missing)
        )
        return

    data = QuadracredEmailData(
        nome="Juca Silva",
        email="jucaimogo@gmail.com",
        link="https://simulador.quadracred.com.br/cadastros/pdf/eyJpdiI6ImZHS2oxMWN5Zjc3amx1c2NKZU9qdGc9PSIsInZhbHVlIjoiWGpmdm16bXc3UkE1ekVpS2dYK2tOQT09IiwibWFjIjoiOTc0NjljNmZjNTJiYmRhZjZiM2M0OTBmM2MyMWQ4NmUxYmUyNWZjMzdiOTdmOTc1ZTBlNTgzM2E5MTliNjE1NiIsInRhZyI6IiJ9",
        valorImovel="R$ 500.000,00",
        valorEntrada="R$ 150.000,00",
        prazo="24 meses",
    )
    asyncio.run(send_quadracred_email(data))

if __name__ == "__main__":
    test_send_quadracred_email()