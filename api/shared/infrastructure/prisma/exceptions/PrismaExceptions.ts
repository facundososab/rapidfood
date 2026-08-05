import { DomainException } from "../../../domain/exceptions/DomainException";

export class EntidadDuplicadaException extends DomainException {
    constructor(mensaje: string) {
        super(`Entidad duplicada: ${mensaje}`);
        this.name = 'EntidadDuplicadaException';
    }
}


export class ErrorDePersistenciaException extends DomainException {
    constructor(mensaje: string) {
        super(`Error de persistencia, ${mensaje}`);
        this.name = 'ErrorDePersistenciaException';
    }
}

export class ErrorDeConexionException extends DomainException {
    constructor(mensaje: string) {
        super(`Error de conexión a la base de datos: ${mensaje}`);
        this.name = 'ErrorDeConexionException';
    }
}
