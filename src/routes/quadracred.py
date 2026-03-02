from datetime import datetime
import re

from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, Header, HTTPException, status
import requests
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models import ServiceSimulation
from src.routes.auth import get_user_from_api_key
from src.utils.sendMail import QuadracredEmailData, send_quadracred_email
from src import schemas

router = APIRouter()

FORM_URL = "https://simulador.quadracred.com.br/cadastros/addsimulacaopb"


def calculate_age(date_str: str) -> int:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            birth_date = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    else:
        raise HTTPException(status_code=400, detail="invalid data_nascimento format")

    today = datetime.utcnow().date()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def parse_brl_currency(value: str) -> float:
    sanitized = value.replace(".", "").replace(",", ".").strip()
    try:
        return float(sanitized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid currency value") from exc


def format_brl_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def extract_imprimir_link(html: str) -> str | None:
    match = re.search(r"(https?://[^\"\']*pdf/[^\"\']+)", html)
    if match:
        return match.group(1)
    return None


@router.post(
    "/simulador",
    response_model=schemas.SimulationResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_simulation(
    payload: schemas.SimulationData,
    db: Session = Depends(get_db),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> schemas.SimulationResponse:
    get_user_from_api_key(db, api_key)

    session = requests.Session()
    headers = {
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "pt-BR,pt;q=0.5",
        "Cache-Control": "max-age=0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://simulador.quadracred.com.br",
        "Referer": FORM_URL,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
    }

    try:
        response = session.get(FORM_URL, headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="failed to access form") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="failed to access form")

    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if not token_input or not token_input.get("value"):
        raise HTTPException(status_code=502, detail="missing form token")

    idade = calculate_age(payload.data_nascimento)
    valor_entrada_num = parse_brl_currency(payload.valor_imovel) - parse_brl_currency(
        payload.valor_afinanciar
    )
    valor_entrada = format_brl_currency(valor_entrada_num)

    form_payload = {
        "_token": token_input["value"],
        "tipo_simulacao": "SG",
        "tipo_pessoa": "CI",
        "nome": payload.nome,
        "data_nascimento": payload.data_nascimento,
        "idade": str(idade),
        "faixa": "1",
        "telefone": payload.telefone,
        "email": payload.email,
        "valor_imovel": payload.valor_imovel,
        "valor_afinanciar": payload.valor_afinanciar,
        "valor_entrada": valor_entrada,
        "valor_renda_bruta": payload.valor_renda_bruta,
        "valor_fgts": payload.valor_fgts,
        "valor_renda_liquida": payload.valor_renda_liquida,
        "qtd_parcelas": payload.qtd_parcelas,
        "aceito_termo": "S",
    }

    try:
        post_response = session.post(FORM_URL, headers=headers, data=form_payload, timeout=20)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="failed to submit form") from exc

    if post_response.status_code >= 400:
        raise HTTPException(status_code=502, detail="failed to submit form")

    imprimir_link = extract_imprimir_link(post_response.text)
    if not imprimir_link:
        raise HTTPException(status_code=502, detail="failed to find imprimir link")

    simulation = ServiceSimulation(
        nome=payload.nome,
        data_nascimento=payload.data_nascimento,
        telefone=payload.telefone,
        email=payload.email,
        valor_imovel=payload.valor_imovel,
        valor_afinanciar=payload.valor_afinanciar,
        valor_renda_bruta=payload.valor_renda_bruta,
        valor_renda_liquida=payload.valor_renda_liquida,
        valor_fgts=payload.valor_fgts,
        qtd_parcelas=payload.qtd_parcelas,
        link_simulacao=imprimir_link,
    )
    db.add(simulation)
    db.commit()

    valor_imovel_formatado = format_brl_currency(parse_brl_currency(payload.valor_imovel))
    email_payload = QuadracredEmailData(
        nome=payload.nome,
        email=payload.email,
        link=imprimir_link,
        valorImovel=f"R$ {valor_imovel_formatado}",
        valorEntrada=f"R$ {valor_entrada}",
        prazo=str(payload.qtd_parcelas),
    )

    email_status = "Email sent successfully"
    try:
        await send_quadracred_email(email_payload)
    except Exception as exc:
        email_status = f"Email failed: {exc}"

    return schemas.SimulationResponse(
        imprimir_link=imprimir_link,
        email_status=email_status,
    )
