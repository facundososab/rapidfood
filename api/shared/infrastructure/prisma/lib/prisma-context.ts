import { AsyncLocalStorage } from 'node:async_hooks';
import type { Prisma, PrismaClient } from '../generated/client';
import { prisma } from './prisma';

type PrismaTransactionClient = Prisma.TransactionClient;
type PrismaClientLike = PrismaClient | PrismaTransactionClient;

const prismaTransactionStorage = new AsyncLocalStorage<PrismaTransactionClient>();

export function getPrismaClient(): PrismaClientLike {
  return prismaTransactionStorage.getStore() ?? prisma;
}

export async function runInPrismaTransaction<T>(
  callback: (client: PrismaTransactionClient) => Promise<T>,
): Promise<T> {
  const currentTransaction = prismaTransactionStorage.getStore();

  if (currentTransaction) {
    return callback(currentTransaction);
  }

  return prisma.$transaction((transactionClient) =>
    prismaTransactionStorage.run(transactionClient, () =>
      callback(transactionClient),
    ),
  );
}
