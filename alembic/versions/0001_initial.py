"""initial booking schema

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "searches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("origin_query", sa.String(160), nullable=False),
        sa.Column("destination_query", sa.String(160), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("adults", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "journey_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("search_id", sa.String(36), sa.ForeignKey("searches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_journey_id", sa.String(160), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_journey_cache_search_id", "journey_cache", ["search_id"])
    op.create_index("ix_journey_cache_provider_journey", "journey_cache", ["provider", "provider_journey_id"])
    op.create_table(
        "booking_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("journey_cache_id", sa.String(36), sa.ForeignKey("journey_cache.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("quoted_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("quoted_currency", sa.String(3), nullable=False),
        sa.Column("provider_quote_payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reference", sa.String(20), nullable=False, unique=True),
        sa.Column("booking_session_id", sa.String(36), sa.ForeignKey("booking_sessions.id"), nullable=False, unique=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_booking_id", sa.String(160), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("contact_email", sa.String(320), nullable=False),
        sa.Column("contact_phone", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bookings_contact_email", "bookings", ["contact_email"])
    op.create_table(
        "passengers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("booking_id", sa.String(36), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(120), nullable=False),
        sa.Column("last_name", sa.String(120), nullable=False),
        sa.Column("passenger_type", sa.String(30), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("nationality", sa.String(3), nullable=True),
        sa.Column("document_type", sa.String(30), nullable=True),
        sa.Column("document_number", sa.String(80), nullable=True),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("booking_id", sa.String(36), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("gateway", sa.String(40), nullable=False),
        sa.Column("gateway_payment_id", sa.String(160), nullable=True),
        sa.Column("idempotency_key", sa.String(120), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("gateway_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("booking_id", sa.String(36), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_ticket_id", sa.String(160), nullable=True),
        sa.Column("ticket_number", sa.String(120), nullable=True),
        sa.Column("qr_text", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "refunds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("booking_id", sa.String(36), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", sa.String(36), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("gateway_refund_id", sa.String(160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_promo_codes_code", "promo_codes", ["code"], unique=True)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("promo_codes")
    op.drop_table("refunds")
    op.drop_table("tickets")
    op.drop_table("payments")
    op.drop_table("passengers")
    op.drop_table("bookings")
    op.drop_table("booking_sessions")
    op.drop_table("journey_cache")
    op.drop_table("searches")
