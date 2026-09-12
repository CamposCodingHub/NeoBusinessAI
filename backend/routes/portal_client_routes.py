"""
Portal do Cliente - API Routes
Acesso read-only para clientes do escritório visualizarem docs, faturas e timeline.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Client, Deadline, Document, Invoice, Matter, get_db
from models.portal_client import PortalActivity, PortalClient
from security import create_access_token, verify_password, verify_token
from security.auth import Role
from security.xss_protection import sanitize_plain_text

router = APIRouter(prefix="/portal", tags=["Portal do Cliente"])

PORTAL_PERMISSION = "portal"
PORTAL_TOKEN_HOURS = 8


class PortalLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


def _require_portal_claim(payload: Dict[str, Any]) -> None:
    perms = payload.get("permissions") or []
    if PORTAL_PERMISSION not in perms:
        raise HTTPException(status_code=401, detail="Token sem escopo de portal")


async def get_current_portal_client(
    request: Request,
    db: Session = Depends(get_db),
) -> PortalClient:
    """Autentica cliente do portal via JWT com claim portal."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = auth_header[7:]
    try:
        payload = verify_token(token, token_type="access")
        _require_portal_claim(payload)
        portal_client_id = int(payload["sub"])

        portal_client = (
            db.query(PortalClient)
            .filter(PortalClient.id == portal_client_id, PortalClient.is_active == True)
            .first()
        )
        if not portal_client:
            raise HTTPException(status_code=401, detail="Acesso inválido")
        return portal_client
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


