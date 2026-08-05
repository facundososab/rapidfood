import { config } from "dotenv";
import { resolve } from "path";

// Load .env from backend root (4 levels up from this file)
config({ path: resolve(__dirname, "../../../../.env") });
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../generated/client";

const connectionString = process.env.PRISMA_LOCAL_DATABASE_URL!;
console.log(`[Prisma] Connecting to DB: ${connectionString?.split('@')[1]}`); // Log DB host/name only for security
const adapter = new PrismaPg({ connectionString });

//Patron singleton
const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

export const prisma =
  globalForPrisma.prisma || new PrismaClient({adapter})

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma