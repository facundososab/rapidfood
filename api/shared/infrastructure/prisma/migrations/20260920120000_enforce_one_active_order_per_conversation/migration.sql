-- Enforce at most ONE active order (DRAFT or PENDING) per conversation.
--
-- Root cause this fixes: `get_or_create_current_draft` is a read-then-create
-- that is not atomic, so two tool calls emitted in PARALLEL within one agent
-- turn could each create a DRAFT. The leftover DRAFT then shadowed the
-- confirmed PENDING order (`get_current_order` prefers DRAFT), so
-- `create_payment_checkout` failed with ORDER_NOT_CONFIRMED.
--
-- Step 1: reconcile existing duplicates — keep the most advanced active order
-- per conversation (PENDING over DRAFT, more lines first, newest first) and
-- cancel the rest. Step 2: add a partial unique index as the hard guarantee
-- (Prisma cannot model partial indexes, so this lives as raw SQL).

WITH ranked AS (
    SELECT
        o.order_id,
        ROW_NUMBER() OVER (
            PARTITION BY o.conversation_id
            ORDER BY
                CASE o.status WHEN 'PENDING' THEN 0 ELSE 1 END,
                (SELECT COUNT(*) FROM "order_line" l WHERE l.order_id = o.order_id) DESC,
                o.created_at DESC,
                o.order_id
        ) AS rn
    FROM "order" o
    WHERE o.status IN ('DRAFT', 'PENDING')
      AND o.conversation_id IS NOT NULL
)
UPDATE "order"
SET status = 'CANCELLED'
WHERE order_id IN (SELECT order_id FROM ranked WHERE rn > 1);

CREATE UNIQUE INDEX "order_one_active_per_conversation"
    ON "order" (conversation_id)
    WHERE status IN ('DRAFT', 'PENDING') AND conversation_id IS NOT NULL;
