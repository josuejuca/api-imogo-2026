from __future__ import annotations

from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class MailSettings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	mail_username: str = Field(alias="MAIL_USERNAME")
	mail_password: str = Field(alias="MAIL_PASSWORD")
	mail_from: str = Field(alias="MAIL_FROM")
	mail_port: int = Field(alias="MAIL_PORT")
	mail_server: str = Field(alias="MAIL_SERVER")
	mail_from_name: str = Field(default="", alias="MAIL_FROM_NAME")
	mail_starttls: bool = Field(default=True, alias="MAIL_STARTTLS")
	mail_ssl_tls: bool = Field(default=False, alias="MAIL_SSL_TLS")
	use_credentials: bool = Field(default=True, alias="USE_CREDENTIALS")
	validate_certs: bool = Field(default=True, alias="VALIDATE_CERTS")


class QuadracredEmailData(BaseModel):
	nome: str
	email: str
	link: str
	valorImovel: str
	valorEntrada: str
	prazo: str


_BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BASE_DIR / ".env")
_TEMPLATES_DIR = _BASE_DIR / "src" / "templates"
_JINJA_ENV = Environment(
	loader=FileSystemLoader(str(_TEMPLATES_DIR)),
	autoescape=select_autoescape(["html", "xml", "jinja"]),
)


def _build_connection_config(settings: MailSettings) -> ConnectionConfig:
	return ConnectionConfig(
		MAIL_USERNAME=settings.mail_username,
		MAIL_PASSWORD=settings.mail_password,
		MAIL_FROM=settings.mail_from,
		MAIL_PORT=settings.mail_port,
		MAIL_SERVER=settings.mail_server,
		MAIL_FROM_NAME=settings.mail_from_name,
		MAIL_STARTTLS=settings.mail_starttls,
		MAIL_SSL_TLS=settings.mail_ssl_tls,
		USE_CREDENTIALS=settings.use_credentials,
		VALIDATE_CERTS=settings.validate_certs,
	)


async def send_quadracred_email(data: QuadracredEmailData) -> None:
	settings = MailSettings()
	conf = _build_connection_config(settings)

	template = _JINJA_ENV.get_template("emails/simulador-quadracred.jinja")
	html = template.render(
		nome=data.nome,
		valorImovel=data.valorImovel,
		valorEntrada=data.valorEntrada,
		prazo=data.prazo,
		link=data.link,
	)

	message = MessageSchema(
		subject="Sua simulacao chegou! - imoGo",
		recipients=[data.email],
		body=html,
		subtype=MessageType.html,
		reply_to=["suporte@imogo.com.br"],
	)

	fm = FastMail(conf)
	await fm.send_message(message)
