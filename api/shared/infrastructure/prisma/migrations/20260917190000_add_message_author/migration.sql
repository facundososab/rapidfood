-- Distinguish who actually wrote a message: the customer, the automated agent
-- or a human operator speaking on the business side. `role` keeps its
-- LLM-facing meaning (operator messages share the AGENT role).
ALTER TABLE "message" ADD COLUMN "author" TEXT NOT NULL DEFAULT 'AGENT';

-- Existing rows: the customer wrote every USER message, the agent the rest.
UPDATE "message" SET "author" = 'CLIENT' WHERE "role" = 'USER';
