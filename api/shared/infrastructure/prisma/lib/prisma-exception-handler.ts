import { Prisma } from "../generated/client";
import { EntidadDuplicadaException, ErrorDePersistenciaException, ErrorDeConexionException } from "../exceptions/PrismaExceptions";

export function mapPrismaError(error: any): Error {
    if (error.code === 'ECONNREFUSED') {
        return new ErrorDeConexionException('No se pudo conectar a la base de datos');
    }

    if (error instanceof Prisma.PrismaClientKnownRequestError) {
        // P2002: Unique constraint failed
        if (error.code === 'P2002') {
            const targetRaw = error.meta?.target;
            let target = Array.isArray(targetRaw) 
                ? targetRaw 
                : (typeof targetRaw === 'string' ? [targetRaw] : []);

            // Fallback: Intentar extraer del mensaje o del error del driver adapter (pg)
            if (target.length === 0) {
                const meta = error.meta as any;
                const driverMessage = meta?.driverAdapterError?.cause?.originalMessage;
                const searchString = driverMessage || error.message;

                if (searchString) {
                    const match = searchString.match(/unique constraint ".*_(.*)_key"/i) || 
                                 searchString.match(/fields: \((.*)\)/i);
                    if (match && match[1]) {
                        target = [match[1]];
                    }
                }
            }
            
            const fields = target.map(f => f.trim()).join(', ');
            
            return new EntidadDuplicadaException(`Ya existe un registro con ese ${fields}`);
        }

        // Connection related errors
        const connectionCodes = ['P1001', 'P1002', 'P1003', 'P1008', 'P1017'];
        if (connectionCodes.includes(error.code)) {
             return new ErrorDeConexionException(`Código: ${error.code}`);
        }
    }
    
    if (error instanceof Error) {
        return new ErrorDePersistenciaException(error.message);
    }
    
    return new ErrorDePersistenciaException('Error desconocido en la base de datos');
}



