/**
 * Non-singleton Prisma client for test infrastructure only.
 * Use ONLY in test helpers (cleanup, global-setup). Never import in production code.
 * Connects to PRISMA_TEST_DATABASE_URL or falls back to PRISMA_LOCAL_DATABASE_URL.
 */
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '../generated/client';

const connectionString =
  process.env.PRISMA_TEST_DATABASE_URL ?? process.env.PRISMA_LOCAL_DATABASE_URL!;

const adapter = new PrismaPg({ connectionString });

export const prismaTest = new PrismaClient({ adapter });
