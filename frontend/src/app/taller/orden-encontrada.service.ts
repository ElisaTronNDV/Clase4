import { Injectable, signal } from '@angular/core';

import { OrdenDetalle } from '../shared/models/ordenes.models';

@Injectable({ providedIn: 'root' })
export class OrdenEncontradaService {
  private readonly orden = signal<OrdenDetalle | null>(null);

  set(orden: OrdenDetalle): void {
    this.orden.set(orden);
  }

  get(): OrdenDetalle | null {
    return this.orden();
  }

  clear(): void {
    this.orden.set(null);
  }
}