def log_portal_activity(
    db: Session,
    portal_client_id: int,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
) -> None:
    """Registra atividade no portal."""
    activity = PortalActivity(
        portal_client_id=portal_client_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(activity)
    db.commit()


def _get_owned_client(db: Session, portal: PortalClient) -> Client:
    client = db.query(Client).filter(Client.id == portal.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


def _custom_data_client_id(doc: Document) -> Optional[int]:
    cd = doc.custom_data or {}
    if not isinstance(cd, dict):
        return None
    raw = cd.get("client_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _documents_for_client(db: Session, client: Client) -> List[Document]:
    """
    Documentos visíveis ao portal: vinculados a Matter do cliente
    ou marcados com custom_data.client_id. Portável (SQLite/Postgres).
    """
    matter_ids = [
        mid
        for (mid,) in db.query(Matter.id).filter(Matter.client_id == client.id).all()
    ]

    by_id: Dict[int, Document] = {}

    if matter_ids:
        for doc in (
            db.query(Document)
            .filter(
                Document.user_id == client.user_id,
                Document.matter_id.in_(matter_ids),
                Document.status != "error",
            )
            .all()
        ):
            by_id[doc.id] = doc

    # Tag via custom_data (filtro em memória — evita JSON path DB-específico)
    for doc in (
        db.query(Document)
        .filter(Document.user_id == client.user_id, Document.status != "error")
        .all()
    ):
        if _custom_data_client_id(doc) == client.id:
            by_id[doc.id] = doc

    docs = list(by_id.values())
    docs.sort(
        key=lambda d: d.created_at or datetime.min,
        reverse=True,
    )
    return docs


def _serialize_invoice(inv: Invoice) -> Dict[str, Any]:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "description": inv.description,
        "total_amount": (inv.total_cents or 0) / 100,
        "status": inv.status,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "payment_url": getattr(inv, "payment_url", None),
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def _serialize_document(doc: Document) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "file_type": doc.file_type,
        "status": doc.status,
        "matter_id": doc.matter_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.post("/login")
async def portal_login(
    body: PortalLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Login do cliente no portal (JSON). Token com escopo `portal`."""
    email = sanitize_plain_text(body.email.strip().lower())
    portal_client = (
        db.query(PortalClient)
        .filter(PortalClient.email == email, PortalClient.is_active == True)
        .first()
    )

    if not portal_client or not verify_password(body.password, portal_client.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    portal_client.last_login = datetime.utcnow()
    portal_client.login_attempts = 0
    db.commit()

    log_portal_activity(
        db,
        portal_client.id,
        "login",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    access_token = create_access_token(
        user_id=str(portal_client.id),
        role=Role.USER,
        permissions=[PORTAL_PERMISSION],
        expires_delta=timedelta(hours=PORTAL_TOKEN_HOURS),
    )

    client_name = portal_client.client.name if portal_client.client else None
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_hours": PORTAL_TOKEN_HOURS,
        "client_name": client_name,
        "client_id": portal_client.client_id,
    }


@router.get("/me")
async def portal_me(
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Perfil mínimo do cliente autenticado no portal."""
    client = _get_owned_client(db, current_portal)
    return {
        "portal_id": current_portal.id,
        "client_id": client.id,
        "client_name": client.name,
        "email": current_portal.email,
        "last_login": current_portal.last_login.isoformat()
        if current_portal.last_login
        else None,
    }


@router.get("/dashboard")
async def portal_dashboard(
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Dashboard do cliente — visão geral read-only."""
    client = _get_owned_client(db, current_portal)
    client_id = client.id

    invoices = (
        db.query(Invoice)
        .filter(Invoice.client_id == client_id)
        .order_by(Invoice.created_at.desc())
        .limit(5)
        .all()
    )

    documents = _documents_for_client(db, client)[:5]

    matter_ids = [
        mid
        for (mid,) in db.query(Matter.id).filter(Matter.client_id == client_id).all()
    ]
    deadlines_q = db.query(Deadline).filter(
        Deadline.user_id == client.user_id,
        Deadline.is_completed == False,
    )
    if matter_ids:
        deadlines_q = deadlines_q.filter(
            (Deadline.matter_id.in_(matter_ids)) | (Deadline.matter_id.is_(None))
        )
    deadlines = deadlines_q.order_by(Deadline.due_date.asc()).limit(5).all()

    total_invoices = db.query(Invoice).filter(Invoice.client_id == client_id).count()
    pending_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.client_id == client_id,
            Invoice.status.in_(["pending", "overdue"]),
        )
        .count()
    )
    all_docs = _documents_for_client(db, client)

    return {
        "client": {
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "status": client.status,
        },
        "summary": {
            "total_invoices": total_invoices,
            "pending_invoices": pending_invoices,
            "total_documents": len(all_docs),
            "upcoming_deadlines": len(deadlines),
        },
        "recent_invoices": [_serialize_invoice(inv) for inv in invoices],
        "shared_documents": [_serialize_document(doc) for doc in documents],
        "upcoming_deadlines": [
            {
                "id": dl.id,
                "description": dl.description,
                "due_date": dl.due_date.isoformat() if dl.due_date else None,
                "urgency": dl.urgency,
            }
            for dl in deadlines
        ],
    }


@router.get("/invoices")
async def portal_list_invoices(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Lista faturas do cliente autenticado (somente as dele)."""
    client_id = current_portal.client_id
    page = max(1, page)
    limit = min(max(1, limit), 100)

    query = db.query(Invoice).filter(Invoice.client_id == client_id)
    if status:
        query = query.filter(Invoice.status == status)

    total = query.count()
    invoices = (
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "invoices": [_serialize_invoice(inv) for inv in invoices],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.get("/invoices/{invoice_id}")
async def portal_get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Detalhe read-only de fatura — IDOR bloqueado por client_id."""
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.client_id == current_portal.client_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    return {"invoice": _serialize_invoice(invoice)}


@router.get("/invoices/{invoice_id}/download")
async def portal_download_invoice(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Stub de download de fatura (PDF) — ownership enforced."""
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.client_id == current_portal.client_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")

    log_portal_activity(
        db,
        current_portal.id,
        "download_invoice",
        resource_type="invoice",
        resource_id=invoice_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return {
        "message": "PDF ainda não disponível — stub MVP",
        "invoice_id": invoice_id,
        "invoice": _serialize_invoice(invoice),
        "download_url": None,
    }


@router.get("/documents")
async def portal_list_documents(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Lista documentos compartilhados com o cliente (read-only)."""
    client = _get_owned_client(db, current_portal)
    page = max(1, page)
    limit = min(max(1, limit), 100)

    all_docs = _documents_for_client(db, client)
    total = len(all_docs)
    start = (page - 1) * limit
    documents = all_docs[start : start + limit]

    return {
        "documents": [_serialize_document(doc) for doc in documents],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.get("/documents/{document_id}")
async def portal_get_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Detalhe read-only de documento — só se pertencente ao cliente."""
    client = _get_owned_client(db, current_portal)
    allowed_ids = {d.id for d in _documents_for_client(db, client)}
    if document_id not in allowed_ids:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    log_portal_activity(
        db,
        current_portal.id,
        "view_document",
        resource_type="document",
        resource_id=document_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return {"document": _serialize_document(doc)}


@router.get("/timeline")
async def portal_timeline(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """
    Timeline conjunta (placeholder MVP): atividades do portal +
    eventos recentes de faturas/documentos do próprio cliente.
    """
    client = _get_owned_client(db, current_portal)
    limit = min(max(1, limit), 100)
    events: List[Dict[str, Any]] = []

    activities = (
        db.query(PortalActivity)
        .filter(PortalActivity.portal_client_id == current_portal.id)
        .order_by(PortalActivity.created_at.desc())
        .limit(limit)
        .all()
    )
    for act in activities:
        events.append(
            {
                "type": "activity",
                "action": act.action,
                "resource_type": act.resource_type,
                "resource_id": act.resource_id,
                "at": act.created_at.isoformat() if act.created_at else None,
                "label": act.action.replace("_", " ").title(),
            }
        )

    for inv in (
        db.query(Invoice)
        .filter(Invoice.client_id == client.id)
        .order_by(Invoice.created_at.desc())
        .limit(10)
        .all()
    ):
        events.append(
            {
                "type": "invoice",
                "action": "invoice_listed",
                "resource_type": "invoice",
                "resource_id": inv.id,
                "at": inv.created_at.isoformat() if inv.created_at else None,
                "label": f"Fatura {inv.invoice_number or inv.id} — {inv.status}",
            }
        )

    for doc in _documents_for_client(db, client)[:10]:
        events.append(
            {
                "type": "document",
                "action": "document_shared",
                "resource_type": "document",
                "resource_id": doc.id,
                "at": doc.created_at.isoformat() if doc.created_at else None,
                "label": f"Documento {doc.title or doc.filename}",
            }
        )

    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    return {"events": events[:limit], "has_more": len(events) > limit}


@router.get("/chat")
async def portal_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client),
):
    """Histórico de chat — stub até canal cliente-escritório."""
    _ = (limit, db, current_portal)
    return {"messages": [], "has_more": False}
