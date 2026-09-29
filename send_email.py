#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESUMO = DATA / "resumo_execucao.json"


def must_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"[ERRO] Variável de ambiente ausente: {name}")
    return v


def fmt_bolinha(cor: str) -> str:
    cor = (cor or "").lower()
    if cor == "verde":
        return "🟢"
    if cor == "amarelo":
        return "🟡"
    if cor == "vermelho":
        return "🔴"
    if cor == "cinza":
        return "⚪"
    return "⚪"


def parse_int(d: dict, key: str, default: int = 0) -> int:
    try:
        return int((d or {}).get(key, default) or default)
    except Exception:
        return default


def main() -> None:
    # SMTP (GitHub Actions)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
    site_url  = os.getenv("SITE_URL", "").strip()

    smtp_user = must_env("SMTP_USER")
    smtp_pass = must_env("SMTP_PASS")
    to_list = must_env("SMTP_TO")
    from_name = os.getenv("SMTP_FROM_NAME", "FVS-RCP • DEPI").strip()

    tos = [x.strip() for x in to_list.split(",") if x.strip()]
    if not tos:
        raise SystemExit("[ERRO] SMTP_TO vazio após parsing.")

    if not RESUMO.exists():
        raise SystemExit(f"[ERRO] Não encontrei {RESUMO}. Rode monitor_act.py antes.")

    resumo = json.loads(RESUMO.read_text(encoding="utf-8"))

    data_exec_raw = (resumo.get("data_execucao", "") or "").strip()
    # Exibe a data no padrão brasileiro (DD/MM/AAAA); mantém o valor original se não for ISO
    try:
        data_exec = datetime.fromisoformat(data_exec_raw[:10]).strftime("%d/%m/%Y")
    except Exception:
        data_exec = data_exec_raw or "N/D"

    # ✅ Compatível com o monitor_act.py (novo formato)
    faixas = (resumo.get("faixas") or {})

    # LÓGICA (60/180):
    # - confortável: >180d
    # - alerta: 61–180d
    # - crítico: ≤60d
    confort = parse_int(faixas, "confortavel_acima_180", 0)
    alerta180 = parse_int(faixas, "atencao_61_180", 0)
    crit60 = parse_int(faixas, "critica_ate_60", 0)

    sem_data = parse_int(faixas, "sem_data", 0)
    vencido = parse_int(faixas, "vencido", 0)

    total_base = int(resumo.get("total_base_painel", 0) or 0)
    ignorados = int(resumo.get("ignorados_arquivados", 0) or 0)
    concluidos = int(resumo.get("concluidos", 0) or 0)

    # Assunto executivo (só 180/60)
    subject = (
        "Monitoramento Mensal de Acordos de Cooperação Técnica (ACT’s) / Convênios / Termos de Cooperação (TC) — "
        f"{data_exec} | 180d:{alerta180} • 60d:{crit60}"
    )

    linhas = []
    linhas.append(f"Data de referência: {data_exec}")
    linhas.append("")
    linhas.append("Panorama mensal da vigência dos instrumentos:")
    linhas.append("")
    linhas.append(
        f"BASE (sem arquivados): {total_base} instrumentos | "
        f"Concluídos: {concluidos} | Arquivados ignorados: {ignorados}"
    )
    linhas.append("")
    linhas.append("PRAZOS DE VIGÊNCIA (janelas de 60 e 180 dias):")
    linhas.append(f"{fmt_bolinha('verde')} Confortável (acima de 180 dias): {confort}")
    linhas.append(f"{fmt_bolinha('amarelo')} Atenção (61 a 180 dias): {alerta180}")
    linhas.append(f"{fmt_bolinha('vermelho')} Crítico (até 60 dias): {crit60}")

    if vencido:
        linhas.append(f"Vigência expirada: {vencido}")
    if sem_data:
        linhas.append(f"{fmt_bolinha('cinza')} Sem registro válido de vigência: {sem_data}")

    linhas.append("")
    linhas.append(
        "Recomenda-se avaliar os instrumentos em alerta quanto à prorrogação, renovação ou "
        "providências cabíveis. Prazos recalculados automaticamente a cada execução."
    )
    linhas.append("")
    linhas.append("Painel Eletrônico (fonte atualizada de vigência):")
    if site_url:
        linhas.append(site_url)
    else:
        linhas.append("(URL do painel não configurada — defina o secret SITE_URL no repositório GitHub)")
    linhas.append("Senha de acesso ao painel: depi2026")
    linhas.append("")
    linhas.append("Relatório gerado automaticamente pelo sistema de monitoramento.")

    body = "\n".join(linhas)

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = ", ".join(tos)
    msg["Subject"] = subject
    msg.set_content(body)

    # Envio SMTP (Gmail)
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)

    print("[OK] Email enviado (sem anexos) para:", tos)


if __name__ == "__main__":
    main()
