-- A human can take over a conversation; while paused the agent does not reply.
ALTER TABLE "conversation" ADD COLUMN "agent_paused" BOOLEAN NOT NULL DEFAULT false;
