import { Injectable, signal } from '@angular/core';

import { Pieza } from '../shared/models/ordenes.models';

export interface OrdenParaImprimir {
  id: number;
  codigo_nest: string;
  material: string;
  espesor_mm: number;
  largo_mm: number;
  ancho_mm: number;
  piezas: Pieza[];
}

@Injectable({ providedIn: 'root' })
export class OrdenConfirmadaService {
  private readonly orden = signal<OrdenParaImprimir | null>(null);

  set(orden: OrdenParaImprimir): void {
    this.orden.set(orden);
  }

  get(): OrdenParaImprimir | null {
    return this.orden();
  }

  clear(): void {
    this.orden.set(null);
  }
}
